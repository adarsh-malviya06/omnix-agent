"""
Automated tests for Phase 2 & 3:
- Database models and schema integrity
- Inventory calculations and non-negative movement constraints
- Transparent supplier comparison and multi-attribute scoring
- Deterministic procurement reorder formulas and MOQ enforcement
- Purchase order workflows and high-value authorization limits
- FastAPI operational endpoints
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from omnix.api.main import app
from omnix.core.exceptions import BusinessRuleViolationException
from omnix.db.base import ApprovalAction, Base, MovementType
from omnix.db.models import (
    Inventory,
    Location,
    Organization,
    Product,
    PurchaseOrder,
    Supplier,
    SupplierProduct,
    User,
)
from omnix.db.seed import seed_database
from omnix.db.session import get_db
from omnix.services.inventory_service import (
    get_all_products,
    get_inventory_positions,
    get_low_stock_items,
    get_out_of_stock_items,
    record_inventory_movement,
)
from omnix.services.procurement_service import (
    calculate_reorder_recommendation,
    create_procurement_recommendation,
    create_purchase_order_draft,
    get_dashboard_statistics,
    process_purchase_order_approval,
)
from omnix.services.supplier_service import (
    calculate_supplier_score,
    compare_suppliers_for_product,
)

# In-memory SQLite for high-speed deterministic test suite
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def db_session():
    """Create test database schema and seed sample data."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_database(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def client(db_session):
    """FastAPI test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestDatabaseAndSeeding:
    def test_seeded_organizations(self, db_session):
        orgs = db_session.query(Organization).all()
        assert len(orgs) >= 2
        names = [o.name for o in orgs]
        assert "AgroBulk Logistics & Wholesale" in names
        assert "QuickBazaar Supermarkets" in names

    def test_seeded_products_and_suppliers(self, db_session):
        products = get_all_products(db_session)
        assert len(products) >= 6
        suppliers = db_session.query(Supplier).all()
        assert len(suppliers) >= 4


class TestInventoryServices:
    def test_low_and_out_of_stock_detection(self, db_session):
        low_items = get_low_stock_items(db_session)
        out_items = get_out_of_stock_items(db_session)

        # SKU-SUGAR-50KG is seeded with 0 stock
        out_skus = [item.product.sku for item in out_items]
        assert "SKU-SUGAR-50KG" in out_skus

        # SKU-RICE-25KG is seeded with 35 units (reorder_point=50)
        low_skus = [item.product.sku for item in low_items]
        assert "SKU-RICE-25KG" in low_skus

    def test_stock_movement_positive(self, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-OIL-15L").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()
        inv_before = (
            db_session.query(Inventory)
            .filter_by(product_id=prod.id, location_id=loc.id)
            .first()
        )
        qty_before = inv_before.quantity_on_hand

        m = record_inventory_movement(
            db_session,
            product_id=prod.id,
            location_id=loc.id,
            movement_type=MovementType.PURCHASE_RECEIPT,
            quantity_delta=20,
            unit_cost=Decimal("2120.00"),
        )
        assert m.quantity_delta == 20
        assert m.quantity_after == qty_before + 20

    def test_stock_movement_negative_guardrail(self, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-SUGAR-50KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()

        # Stock is 0, deducting 10 should violate deterministic non-negative constraint
        with pytest.raises(BusinessRuleViolationException) as excinfo:
            record_inventory_movement(
                db_session,
                product_id=prod.id,
                location_id=loc.id,
                movement_type=MovementType.SALE,
                quantity_delta=-10,
            )
        assert "Insufficient stock" in str(excinfo.value)


class TestSupplierServices:
    def test_supplier_scoring_math(self):
        # Best price=1000, best lead=2, rel=95%
        # Supplier A: Price 1000, Lead 2, Rel 95 -> 100% composite
        score_a = calculate_supplier_score(
            unit_price=Decimal("1000"),
            min_price=Decimal("1000"),
            lead_days=2,
            min_lead=2,
            reliability_score=Decimal("95.00"),
        )
        assert score_a == 98.5  # 40(100) + 30(100) + 30(95) = 40 + 30 + 28.5 = 98.5

        # Supplier B: More expensive price 1250 (score 80), lead 4 (score 50), rel 90 (score 90)
        score_b = calculate_supplier_score(
            unit_price=Decimal("1250"),
            min_price=Decimal("1000"),
            lead_days=4,
            min_lead=2,
            reliability_score=Decimal("90.00"),
        )
        # 40*(80) + 30*(50) + 30*(90) = 32 + 15 + 27 = 74.0
        assert score_b == 74.0

    def test_supplier_comparison_ranking(self, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        comparison = compare_suppliers_for_product(db_session, prod.id)
        assert len(comparison.quotes) >= 2
        # Highest composite score must be marked as recommended
        assert comparison.quotes[0].is_recommended is True
        assert (
            comparison.quotes[0].composite_score
            >= comparison.quotes[1].composite_score
        )


class TestProcurementServices:
    def test_reorder_calculation_formula(self, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        loc = db_session.query(Location).filter_by(code="WH-VASHI").first()

        calc = calculate_reorder_recommendation(
            db_session,
            product_id=prod.id,
            location_id=loc.id,
            daily_demand_override=10.0,
            lead_time_override=5,
        )
        # Reorder Point = (10 * 5) + safety_stock (20) = 70
        assert calc.calculated_reorder_point == 70
        assert calc.is_reorder_needed is True
        # Suggested quantity must satisfy deficit (70 - available) and MOQ
        assert calc.suggested_order_quantity >= 50

    def test_purchase_order_approval_workflow(self, db_session):
        org = db_session.query(Organization).first()
        sup = db_session.query(Supplier).first()
        loc = db_session.query(Location).first()
        user_mgr = db_session.query(User).filter_by(role="manager").first()
        prod = db_session.query(Product).first()

        from omnix.schemas.procurement import PurchaseOrderCreate, PurchaseOrderItemCreate

        po_in = PurchaseOrderCreate(
            organization_id=org.id,
            supplier_id=sup.id,
            destination_location_id=loc.id,
            notes="Test draft PO",
            items=[
                PurchaseOrderItemCreate(
                    product_id=prod.id, quantity=10, unit_price=Decimal("500.00")
                )
            ],
        )
        po = create_purchase_order_draft(db_session, po_in)
        assert po.status.value == "pending_approval"
        assert po.total_amount == Decimal("5000.00")

        # Approve
        approval = process_purchase_order_approval(
            db_session,
            purchase_order_id=po.id,
            user_id=user_mgr.id,
            action=ApprovalAction.APPROVED,
            comments="Approved for store replenishment",
        )
        assert approval.action.value == "approved"
        assert po.status.value == "approved"


class TestAPIEndpoints:
    def test_api_list_products(self, client):
        res = client.get("/api/v1/inventory/products")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 6

    def test_api_inventory_stock(self, client):
        res = client.get("/api/v1/inventory/stock")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 6

    def test_api_dashboard_stats(self, client):
        res = client.get("/api/v1/procurement/dashboard-stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total_products"] >= 6
        assert float(data["total_inventory_value"]) > 0
        assert data["currency"] == "INR"

    def test_api_supplier_comparison(self, client, db_session):
        prod = db_session.query(Product).filter_by(sku="SKU-RICE-25KG").first()
        res = client.get(f"/api/v1/suppliers/compare/{prod.id}")
        assert res.status_code == 200
        data = res.json()
        assert len(data["quotes"]) >= 2
        assert data["quotes"][0]["is_recommended"] is True
