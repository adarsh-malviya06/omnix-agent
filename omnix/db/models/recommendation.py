"""
Recommendation model for AI and rule-generated procurement recommendations.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, RecommendationStatus, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.product import Product
    from omnix.db.models.supplier import Supplier
    from omnix.db.models.location import Location
    from omnix.db.models.purchase_order import PurchaseOrder


class Recommendation(TimestampMixin, Base):
    """
    Automated or agent-driven replenishment recommendation.
    """

    __tablename__ = "recommendations"

    __table_args__ = (
        CheckConstraint("suggested_quantity > 0", name="ck_rec_suggested_qty_positive"),
        CheckConstraint("estimated_cost >= 0", name="ck_rec_estimated_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    suggested_supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purchase_order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus), nullable=False, default=RecommendationStatus.PENDING, index=True
    )
    suggested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    product: Mapped["Product"] = relationship("Product", back_populates="recommendations")
    suggested_supplier: Mapped[Optional["Supplier"]] = relationship("Supplier")
    location: Mapped["Location"] = relationship("Location")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="recommendations"
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation id={self.id} product_id={self.product_id} "
            f"qty={self.suggested_quantity} status={self.status}>"
        )
