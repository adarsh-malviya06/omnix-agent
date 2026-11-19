"""
Seed script populating realistic, consistent sample data for:
A. Wholesale & Distribution (Grains, Bulk Edibles)
B. Retail Stores & Supermarkets (Daily FMCG, Packaged Foods)
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from omnix.db.base import (
    ApprovalAction,
    AuditEventType,
    BusinessType,
    LocationType,
    MovementType,
    PurchaseOrderStatus,
    RecommendationStatus,
    UserRole,
)
from omnix.db.models import (
    Approval,
    AuditLog,
    DemandHistory,
    Inventory,
    InventoryMovement,
    Location,
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Recommendation,
    Supplier,
    SupplierProduct,
    User,
)


def seed_database(db: Session):
    """
    Idempotent seed function. Checks for existing data and only seeds if empty or missing.
    """
    # 1. Check if organization already exists
    org_wholesale = db.query(Organization).filter_by(name="AgroBulk Logistics & Wholesale").first()
    if not org_wholesale:
        org_wholesale = Organization(
            name="AgroBulk Logistics & Wholesale",
            business_type=BusinessType.WHOLESALE,
            gst_number="27AABCA1234F1Z5",
            contact_email="operations@agrobulk.in",
            contact_phone="+91-9820011223",
            address="Plot 45, APMC Market Yard, Vashi",
            city="Navi Mumbai",
            state="Maharashtra",
        )
        db.add(org_wholesale)

    org_retail = db.query(Organization).filter_by(name="QuickBazaar Supermarkets").first()
    if not org_retail:
        org_retail = Organization(
            name="QuickBazaar Supermarkets",
            business_type=BusinessType.SUPERMARKET,
            gst_number="27AABCQ9876K1Z2",
            contact_email="procurement@quickbazaar.in",
            contact_phone="+91-9820055443",
            address="Tower B, Central Mall, Andheri West",
            city="Mumbai",
            state="Maharashtra",
        )
        db.add(org_retail)

    db.flush()

    # 2. Users
    user_admin = db.query(User).filter_by(email="admin@agrobulk.in").first()
    if not user_admin:
        user_admin = User(
            organization_id=org_wholesale.id,
            full_name="Rajesh Sharma",
            email="admin@agrobulk.in",
            hashed_password="insecure_dev_hash",
            role=UserRole.ADMIN,
        )
        db.add(user_admin)

    user_manager = db.query(User).filter_by(email="procurement@quickbazaar.in").first()
    if not user_manager:
        user_manager = User(
            organization_id=org_retail.id,
            full_name="Pooja Mehta",
            email="procurement@quickbazaar.in",
            hashed_password="insecure_dev_hash",
            role=UserRole.MANAGER,
        )
        db.add(user_manager)

    db.flush()

    # 3. Locations
    wh_main = db.query(Location).filter_by(code="WH-VASHI").first()
    if not wh_main:
        wh_main = Location(
            organization_id=org_wholesale.id,
            name="Central Distribution Warehouse Vashi",
            code="WH-VASHI",
            location_type=LocationType.WAREHOUSE,
            city="Navi Mumbai",
            state="Maharashtra",
        )
        db.add(wh_main)

    store_bandra = db.query(Location).filter_by(code="ST-BANDRA").first()
    if not store_bandra:
        store_bandra = Location(
            organization_id=org_retail.id,
            name="QuickBazaar Bandra West Store",
            code="ST-BANDRA",
            location_type=LocationType.STORE,
            city="Mumbai",
            state="Maharashtra",
        )
        db.add(store_bandra)

    db.flush()

    # 4. Products
    products_data = [
        # Wholesale products
        {
            "org_id": org_wholesale.id,
            "sku": "SKU-RICE-25KG",
            "name": "Basmati Rice Premium 25 kg",
            "category": "Grains & Staples",
            "uom": "bag",
            "pack_size": Decimal("25"),
            "standard_cost": Decimal("1850.00"),
            "selling_price": Decimal("2250.00"),
            "reorder_point": 50,
            "reorder_quantity": 100,
            "safety_stock": 20,
        },
        {
            "org_id": org_wholesale.id,
            "sku": "SKU-SUGAR-50KG",
            "name": "Refined White Sugar 50 kg",
            "category": "Grains & Staples",
            "uom": "bag",
            "pack_size": Decimal("50"),
            "standard_cost": Decimal("2200.00"),
            "selling_price": Decimal("2550.00"),
            "reorder_point": 25,
            "reorder_quantity": 50,
            "safety_stock": 10,
        },
        {
            "org_id": org_wholesale.id,
            "sku": "SKU-OIL-15L",
            "name": "Sunflower Cooking Oil 15 L Tin",
            "category": "Edible Oils",
            "uom": "tin",
            "pack_size": Decimal("15"),
            "standard_cost": Decimal("2150.00"),
            "selling_price": Decimal("2450.00"),
            "reorder_point": 40,
            "reorder_quantity": 80,
            "safety_stock": 15,
        },
        # Retail Supermarket products
        {
            "org_id": org_retail.id,
            "sku": "SKU-ATTA-5KG",
            "name": "Chakki Fresh Atta 5 kg",
            "category": "Flour & Atta",
            "uom": "packet",
            "pack_size": Decimal("5"),
            "standard_cost": Decimal("210.00"),
            "selling_price": Decimal("265.00"),
            "reorder_point": 60,
            "reorder_quantity": 120,
            "safety_stock": 25,
        },
        {
            "org_id": org_retail.id,
            "sku": "SKU-TEA-500G",
            "name": "Premium Assam Tea 500 g",
            "category": "Beverages",
            "uom": "box",
            "pack_size": Decimal("0.5"),
            "standard_cost": Decimal("320.00"),
            "selling_price": Decimal("410.00"),
            "reorder_point": 30,
            "reorder_quantity": 60,
            "safety_stock": 15,
        },
        {
            "org_id": org_retail.id,
            "sku": "SKU-GHEE-1L",
            "name": "Pure Cow Ghee 1 L Jar",
            "category": "Dairy & Ghee",
            "uom": "jar",
            "pack_size": Decimal("1"),
            "standard_cost": Decimal("580.00"),
            "selling_price": Decimal("690.00"),
            "reorder_point": 35,
            "reorder_quantity": 70,
            "safety_stock": 10,
        },
    ]

    product_map = {}
    for pdata in products_data:
        prod = db.query(Product).filter_by(sku=pdata["sku"]).first()
        if not prod:
            prod = Product(
                organization_id=pdata["org_id"],
                sku=pdata["sku"],
                name=pdata["name"],
                category=pdata["category"],
                uom=pdata["uom"],
                pack_size=pdata["pack_size"],
                standard_cost=pdata["standard_cost"],
                selling_price=pdata["selling_price"],
                reorder_point=pdata["reorder_point"],
                reorder_quantity=pdata["reorder_quantity"],
                safety_stock=pdata["safety_stock"],
            )
            db.add(prod)
            db.flush()
        product_map[pdata["sku"]] = prod

    # 5. Suppliers
    suppliers_data = [
        {
            "org_id": org_wholesale.id,
            "code": "SUP-AGRO-01",
            "name": "AgroGlobal Commodities Ltd",
            "reliability_score": Decimal("96.50"),
            "avg_lead_days": Decimal("3.5"),
            "payment_terms": "Net 30",
        },
        {
            "org_id": org_wholesale.id,
            "code": "SUP-BHARAT-02",
            "name": "Bharat Agro Supplies",
            "reliability_score": Decimal("88.00"),
            "avg_lead_days": Decimal("6.0"),
            "payment_terms": "Advance 20%, Balance Net 15",
        },
        {
            "org_id": org_retail.id,
            "code": "SUP-APEX-01",
            "name": "Apex FMCG Distributors",
            "reliability_score": Decimal("93.20"),
            "avg_lead_days": Decimal("2.0"),
            "payment_terms": "Net 15",
        },
        {
            "org_id": org_retail.id,
            "code": "SUP-METRO-02",
            "name": "Metro Daily Supplies",
            "reliability_score": Decimal("85.50"),
            "avg_lead_days": Decimal("4.0"),
            "payment_terms": "Weekly Settlement",
        },
    ]

    supplier_map = {}
    for sdata in suppliers_data:
        sup = db.query(Supplier).filter_by(code=sdata["code"]).first()
        if not sup:
            sup = Supplier(
                organization_id=sdata["org_id"],
                code=sdata["code"],
                name=sdata["name"],
                reliability_score=sdata["reliability_score"],
                avg_lead_days=sdata["avg_lead_days"],
                payment_terms=sdata["payment_terms"],
            )
            db.add(sup)
            db.flush()
        supplier_map[sdata["code"]] = sup

    # 6. Supplier Products (Pricing, MOQs, Lead times)
    sp_data = [
        # AgroGlobal sells Rice and Sugar
        ("SUP-AGRO-01", "SKU-RICE-25KG", Decimal("1820.00"), 50, 3),
        ("SUP-AGRO-01", "SKU-SUGAR-50KG", Decimal("2180.00"), 30, 4),
        # Bharat Agro sells Rice (cheaper, higher lead time) and Oil
        ("SUP-BHARAT-02", "SKU-RICE-25KG", Decimal("1790.00"), 100, 7),
        ("SUP-BHARAT-02", "SKU-OIL-15L", Decimal("2120.00"), 40, 5),
        # Apex FMCG sells Atta, Tea, Ghee
        ("SUP-APEX-01", "SKU-ATTA-5KG", Decimal("205.00"), 50, 2),
        ("SUP-APEX-01", "SKU-TEA-500G", Decimal("310.00"), 20, 2),
        ("SUP-APEX-01", "SKU-GHEE-1L", Decimal("570.00"), 25, 3),
        # Metro Daily sells Atta and Tea
        ("SUP-METRO-02", "SKU-ATTA-5KG", Decimal("200.00"), 100, 4),
        ("SUP-METRO-02", "SKU-TEA-500G", Decimal("315.00"), 30, 3),
    ]

    for sup_code, sku, price, moq, lead_days in sp_data:
        sup = supplier_map[sup_code]
        prod = product_map[sku]
        sp = (
            db.query(SupplierProduct)
            .filter_by(supplier_id=sup.id, product_id=prod.id)
            .first()
        )
        if not sp:
            sp = SupplierProduct(
                supplier_id=sup.id,
                product_id=prod.id,
                unit_price=price,
                moq=moq,
                lead_days=lead_days,
                is_available=True,
            )
            db.add(sp)

    # 7. Inventory Levels
    inventory_data = [
        # Wholesale warehouse stock
        ("SKU-RICE-25KG", wh_main.id, 35, 5, Decimal("1820.00")),   # Low stock (point=50)
        ("SKU-SUGAR-50KG", wh_main.id, 0, 0, Decimal("2180.00")),    # Out of stock!
        ("SKU-OIL-15L", wh_main.id, 120, 10, Decimal("2120.00")),   # Healthy
        # Retail store stock
        ("SKU-ATTA-5KG", store_bandra.id, 45, 0, Decimal("205.00")), # Low stock (point=60)
        ("SKU-TEA-500G", store_bandra.id, 80, 5, Decimal("310.00")), # Healthy (point=30)
        ("SKU-GHEE-1L", store_bandra.id, 8, 2, Decimal("570.00")),    # Critical low (point=35)
    ]

    for sku, loc_id, on_hand, reserved, cost in inventory_data:
        prod = product_map[sku]
        inv = db.query(Inventory).filter_by(product_id=prod.id, location_id=loc_id).first()
        if not inv:
            inv = Inventory(
                product_id=prod.id,
                location_id=loc_id,
                quantity_on_hand=on_hand,
                quantity_reserved=reserved,
                last_purchase_cost=cost,
            )
            db.add(inv)

    db.flush()

    # 8. Demand History (last 30 days)
    today = date.today()
    for sku, prod in product_map.items():
        # Check if history exists
        has_history = db.query(DemandHistory).filter_by(product_id=prod.id).first()
        if not has_history:
            loc_id = wh_main.id if prod.organization_id == org_wholesale.id else store_bandra.id
            for i in range(30):
                d = today - timedelta(days=30 - i)
                # Deterministic consumption pattern
                base_qty = 8 if "RICE" in sku else (5 if "SUGAR" in sku else 12)
                variation = (i % 5) - 2
                qty_sold = max(1, base_qty + variation)
                rev = Decimal(str(qty_sold)) * prod.selling_price
                dh = DemandHistory(
                    product_id=prod.id,
                    location_id=loc_id,
                    record_date=d,
                    quantity_sold=qty_sold,
                    quantity_returned=1 if i % 10 == 0 else 0,
                    revenue=rev,
                )
                db.add(dh)

    # 9. Example Purchase Orders
    po1 = db.query(PurchaseOrder).filter_by(po_number="PO-2026-0001").first()
    if not po1:
        po1 = PurchaseOrder(
            organization_id=org_wholesale.id,
            po_number="PO-2026-0001",
            supplier_id=supplier_map["SUP-AGRO-01"].id,
            destination_location_id=wh_main.id,
            status=PurchaseOrderStatus.PENDING_APPROVAL,
            currency="INR",
            total_amount=Decimal("182000.00"),
            notes="Replenishment order for Basmati Rice",
            order_date=datetime.now(timezone.utc),
        )
        db.add(po1)
        db.flush()

        item1 = PurchaseOrderItem(
            purchase_order_id=po1.id,
            product_id=product_map["SKU-RICE-25KG"].id,
            quantity=100,
            unit_price=Decimal("1820.00"),
            subtotal=Decimal("182000.00"),
        )
        db.add(item1)

    # 10. Audit Log
    log1 = db.query(AuditLog).filter_by(action="SYSTEM_INIT_SEED").first()
    if not log1:
        log1 = AuditLog(
            organization_id=org_wholesale.id,
            user_id=user_admin.id,
            event_type=AuditEventType.SYSTEM_EVENT,
            actor="SeedService",
            action="SYSTEM_INIT_SEED",
            details="Initial sample business data loaded successfully.",
        )
        db.add(log1)

    db.commit()


if __name__ == "__main__":
    from omnix.db.session import SessionLocal, init_db
    print("Initializing database tables...")
    init_db()
    print("Seeding demo operations data...")
    _session = SessionLocal()
    try:
        seed_database(_session)
        print("Database initialized and demo data seeded successfully.")
    finally:
        _session.close()
