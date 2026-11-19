"""
Pydantic schemas for Procurement, Recommendations, and Purchase Orders.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReorderCalculationRequest(BaseModel):
    product_id: int
    location_id: int
    daily_demand_override: Optional[float] = None
    lead_time_override: Optional[int] = None


class ReorderCalculationResult(BaseModel):
    product_id: int
    location_id: int
    current_stock: int
    reserved_stock: int
    available_stock: int
    safety_stock: int
    avg_daily_demand: float
    effective_lead_days: int
    calculated_reorder_point: int
    is_reorder_needed: bool
    suggested_order_quantity: int
    best_supplier_id: Optional[int] = None
    best_supplier_name: Optional[str] = None
    estimated_unit_cost: Decimal
    estimated_total_cost: Decimal
    data_source: str = Field(description="Historical average vs manual override vs default")


class RecommendationResponse(BaseModel):
    id: int
    organization_id: int
    product_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    location_id: int
    suggested_supplier_id: Optional[int] = None
    suggested_supplier_name: Optional[str] = None
    suggested_quantity: int
    current_stock: int
    reorder_point: int
    estimated_cost: Decimal
    status: str
    reasoning: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal


class PurchaseOrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderCreate(BaseModel):
    organization_id: int
    supplier_id: int
    destination_location_id: int
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderResponse(BaseModel):
    id: int
    organization_id: int
    po_number: str
    supplier_id: int
    supplier_name: Optional[str] = None
    destination_location_id: int
    status: str
    currency: str
    total_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    items: List[PurchaseOrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequest(BaseModel):
    action: str = Field(description="'approved', 'rejected', or 'escalated'")
    user_id: int
    comments: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    purchase_order_id: int
    user_id: int
    action: str
    comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardStatsResponse(BaseModel):
    total_products: int
    total_inventory_value: Decimal
    low_stock_count: int
    out_of_stock_count: int
    pending_approvals_count: int
    total_suppliers: int
    currency: str = "INR"
