"""
Inventory business service.
Pure deterministic logic for stock queries, threshold auditing, and inventory movements.
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from omnix.core.exceptions import BusinessRuleViolationException, NotFoundException
from omnix.db.base import MovementType
from omnix.db.models import Inventory, InventoryMovement, Location, Product


def get_all_products(db: Session, organization_id: Optional[int] = None) -> List[Product]:
    """Retrieve products, optionally filtered by organization."""
    query = db.query(Product).filter(Product.is_active == True)
    if organization_id:
        query = query.filter(Product.organization_id == organization_id)
    return query.all()


def get_product_by_id(db: Session, product_id: int) -> Product:
    """Fetch product by ID or raise NotFoundException."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found.")
    return product


def get_product_by_sku(db: Session, sku: str) -> Product:
    """Fetch product by SKU or raise NotFoundException."""
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        raise NotFoundException(f"Product with SKU '{sku}' not found.")
    return product


def get_inventory_positions(
    db: Session,
    organization_id: Optional[int] = None,
    location_id: Optional[int] = None,
    product_id: Optional[int] = None,
) -> List[Inventory]:
    """Query current inventory levels across locations."""
    query = db.query(Inventory).join(Product)
    if organization_id:
        query = query.filter(Product.organization_id == organization_id)
    if location_id:
        query = query.filter(Inventory.location_id == location_id)
    if product_id:
        query = query.filter(Inventory.product_id == product_id)
    return query.all()


def get_low_stock_items(db: Session, organization_id: Optional[int] = None) -> List[Inventory]:
    """Identify inventory positions where on-hand quantity <= reorder_point."""
    items = get_inventory_positions(db, organization_id=organization_id)
    return [item for item in items if item.is_low_stock and not item.is_out_of_stock]


def get_out_of_stock_items(db: Session, organization_id: Optional[int] = None) -> List[Inventory]:
    """Identify inventory positions where quantity_on_hand == 0."""
    items = get_inventory_positions(db, organization_id=organization_id)
    return [item for item in items if item.is_out_of_stock]


def record_inventory_movement(
    db: Session,
    product_id: int,
    location_id: int,
    movement_type: MovementType,
    quantity_delta: int,
    unit_cost: Optional[Decimal] = None,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None,
    purchase_order_id: Optional[int] = None,
) -> InventoryMovement:
    """
    Atomically adjust inventory and record an audit ledger entry.
    Enforces non-negative stock constraint deterministically.
    """
    if quantity_delta == 0:
        raise BusinessRuleViolationException("Movement quantity delta cannot be zero.")

    # Find or initialize inventory record
    inv = (
        db.query(Inventory)
        .filter_by(product_id=product_id, location_id=location_id)
        .with_for_update()
        .first()
    )

    if not inv:
        if quantity_delta < 0:
            raise BusinessRuleViolationException(
                f"Cannot decrement stock. No inventory record exists for product {product_id} at location {location_id}."
            )
        inv = Inventory(
            product_id=product_id,
            location_id=location_id,
            quantity_on_hand=0,
            quantity_reserved=0,
            last_purchase_cost=unit_cost or Decimal("0.00"),
        )
        db.add(inv)
        db.flush()

    new_qty = inv.quantity_on_hand + quantity_delta
    if new_qty < 0:
        raise BusinessRuleViolationException(
            f"Insufficient stock for product {product_id}. Available: {inv.quantity_on_hand}, Requested reduction: {abs(quantity_delta)}"
        )

    inv.quantity_on_hand = new_qty
    if unit_cost is not None and unit_cost > 0:
        inv.last_purchase_cost = unit_cost

    total_cost = None
    if unit_cost is not None:
        total_cost = abs(quantity_delta) * unit_cost

    movement = InventoryMovement(
        product_id=product_id,
        location_id=location_id,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        quantity_after=new_qty,
        unit_cost=unit_cost,
        total_cost=total_cost,
        reference_number=reference_number,
        notes=notes,
        purchase_order_id=purchase_order_id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def get_movement_history(
    db: Session,
    product_id: Optional[int] = None,
    location_id: Optional[int] = None,
    limit: int = 50,
) -> List[InventoryMovement]:
    """Retrieve historical stock transactions in reverse chronological order."""
    query = db.query(InventoryMovement).order_by(InventoryMovement.performed_at.desc())
    if product_id:
        query = query.filter(InventoryMovement.product_id == product_id)
    if location_id:
        query = query.filter(InventoryMovement.location_id == location_id)
    return query.limit(limit).all()
