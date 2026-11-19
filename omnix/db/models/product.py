"""
Product model — master catalogue entry for every tracked SKU.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.inventory import Inventory
    from omnix.db.models.inventory_movement import InventoryMovement
    from omnix.db.models.supplier_product import SupplierProduct
    from omnix.db.models.demand_history import DemandHistory
    from omnix.db.models.purchase_order_item import PurchaseOrderItem
    from omnix.db.models.recommendation import Recommendation


class Product(TimestampMixin, Base):
    """
    Master product catalogue entry.

    Monetary columns (standard_cost, selling_price) use Numeric(14, 2)
    to avoid floating-point rounding errors in procurement calculations.
    Unit of measure (uom) is a free string: 'kg', 'litre', 'unit', 'carton', etc.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    uom: Mapped[str] = mapped_column(String(30), nullable=False, default="unit")
    pack_size: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3), nullable=True,
        comment="Number of base units in one stock-keeping pack (e.g. 25 for a 25 kg bag)"
    )
    # Monetary — stored as exact Decimal, formatted only in presentation layer
    standard_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True,
        comment="Standard purchase cost per UOM in INR"
    )
    selling_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True,
        comment="Retail selling price per UOM in INR"
    )
    # Reorder rules
    reorder_point: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Stock level that triggers a reorder alert"
    )
    reorder_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Default suggested replenishment quantity"
    )
    safety_stock: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Minimum buffer stock maintained at all times"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="products")
    inventory_records: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="product")
    movements: Mapped[List["InventoryMovement"]] = relationship("InventoryMovement", back_populates="product")
    supplier_products: Mapped[List["SupplierProduct"]] = relationship("SupplierProduct", back_populates="product")
    demand_history: Mapped[List["DemandHistory"]] = relationship("DemandHistory", back_populates="product")
    purchase_order_items: Mapped[List["PurchaseOrderItem"]] = relationship("PurchaseOrderItem", back_populates="product")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku='{self.sku}' name='{self.name}'>"
