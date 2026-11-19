"""
Supplier business service.
Transparent supplier lookup, scoring, and multi-attribute price/delivery comparison.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from omnix.core.exceptions import NotFoundException
from omnix.db.models import Product, Supplier, SupplierProduct
from omnix.schemas.supplier import SupplierComparisonItem, SupplierComparisonResponse


def get_all_suppliers(db: Session, organization_id: Optional[int] = None) -> List[Supplier]:
    """Retrieve all active suppliers."""
    query = db.query(Supplier).filter(Supplier.is_active == True)
    if organization_id:
        query = query.filter(Supplier.organization_id == organization_id)
    return query.all()


def get_supplier_by_id(db: Session, supplier_id: int) -> Supplier:
    """Fetch supplier by ID or raise NotFoundException."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise NotFoundException(f"Supplier with ID {supplier_id} not found.")
    return supplier


def get_supplier_products(
    db: Session, supplier_id: Optional[int] = None, product_id: Optional[int] = None
) -> List[SupplierProduct]:
    """Fetch supplier catalog mappings."""
    query = db.query(SupplierProduct).filter(SupplierProduct.is_available == True)
    if supplier_id:
        query = query.filter(SupplierProduct.supplier_id == supplier_id)
    if product_id:
        query = query.filter(SupplierProduct.product_id == product_id)
    return query.all()


def calculate_supplier_score(
    unit_price: Decimal,
    min_price: Decimal,
    lead_days: int,
    min_lead: int,
    reliability_score: Decimal,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Transparent multi-attribute scoring model for supplier selection.
    
    Default weights:
      - Price: 40% (relative to lowest available quote)
      - Delivery Speed: 30% (relative to fastest available lead time)
      - Reliability: 30% (historical on-time % / 100)
    
    Returns composite score from 0.0 to 100.0.
    """
    if weights is None:
        weights = {"price": 0.40, "lead": 0.30, "reliability": 0.30}

    # Price score: 100 for min_price, lower as price increases
    # formula: (min_price / unit_price) * 100
    price_score = float((min_price / unit_price) * 100) if unit_price > 0 else 0.0

    # Lead time score: 100 for fastest delivery
    # formula: (min_lead / lead_days) * 100
    lead_score = (min_lead / lead_days * 100) if lead_days > 0 else 100.0

    # Reliability score: direct percentage (0-100)
    rel_score = float(reliability_score)

    composite = (
        weights["price"] * price_score
        + weights["lead"] * lead_score
        + weights["reliability"] * rel_score
    )
    return round(composite, 2)


def compare_suppliers_for_product(db: Session, product_id: int) -> SupplierComparisonResponse:
    """
    Compare all available vendor quotes for a specific product.
    Ranks suppliers using the transparent multi-attribute scoring model.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundException(f"Product with ID {product_id} not found.")

    supplier_products = (
        db.query(SupplierProduct)
        .join(Supplier)
        .filter(
            SupplierProduct.product_id == product_id,
            SupplierProduct.is_available == True,
            Supplier.is_active == True,
        )
        .all()
    )

    if not supplier_products:
        return SupplierComparisonResponse(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            quotes=[],
        )

    # Determine baselines for relative scoring
    min_price = min(sp.unit_price for sp in supplier_products)
    min_lead = min(sp.lead_days for sp in supplier_products)

    items = []
    for sp in supplier_products:
        score = calculate_supplier_score(
            unit_price=sp.unit_price,
            min_price=min_price,
            lead_days=sp.lead_days,
            min_lead=min_lead,
            reliability_score=sp.supplier.reliability_score,
        )
        items.append(
            SupplierComparisonItem(
                supplier_id=sp.supplier_id,
                supplier_name=sp.supplier.name,
                supplier_code=sp.supplier.code,
                unit_price=sp.unit_price,
                lead_days=sp.lead_days,
                moq=sp.moq,
                reliability_score=sp.supplier.reliability_score,
                composite_score=score,
            )
        )

    # Sort descending by composite score
    items.sort(key=lambda x: x.composite_score, reverse=True)
    if items:
        items[0].is_recommended = True

    return SupplierComparisonResponse(
        product_id=product.id,
        product_name=product.name,
        product_sku=product.sku,
        quotes=items,
    )
