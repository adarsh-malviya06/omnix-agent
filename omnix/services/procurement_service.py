"""
Procurement and Purchase Order business services.
Deterministic calculations for reorder points, economic quantities, spending rules, and approval gates.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from omnix.core.config import get_settings
from omnix.core.exceptions import BusinessRuleViolationException, NotFoundException
from omnix.db.base import (
    ApprovalAction,
    AuditEventType,
    PurchaseOrderStatus,
    RecommendationStatus,
)
from omnix.db.models import (
    Approval,
    AuditLog,
    DemandHistory,
    Inventory,
    Location,
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Recommendation,
    Supplier,
    SupplierProduct,
    User,
)
from omnix.schemas.procurement import (
    DashboardStatsResponse,
    PurchaseOrderCreate,
    ReorderCalculationResult,
)
from omnix.services.inventory_service import get_all_products, get_inventory_positions
from omnix.services.settings_service import get_setting_value
from omnix.services.supplier_service import compare_suppliers_for_product


def calculate_average_daily_demand(
    db: Session, product_id: int, location_id: int, lookback_days: int = 30
) -> float:
    """
    Calculate average daily consumption from DemandHistory over lookback_days.
    Returns 0.0 if no demand records exist.
    """
    since_date = date.today() - timedelta(days=lookback_days)
    records = (
        db.query(DemandHistory)
        .filter(
            DemandHistory.product_id == product_id,
            DemandHistory.location_id == location_id,
            DemandHistory.record_date >= since_date,
        )
        .all()
    )

    if not records:
        return 0.0

    total_net = sum(r.net_demand for r in records)
    return round(total_net / len(records), 2)


def calculate_reorder_recommendation(
    db: Session,
    product_id: int,
    location_id: int,
    daily_demand_override: Optional[float] = None,
    lead_time_override: Optional[int] = None,
) -> ReorderCalculationResult:
    """
    Deterministic procurement calculation:
      Reorder Point = (Daily Demand × Lead Time) + Safety Stock
      Recommended Order = max(0, Reorder Point - Current Stock)
      Adjusted for Supplier MOQ.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found.")

    inv = (
        db.query(Inventory)
        .filter_by(product_id=product_id, location_id=location_id)
        .first()
    )
    current_stock = inv.quantity_on_hand if inv else 0
    reserved_stock = inv.quantity_reserved if inv else 0
    available_stock = max(0, current_stock - reserved_stock)

    # 1. Determine daily demand
    if daily_demand_override is not None and daily_demand_override >= 0:
        avg_demand = daily_demand_override
        source = "User Override"
    else:
        avg_demand = calculate_average_daily_demand(db, product_id, location_id)
        if avg_demand > 0:
            source = "30-Day Historical Average"
        else:
            avg_demand = 5.0  # Fallback assumption for items without history
            source = "Default Fallback (Missing History)"

    # 2. Get best supplier quote for lead time and unit price
    comparison = compare_suppliers_for_product(db, product_id)
    best_quote = comparison.quotes[0] if comparison.quotes else None

    if lead_time_override is not None and lead_time_override > 0:
        lead_days = lead_time_override
    elif best_quote:
        lead_days = best_quote.lead_days
    else:
        lead_days = 7

    # Incorporate dynamic safety stock buffer from system settings
    buffer_units = int(get_setting_value(db, "low_stock_threshold", 0))
    safety_stock = max(product.safety_stock or 0, buffer_units)

    # 3. Deterministic formula
    # Reorder Point = (Daily Demand * Lead Time) + Safety Stock
    calc_reorder_point = math.ceil((avg_demand * lead_days) + safety_stock)

    is_reorder_needed = available_stock <= calc_reorder_point

    if is_reorder_needed:
        # Deficit = Reorder Point - Available Stock
        deficit = calc_reorder_point - available_stock
        suggested_qty = max(product.reorder_quantity or deficit, deficit)
        # Enforce MOQ if supplier quote exists
        if best_quote and best_quote.moq > suggested_qty:
            suggested_qty = best_quote.moq
    else:
        suggested_qty = 0

    unit_cost = best_quote.unit_price if best_quote else (product.standard_cost or Decimal("0.00"))
    total_cost = unit_cost * Decimal(str(suggested_qty))

    return ReorderCalculationResult(
        product_id=product.id,
        location_id=location_id,
        current_stock=current_stock,
        reserved_stock=reserved_stock,
        available_stock=available_stock,
        safety_stock=safety_stock,
        avg_daily_demand=avg_demand,
        effective_lead_days=lead_days,
        calculated_reorder_point=calc_reorder_point,
        is_reorder_needed=is_reorder_needed,
        suggested_order_quantity=suggested_qty,
        best_supplier_id=best_quote.supplier_id if best_quote else None,
        best_supplier_name=best_quote.supplier_name if best_quote else None,
        estimated_unit_cost=unit_cost,
        estimated_total_cost=total_cost,
        data_source=source,
    )


