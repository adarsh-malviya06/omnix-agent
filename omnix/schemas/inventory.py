"""
Pydantic schemas for Inventory domain.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    uom: str
    pack_size: Optional[Decimal] = None
    standard_cost: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    reorder_point: int = 0
    reorder_quantity: int = 0
    safety_stock: int = 0
    is_active: bool = True


class ProductCreate(ProductBase):
    organization_id: int


class ProductResponse(ProductBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryBase(BaseModel):
    product_id: int
    location_id: int
    quantity_on_hand: int
    quantity_reserved: int = 0
    last_purchase_cost: Decimal = Decimal("0.00")


class InventoryResponse(InventoryBase):
    id: int
    quantity_available: int
    is_low_stock: bool
    is_out_of_stock: bool
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    location_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InventoryMovementCreate(BaseModel):
    product_id: int
    location_id: int
    movement_type: str
    quantity_delta: int
    unit_cost: Optional[Decimal] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    location_id: int
    movement_type: str
    quantity_delta: int
    quantity_after: int
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    performed_at: datetime

    model_config = ConfigDict(from_attributes=True)
