"""
Pydantic schemas for Supplier domain.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SupplierBase(BaseModel):
    code: str
    name: str
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    reliability_score: Decimal = Decimal("100.00")
    avg_lead_days: Decimal = Decimal("7.0")
    payment_terms: Optional[str] = None
    is_active: bool = True
    is_preferred: bool = False


class SupplierCreate(SupplierBase):
    organization_id: int


class SupplierResponse(SupplierBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierProductResponse(BaseModel):
    id: int
    supplier_id: int
    product_id: int
    supplier_sku: Optional[str] = None
    unit_price: Decimal
    moq: int
    lead_days: int
    is_available: bool
    is_preferred_supplier: bool
    supplier_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SupplierComparisonItem(BaseModel):
    supplier_id: int
    supplier_name: str
    supplier_code: str
    unit_price: Decimal
    lead_days: int
    moq: int
    reliability_score: Decimal
    composite_score: float = Field(
        description="Weighted score (0-100) based on price, delivery speed, and reliability"
    )
    is_recommended: bool = False


class SupplierComparisonResponse(BaseModel):
    product_id: int
    product_name: str
    product_sku: str
    quotes: List[SupplierComparisonItem]
