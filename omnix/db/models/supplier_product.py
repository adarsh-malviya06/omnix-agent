"""
SupplierProduct model — catalogue of products offered by each supplier,
with their specific pricing, lead time and minimum order quantity.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.supplier import Supplier
    from omnix.db.models.product import Product


class SupplierProduct(TimestampMixin, Base):
    """
    Links a Supplier to a Product they can supply, with their quoted price,
    lead time and minimum order quantity (MOQ).

    One product can have multiple suppliers; each has potentially different:
      - unit_price  : quoted cost per UOM in INR
      - lead_days   : specific lead time for this supplier-product combination
      - moq         : minimum units that must be ordered per purchase
      - supplier_sku: supplier's own catalogue code for cross-referencing

    Unique on (supplier_id, product_id).
    """

    __tablename__ = "supplier_products"

    __table_args__ = (
        UniqueConstraint("supplier_id", "product_id", name="uq_supplier_product"),
        CheckConstraint("unit_price > 0", name="ck_sp_unit_price_positive"),
        CheckConstraint("moq >= 1", name="ck_sp_moq_at_least_one"),
        CheckConstraint("lead_days >= 0", name="ck_sp_lead_days_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    supplier_sku: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Supplier's internal catalogue code for this product"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False,
        comment="Quoted unit purchase price in INR"
    )
    moq: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Minimum order quantity per purchase"
    )
    lead_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7,
        comment="Calendar days from order placement to delivery for this item"
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_preferred_supplier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="supplier_products")
    product: Mapped["Product"] = relationship("Product", back_populates="supplier_products")

    def __repr__(self) -> str:
        return (
            f"<SupplierProduct supplier_id={self.supplier_id} "
            f"product_id={self.product_id} "
            f"price=₹{self.unit_price}>"
        )
