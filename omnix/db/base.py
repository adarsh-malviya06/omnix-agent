"""
Shared SQLAlchemy base configuration, mixins and enumerations for OMNIX models.
"""

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared declarative base for all OMNIX ORM models."""
    pass


# ---------------------------------------------------------------------------
# Timestamp Mixin — applied to every table that tracks creation/update time
# ---------------------------------------------------------------------------

class TimestampMixin:
    """Adds created_at and updated_at columns to any inheriting model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class BusinessType(str, enum.Enum):
    """Classification of OMNIX client organisations."""
    WHOLESALE = "wholesale"
    DISTRIBUTION = "distribution"
    RETAIL = "retail"
    SUPERMARKET = "supermarket"


class LocationType(str, enum.Enum):
    """Physical storage facility type."""
    WAREHOUSE = "warehouse"
    STORE = "store"
    DISTRIBUTION_CENTER = "distribution_center"


class UserRole(str, enum.Enum):
    """Permission level for OMNIX platform users."""
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


class MovementType(str, enum.Enum):
    """Classification of a stock movement transaction."""
    PURCHASE_RECEIPT = "purchase_receipt"   # Stock in from a purchase order
    SALE = "sale"                           # Stock out for customer sale
    TRANSFER_IN = "transfer_in"            # Transferred from another location
    TRANSFER_OUT = "transfer_out"          # Transferred to another location
    ADJUSTMENT_POSITIVE = "adjustment_positive"  # Manual positive correction
    ADJUSTMENT_NEGATIVE = "adjustment_negative"  # Manual negative correction
    RETURN = "return"                       # Customer return back to stock
    DAMAGE = "damage"                       # Damaged / written off


class PurchaseOrderStatus(str, enum.Enum):
    """Lifecycle state of a purchase order."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class RecommendationStatus(str, enum.Enum):
    """State of an AI-generated procurement recommendation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalAction(str, enum.Enum):
    """Human decision recorded in the approval audit table."""
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class AuditEventType(str, enum.Enum):
    """High-level category for audit log entries."""
    INVENTORY_SCAN = "inventory_scan"
    STOCK_MOVEMENT = "stock_movement"
    PO_CREATED = "po_created"
    PO_APPROVED = "po_approved"
    PO_REJECTED = "po_rejected"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    USER_LOGIN = "user_login"
    SETTINGS_CHANGED = "settings_changed"
    AGENT_ACTION = "agent_action"
    SYSTEM_EVENT = "system_event"
