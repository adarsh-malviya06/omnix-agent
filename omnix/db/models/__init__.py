"""
Omnix database models package initialization and consolidated export.
"""

from omnix.db.base import (
    ApprovalAction,
    AuditEventType,
    Base,
    BusinessType,
    LocationType,
    MovementType,
    PurchaseOrderStatus,
    RecommendationStatus,
    TimestampMixin,
    UserRole,
)
from omnix.db.models.alert import InventoryAlert
from omnix.db.models.approval import Approval, AuditLog
from omnix.db.models.demand_history import DemandHistory
from omnix.db.models.inventory import Inventory
from omnix.db.models.inventory_movement import InventoryMovement
from omnix.db.models.location import Location
from omnix.db.models.organization import Organization
from omnix.db.models.product import Product
from omnix.db.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from omnix.db.models.recommendation import Recommendation
from omnix.db.models.setting import SystemSetting
from omnix.db.models.supplier import Supplier
from omnix.db.models.supplier_product import SupplierProduct
from omnix.db.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "BusinessType",
    "LocationType",
    "UserRole",
    "MovementType",
    "PurchaseOrderStatus",
    "RecommendationStatus",
    "ApprovalAction",
    "AuditEventType",
    "Organization",
    "User",
    "Location",
    "Product",
    "Inventory",
    "InventoryMovement",
    "Supplier",
    "SupplierProduct",
    "DemandHistory",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "Recommendation",
    "Approval",
    "AuditLog",
    "SystemSetting",
    "InventoryAlert",
]
