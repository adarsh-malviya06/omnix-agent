"""
Location model — physical warehouse or store belonging to an organisation.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, LocationType, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.inventory import Inventory
    from omnix.db.models.inventory_movement import InventoryMovement


class Location(TimestampMixin, Base):
    """
    Represents a physical facility — warehouse, distribution centre or retail store.
    Inventory records are always associated with a specific Location.
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location_type: Mapped[LocationType] = mapped_column(
        Enum(LocationType), nullable=False
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="locations")
    inventory_records: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="location")
    movements: Mapped[List["InventoryMovement"]] = relationship("InventoryMovement", back_populates="location")

    def __repr__(self) -> str:
        return f"<Location id={self.id} code='{self.code}' type={self.location_type}>"
