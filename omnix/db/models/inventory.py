"""
Inventory model — current stock position for a product at a specific location.
One row per (product, location) pair per organisation.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.product import Product
    from omnix.db.models.location import Location


class Inventory(TimestampMixin, Base):
    """
    Current stock level for a product at a physical location.

    Constraints:
      - quantity_on_hand must be >= 0 (stock cannot go negative).
      - Unique on (product_id, location_id) — one record per product-location pair.
    """

    __tablename__ = "inventory"

    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_inventory_product_location"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_qty_non_negative"),
        CheckConstraint("quantity_reserved >= 0", name="ck_inventory_reserved_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Units already allocated to outgoing orders but not yet dispatched"
    )
    # Snapshot of cost used for inventory valuation (can differ from product.standard_cost)
    last_purchase_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00"),
        comment="Unit cost from the most recent purchase receipt in INR"
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_records")
    location: Mapped["Location"] = relationship("Location", back_populates="inventory_records")

    @property
    def quantity_available(self) -> int:
        """Net available quantity after deducting reserved stock."""
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    @property
    def is_low_stock(self) -> bool:
        """True when on-hand stock is at or below the product's reorder point."""
        return self.quantity_on_hand <= self.product.reorder_point

    @property
    def is_out_of_stock(self) -> bool:
        """True when no units are available."""
        return self.quantity_on_hand == 0

    def __repr__(self) -> str:
        return (
            f"<Inventory product_id={self.product_id} "
            f"location_id={self.location_id} "
            f"qty={self.quantity_on_hand}>"
        )
