"""
Procurement and Purchase Order API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from omnix.db.base import ApprovalAction
from omnix.db.models import PurchaseOrder, Recommendation
from omnix.db.session import get_db
from omnix.schemas.procurement import (
    ApprovalRequest,
    ApprovalResponse,
    DashboardStatsResponse,
    PurchaseOrderCreate,
    PurchaseOrderItemResponse,
    PurchaseOrderResponse,
    RecommendationResponse,
    ReorderCalculationRequest,
    ReorderCalculationResult,
)
from omnix.services.procurement_service import (
    calculate_reorder_recommendation,
    create_procurement_recommendation,
    create_purchase_order_draft,
    get_dashboard_statistics,
    process_purchase_order_approval,
)

router = APIRouter(prefix="/procurement", tags=["Procurement & Orders"])


@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_stats(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """Retrieve aggregate business operations and procurement statistics."""
    return get_dashboard_statistics(db, organization_id=organization_id)


@router.post("/calculate-reorder", response_model=ReorderCalculationResult)
def calculate_reorder(
    request: ReorderCalculationRequest, db: Session = Depends(get_db)
):
    """Calculate deterministic replenishment need, safety reorder point, and cost."""
    return calculate_reorder_recommendation(
        db,
        product_id=request.product_id,
        location_id=request.location_id,
        daily_demand_override=request.daily_demand_override,
        lead_time_override=request.lead_time_override,
    )


@router.post("/recommendations/generate/{product_id}/{location_id}", response_model=RecommendationResponse, status_code=201)
def generate_recommendation(
    product_id: int, location_id: int, db: Session = Depends(get_db)
):
    """Generate and persist a reorder recommendation."""
    rec = create_procurement_recommendation(db, product_id=product_id, location_id=location_id)
    return RecommendationResponse(
        id=rec.id,
        organization_id=rec.organization_id,
        product_id=rec.product_id,
        product_name=rec.product.name,
        product_sku=rec.product.sku,
        location_id=rec.location_id,
        suggested_supplier_id=rec.suggested_supplier_id,
        suggested_supplier_name=rec.suggested_supplier.name if rec.suggested_supplier else None,
        suggested_quantity=rec.suggested_quantity,
        current_stock=rec.current_stock,
        reorder_point=rec.reorder_point,
        estimated_cost=rec.estimated_cost,
        status=rec.status.value,
        reasoning=rec.reasoning,
        created_at=rec.created_at,
    )


@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """List pending and historical procurement recommendations."""
    query = db.query(Recommendation)
    if organization_id:
        query = query.filter(Recommendation.organization_id == organization_id)
    recs = query.order_by(Recommendation.created_at.desc()).all()
    return [
        RecommendationResponse(
            id=r.id,
            organization_id=r.organization_id,
            product_id=r.product_id,
            product_name=r.product.name,
            product_sku=r.product.sku,
            location_id=r.location_id,
            suggested_supplier_id=r.suggested_supplier_id,
            suggested_supplier_name=r.suggested_supplier.name if r.suggested_supplier else None,
            suggested_quantity=r.suggested_quantity,
            current_stock=r.current_stock,
            reorder_point=r.reorder_point,
            estimated_cost=r.estimated_cost,
            status=r.status.value,
            reasoning=r.reasoning,
            created_at=r.created_at,
        )
        for r in recs
    ]


@router.post("/orders", response_model=PurchaseOrderResponse, status_code=201)
def create_order(order_in: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """Create a new purchase order draft."""
    po = create_purchase_order_draft(db, order_data=order_in)
    return PurchaseOrderResponse(
        id=po.id,
        organization_id=po.organization_id,
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier.name,
        destination_location_id=po.destination_location_id,
        status=po.status.value,
        currency=po.currency,
        total_amount=po.total_amount,
        notes=po.notes,
        created_at=po.created_at,
        items=[
            PurchaseOrderItemResponse(
                id=itm.id,
                product_id=itm.product_id,
                product_name=itm.product.name,
                quantity=itm.quantity,
                unit_price=itm.unit_price,
                subtotal=itm.subtotal,
            )
            for itm in po.items
        ],
    )


@router.get("/orders", response_model=List[PurchaseOrderResponse])
def list_orders(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """List purchase orders with line items."""
    query = db.query(PurchaseOrder)
    if organization_id:
        query = query.filter(PurchaseOrder.organization_id == organization_id)
    orders = query.order_by(PurchaseOrder.created_at.desc()).all()
    return [
        PurchaseOrderResponse(
            id=po.id,
            organization_id=po.organization_id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            supplier_name=po.supplier.name,
            destination_location_id=po.destination_location_id,
            status=po.status.value,
            currency=po.currency,
            total_amount=po.total_amount,
            notes=po.notes,
            created_at=po.created_at,
            items=[
                PurchaseOrderItemResponse(
                    id=itm.id,
                    product_id=itm.product_id,
                    product_name=itm.product.name,
                    quantity=itm.quantity,
                    unit_price=itm.unit_price,
                    subtotal=itm.subtotal,
                )
                for itm in po.items
            ],
        )
        for po in orders
    ]


@router.post("/orders/{po_id}/approve", response_model=ApprovalResponse)
def approve_or_reject_order(
    po_id: int, request: ApprovalRequest, db: Session = Depends(get_db)
):
    """Human-in-the-loop decision: approve, reject, or escalate a purchase order."""
    action = ApprovalAction(request.action.lower())
    appr = process_purchase_order_approval(
        db,
        purchase_order_id=po_id,
        user_id=request.user_id,
        action=action,
        comments=request.comments,
    )
    return ApprovalResponse(
        id=appr.id,
        purchase_order_id=appr.purchase_order_id,
        user_id=appr.user_id,
        action=appr.action.value,
        comments=appr.comments,
        created_at=appr.created_at,
    )
