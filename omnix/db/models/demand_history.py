"""
DemandHistory model — daily consumption records used by the ML forecasting service.
"""

from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.product import Product
    from omnix.db.models.location import Location


class DemandHistory(TimestampMixin, Base):
    """
    One record per product per location per day capturing units consumed/sold.

    quantity_sold: actual units consumed/sold that day.
    quantity_returned: units returned/credited back that day.
    net_demand: computed property = quantity_sold - quantity_returned.

    The ML service reads this table to build training datasets for forecasting.
    """

    __tablename__ = "demand_history"

    __table_args__ = (
        CheckConstraint("quantity_sold >= 0", name="ck_dh_sold_non_negative"),
        CheckConstraint("quantity_returned >= 0", name="ck_dh_returned_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_returned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Optional revenue capture for analytics
    revenue: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True,
        comment="Total sales revenue for the day in INR"
    )
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="demand_history")
    location: Mapped["Location"] = relationship("Location")

    @property
    def net_demand(self) -> int:
        return max(0, self.quantity_sold - self.quantity_returned)

    def __repr__(self) -> str:
        return (
            f"<DemandHistory product_id={self.product_id} "
            f"date={self.record_date} "
            f"sold={self.quantity_sold}>"
        )
