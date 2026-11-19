"""
Supplier API endpoints for vendor lookup and multi-attribute scoring.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from omnix.db.session import get_db
from omnix.schemas.supplier import (
    SupplierComparisonResponse,
    SupplierProductResponse,
    SupplierResponse,
)
from omnix.services.supplier_service import (
    compare_suppliers_for_product,
    get_all_suppliers,
    get_supplier_by_id,
    get_supplier_products,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers & Vendors"])


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    organization_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """Retrieve all active suppliers."""
    return get_all_suppliers(db, organization_id=organization_id)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """Fetch supplier profile by ID."""
    return get_supplier_by_id(db, supplier_id=supplier_id)


@router.get("/{supplier_id}/products", response_model=List[SupplierProductResponse])
def list_supplier_products(supplier_id: int, db: Session = Depends(get_db)):
    """Fetch product catalog mappings for a specific supplier."""
    return get_supplier_products(db, supplier_id=supplier_id)


@router.get("/compare/{product_id}", response_model=SupplierComparisonResponse)
def compare_product_suppliers(product_id: int, db: Session = Depends(get_db)):
    """Compare vendor quotes, lead times, and reliability scores for a product."""
    return compare_suppliers_for_product(db, product_id=product_id)
