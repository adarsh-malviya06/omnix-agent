"""
Approval and AuditLog models.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import ApprovalAction, AuditEventType, Base, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.user import User
    from omnix.db.models.purchase_order import PurchaseOrder


class Approval(TimestampMixin, Base):
    """
    Human approval / rejection audit record for Purchase Orders.
    """

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction), nullable=False, index=True
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="approvals")
    approved_by_user: Mapped["User"] = relationship("User", back_populates="approvals")

    def __repr__(self) -> str:
        return f"<Approval id={self.id} po_id={self.purchase_order_id} action={self.action}>"


class AuditLog(TimestampMixin, Base):
    """
    Centralized governance and compliance audit log.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType), nullable=False, index=True
    )
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="System")
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_logs")
    user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} event={self.event_type} action='{self.action}'>"
