"""
InventoryMovement model — immutable ledger of every stock transaction.
Each movement records a quantity delta and the resulting balance.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, MovementType, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.product import Product
    from omnix.db.models.location import Location
    from omnix.db.models.purchase_order import PurchaseOrder


class InventoryMovement(TimestampMixin, Base):
    """
    An immutable ledger entry for every stock in/out event.

    quantity_delta is positive for receipts, negative for issues.
    quantity_after records the balance immediately after this movement.
    Reference columns link back to the originating business document.
    """

    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType), nullable=False, index=True
    )
    quantity_delta: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Positive = stock in, Negative = stock out"
    )
    quantity_after: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Balance on-hand immediately after this movement"
    )
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True,
        comment="Unit cost at time of movement in INR"
    )
    total_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True,
        comment="Total cost of this movement in INR"
    )
    # Reference document links
    purchase_order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="External reference: sale invoice, transfer slip, adjustment note"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="movements")
    location: Mapped["Location"] = relationship("Location", back_populates="movements")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="movements"
    )

    def __repr__(self) -> str:
        return (
            f"<InventoryMovement id={self.id} "
            f"product_id={self.product_id} "
            f"type={self.movement_type} "
            f"delta={self.quantity_delta:+d}>"
        )
