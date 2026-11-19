"""
Organization model — top-level tenant boundary for the multi-business platform.
Every business data record links to an Organization via organization_id.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, BusinessType, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.user import User
    from omnix.db.models.location import Location
    from omnix.db.models.product import Product
    from omnix.db.models.supplier import Supplier
    from omnix.db.models.purchase_order import PurchaseOrder
    from omnix.db.models.audit_log import AuditLog


class Organization(TimestampMixin, Base):
    """
    Represents a client business — a wholesale distributor or a retail chain.
    Acts as the multi-tenant boundary for all operational data.
    """

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    business_type: Mapped[BusinessType] = mapped_column(
        Enum(BusinessType), nullable=False
    )
    gst_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, unique=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    locations: Mapped[List["Location"]] = relationship("Location", back_populates="organization")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="organization")
    suppliers: Mapped[List["Supplier"]] = relationship("Supplier", back_populates="organization")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="organization")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name='{self.name}' type={self.business_type}>"
