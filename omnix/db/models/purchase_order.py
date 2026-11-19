"""
PurchaseOrder and PurchaseOrderItem models.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, PurchaseOrderStatus, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.supplier import Supplier
    from omnix.db.models.location import Location
    from omnix.db.models.product import Product
    from omnix.db.models.approval import Approval
    from omnix.db.models.recommendation import Recommendation
    from omnix.db.models.inventory_movement import InventoryMovement


class PurchaseOrder(TimestampMixin, Base):
    """
    Purchase Order header model.
    """

    __tablename__ = "purchase_orders"

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_po_total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    destination_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus), nullable=False, default=PurchaseOrderStatus.DRAFT, index=True
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="purchase_orders")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")
    destination_location: Mapped["Location"] = relationship("Location")
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan"
    )
    approvals: Mapped[List["Approval"]] = relationship(
        "Approval", back_populates="purchase_order", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="purchase_order"
    )
    movements: Mapped[List["InventoryMovement"]] = relationship(
        "InventoryMovement", back_populates="purchase_order"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder id={self.id} po_number='{self.po_number}' status={self.status}>"


class PurchaseOrderItem(TimestampMixin, Base):
    """
    Line item inside a purchase order.
    """

    __tablename__ = "purchase_order_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_poi_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_poi_unit_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="ck_poi_subtotal_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="purchase_order_items")

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrderItem id={self.id} "
            f"po_id={self.purchase_order_id} product_id={self.product_id} qty={self.quantity}>"
        )
