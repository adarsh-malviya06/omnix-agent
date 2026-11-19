"""
Supplier model — a vendor that supplies products to an organisation.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.supplier_product import SupplierProduct
    from omnix.db.models.purchase_order import PurchaseOrder


class Supplier(TimestampMixin, Base):
    """
    A registered vendor entity.

    reliability_score: 0.0–100.0 percentage representing on-time delivery history.
    avg_lead_days: Average calendar days between placing an order and receiving goods.
    """

    __tablename__ = "suppliers"

    __table_args__ = (
        CheckConstraint(
            "reliability_score >= 0 AND reliability_score <= 100",
            name="ck_supplier_reliability_range",
        ),
        CheckConstraint("avg_lead_days >= 0", name="ck_supplier_lead_days_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reliability_score: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=100.00
    )
    avg_lead_days: Mapped[int] = mapped_column(Numeric(5, 1), nullable=False, default=7)
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="e.g. 'Net 30', '50% advance + 50% on delivery'"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="suppliers")
    supplier_products: Mapped[List["SupplierProduct"]] = relationship(
        "SupplierProduct", back_populates="supplier"
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="supplier"
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} code='{self.code}' name='{self.name}'>"
