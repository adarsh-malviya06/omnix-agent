"""
Inventory API endpoints for products, stock positions, and movements.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from omnix.db.base import MovementType
from omnix.db.session import get_db
from omnix.schemas.inventory import (
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryResponse,
    ProductResponse,
)
from omnix.services.inventory_service import (
    get_all_products,
    get_inventory_positions,
    get_low_stock_items,
    get_movement_history,
    get_out_of_stock_items,
    get_product_by_id,
    record_inventory_movement,
)

router = APIRouter(prefix="/inventory", tags=["Inventory & Products"])


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """Retrieve all active catalog products."""
    return get_all_products(db, organization_id=organization_id)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get single product details by ID."""
    return get_product_by_id(db, product_id=product_id)


@router.get("/stock", response_model=List[InventoryResponse])
def list_inventory(
    organization_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Query current inventory levels with health indicators."""
    items = get_inventory_positions(
        db, organization_id=organization_id, location_id=location_id, product_id=product_id
    )
    result = []
    for itm in items:
        res = InventoryResponse(
            id=itm.id,
            product_id=itm.product_id,
            location_id=itm.location_id,
            quantity_on_hand=itm.quantity_on_hand,
            quantity_reserved=itm.quantity_reserved,
            quantity_available=itm.quantity_available,
            last_purchase_cost=itm.last_purchase_cost,
            is_low_stock=itm.is_low_stock,
            is_out_of_stock=itm.is_out_of_stock,
            product_name=itm.product.name,
            product_sku=itm.product.sku,
            location_name=itm.location.name,
        )
        result.append(res)
    return result


@router.get("/stock/low", response_model=List[InventoryResponse])
def list_low_stock(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """Filter inventory items currently at or below safety reorder threshold."""
    items = get_low_stock_items(db, organization_id=organization_id)
    return [
        InventoryResponse(
            id=itm.id,
            product_id=itm.product_id,
            location_id=itm.location_id,
            quantity_on_hand=itm.quantity_on_hand,
            quantity_reserved=itm.quantity_reserved,
            quantity_available=itm.quantity_available,
            last_purchase_cost=itm.last_purchase_cost,
            is_low_stock=itm.is_low_stock,
            is_out_of_stock=itm.is_out_of_stock,
            product_name=itm.product.name,
            product_sku=itm.product.sku,
            location_name=itm.location.name,
        )
        for itm in items
    ]


@router.get("/stock/out-of-stock", response_model=List[InventoryResponse])
def list_out_of_stock(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """Filter completely depleted inventory items."""
    items = get_out_of_stock_items(db, organization_id=organization_id)
    return [
        InventoryResponse(
            id=itm.id,
            product_id=itm.product_id,
            location_id=itm.location_id,
            quantity_on_hand=itm.quantity_on_hand,
            quantity_reserved=itm.quantity_reserved,
            quantity_available=itm.quantity_available,
            last_purchase_cost=itm.last_purchase_cost,
            is_low_stock=itm.is_low_stock,
            is_out_of_stock=itm.is_out_of_stock,
            product_name=itm.product.name,
            product_sku=itm.product.sku,
            location_name=itm.location.name,
        )
        for itm in items
    ]


@router.post("/movements", response_model=InventoryMovementResponse, status_code=201)
def record_movement(
    movement_in: InventoryMovementCreate, db: Session = Depends(get_db)
):
    """Atomically record a stock transaction and adjust inventory balance."""
    m_type = MovementType(movement_in.movement_type)
    return record_inventory_movement(
        db=db,
        product_id=movement_in.product_id,
        location_id=movement_in.location_id,
        movement_type=m_type,
        quantity_delta=movement_in.quantity_delta,
        unit_cost=movement_in.unit_cost,
        reference_number=movement_in.reference_number,
        notes=movement_in.notes,
    )


@router.get("/movements", response_model=List[InventoryMovementResponse])
def list_movements(
    product_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve historical inventory movements audit trail."""
    return get_movement_history(
        db, product_id=product_id, location_id=location_id, limit=limit
    )