def create_procurement_recommendation(
    db: Session, product_id: int, location_id: int
) -> Recommendation:
    """
    Run calculation and persist a Recommendation entity.
    """
    calc = calculate_reorder_recommendation(db, product_id, location_id)
    product = db.query(Product).filter_by(id=product_id).first()

    rec = Recommendation(
        organization_id=product.organization_id,
        product_id=product_id,
        suggested_supplier_id=calc.best_supplier_id,
        location_id=location_id,
        status=RecommendationStatus.PENDING,
        suggested_quantity=calc.suggested_order_quantity,
        current_stock=calc.current_stock,
        reorder_point=calc.calculated_reorder_point,
        estimated_cost=calc.estimated_total_cost,
        confidence_score=95.0 if "Historical" in calc.data_source else 70.0,
        reasoning=(
            f"Stock ({calc.current_stock}) at or below reorder threshold ({calc.calculated_reorder_point}). "
            f"Daily demand ~{calc.avg_daily_demand} units, supplier lead time {calc.effective_lead_days} days. "
            f"Source: {calc.data_source}."
        ),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def create_purchase_order_draft(
    db: Session, order_data: PurchaseOrderCreate
) -> PurchaseOrder:
    """
    Create a new Purchase Order in DRAFT status with validated line items.
    """
    # 1. Generate PO Number
    count = db.query(PurchaseOrder).count() + 1
    po_number = f"PO-{datetime.now().year}-{count:04d}"

    # 2. Compute total and validate lines
    total_amount = Decimal("0.00")
    items_to_add = []

    for item in order_data.items:
        product = db.query(Product).filter_by(id=item.product_id).first()
        if not product:
            raise NotFoundException(f"Product ID {item.product_id} not found.")

        subtotal = item.unit_price * Decimal(str(item.quantity))
        total_amount += subtotal
        items_to_add.append(
            PurchaseOrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=subtotal,
            )
        )

    po = PurchaseOrder(
        organization_id=order_data.organization_id,
        po_number=po_number,
        supplier_id=order_data.supplier_id,
        destination_location_id=order_data.destination_location_id,
        status=PurchaseOrderStatus.PENDING_APPROVAL,
        currency="INR",
        total_amount=total_amount,
        notes=order_data.notes,
        order_date=datetime.now(timezone.utc),
    )
    db.add(po)
    db.flush()

    for itm in items_to_add:
        itm.purchase_order_id = po.id
        db.add(itm)

    # Audit log
    audit = AuditLog(
        organization_id=order_data.organization_id,
        event_type=AuditEventType.PO_CREATED,
        actor="ProcurementService",
        action=f"Created PO {po_number}",
        details=f"Drafted PO with {len(items_to_add)} items. Total: ₹{total_amount}",
    )
    db.add(audit)

    db.commit()
    db.refresh(po)
    return po


def process_purchase_order_approval(
    db: Session,
    purchase_order_id: int,
    user_id: int,
    action: ApprovalAction,
    comments: Optional[str] = None,
) -> Approval:
    """
    Execute human-in-the-loop approval or rejection.
    Strictly enforces authorization and spending policy thresholds.
    """
    settings = get_settings()

    po = db.query(PurchaseOrder).filter_by(id=purchase_order_id).first()
    if not po:
        raise NotFoundException(f"Purchase Order ID {purchase_order_id} not found.")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise NotFoundException(f"User ID {user_id} not found.")

    if po.status not in [PurchaseOrderStatus.PENDING_APPROVAL, PurchaseOrderStatus.DRAFT]:
        raise BusinessRuleViolationException(
            f"Cannot process approval. PO {po.po_number} is currently in {po.status} status."
        )

    # Check spending thresholds
    high_value_limit = Decimal(str(get_setting_value(db, "high_value_threshold", settings.high_value_threshold)))
    if action == ApprovalAction.APPROVED:
        if po.total_amount > high_value_limit:
            if user.role not in ["admin", "manager"]:
                raise BusinessRuleViolationException(
                    f"PO total ₹{po.total_amount} exceeds high-value threshold (₹{high_value_limit}). "
                    f"Requires Admin or Manager approval."
                )
        po.status = PurchaseOrderStatus.APPROVED
    elif action == ApprovalAction.REJECTED:
        po.status = PurchaseOrderStatus.REJECTED
    elif action == ApprovalAction.ESCALATED:
        po.status = PurchaseOrderStatus.PENDING_APPROVAL

    approval = Approval(
        purchase_order_id=po.id,
        user_id=user.id,
        action=action,
        comments=comments,
    )
    db.add(approval)

    audit = AuditLog(
        organization_id=po.organization_id,
        user_id=user.id,
        event_type=(
            AuditEventType.PO_APPROVED
            if action == ApprovalAction.APPROVED
            else AuditEventType.PO_REJECTED
        ),
        actor=user.full_name,
        action=f"PO {po.po_number} {action.value.upper()}",
        details=f"Decision recorded with comments: {comments or 'None'}",
    )
    db.add(audit)

    db.commit()
    db.refresh(approval)
    return approval


def get_dashboard_statistics(db: Session, organization_id: Optional[int] = None) -> DashboardStatsResponse:
    """
    Aggregate real-time business metrics across products, inventory, and procurement.
    """
    # 1. Total active products
    prod_query = db.query(func.count(Product.id)).filter(Product.is_active == True)
    if organization_id:
        prod_query = prod_query.filter(Product.organization_id == organization_id)
    total_products = prod_query.scalar() or 0

    # 2. Total inventory value and status counts
    inv_items = get_inventory_positions(db, organization_id=organization_id)
    total_val = Decimal("0.00")
    low_stock_count = 0
    out_of_stock_count = 0

    for itm in inv_items:
        val = itm.quantity_on_hand * itm.last_purchase_cost
        total_val += val
        if itm.is_out_of_stock:
            out_of_stock_count += 1
        elif itm.is_low_stock:
            low_stock_count += 1

    # 3. Pending approvals
    po_query = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.status == PurchaseOrderStatus.PENDING_APPROVAL
    )
    if organization_id:
        po_query = po_query.filter(PurchaseOrder.organization_id == organization_id)
    pending_approvals = po_query.scalar() or 0

    # 4. Total active suppliers
    sup_query = db.query(func.count(Supplier.id)).filter(Supplier.is_active == True)
    if organization_id:
        sup_query = sup_query.filter(Supplier.organization_id == organization_id)
    total_suppliers = sup_query.scalar() or 0

    return DashboardStatsResponse(
        total_products=total_products,
        total_inventory_value=total_val,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        pending_approvals_count=pending_approvals,
        total_suppliers=total_suppliers,
        currency="INR",
    )
