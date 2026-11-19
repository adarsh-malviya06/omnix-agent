"""
Realistic placeholder datasets for Phase 1 UI preview and validation.
All monetary values are stored as numeric (Decimal-compatible) amounts in INR.
Presentation formatting is applied by the currency utility (format_inr / format_inr_compact).
"""

from omnix.core.currency import format_inr, format_inr_compact

# ---------------------------------------------------------------------------
# Overview KPIs — raw numeric values used by format_inr at display time
# ---------------------------------------------------------------------------
OVERVIEW_KPIS_RAW = {
    "total_products": 148,
    "inventory_val": 23_84_250.00,     # ₹23,84,250.00
    "low_stock_count": 7,
    "stockout_risk_count": 3,
    "pending_pos": 4,
}

OVERVIEW_KPIS = {
    "total_products": str(OVERVIEW_KPIS_RAW["total_products"]),
    "inventory_val": format_inr(OVERVIEW_KPIS_RAW["inventory_val"]),
    "low_stock_count": str(OVERVIEW_KPIS_RAW["low_stock_count"]),
    "stockout_risk_count": str(OVERVIEW_KPIS_RAW["stockout_risk_count"]),
    "pending_pos": str(OVERVIEW_KPIS_RAW["pending_pos"]),
}

# ---------------------------------------------------------------------------
# Inventory — unit_cost stored as numeric INR; formatted string for display
# Realistic Indian wholesale grocery prices per unit
# ---------------------------------------------------------------------------
SAMPLE_INVENTORY = [
    {
        "sku": "SKU-RICE-25KG",
        "name": "Basmati Rice Premium 25 kg",
        "category": "Grains & Staples",
        "stock": 42,
        "min_threshold": 50,
        "unit_cost_num": 1_850.00,           # ₹1,850.00 per 25 kg bag (wholesale)
        "unit_cost": format_inr(1_850.00),
        "location": "Warehouse A-12",
        "status": "LOW_STOCK",
    },
    {
        "sku": "SKU-OIL-5L",
        "name": "Sunflower Cooking Oil 5 L",
        "category": "Edible Oils",
        "stock": 180,
        "min_threshold": 60,
        "unit_cost_num": 760.00,             # ₹760.00 per 5 L tin
        "unit_cost": format_inr(760.00),
        "location": "Warehouse B-04",
        "status": "IN_STOCK",
    },
    {
        "sku": "SKU-SUGAR-50KG",
        "name": "Refined White Sugar 50 kg",
        "category": "Grains & Staples",
        "stock": 8,
        "min_threshold": 25,
        "unit_cost_num": 2_200.00,           # ₹2,200.00 per 50 kg bag
        "unit_cost": format_inr(2_200.00),
        "location": "Warehouse A-08",
        "status": "OUT_OF_STOCK",
    },
    {
        "sku": "SKU-FLOUR-10KG",
        "name": "All-Purpose Wheat Flour 10 kg",
        "category": "Baking Supplies",
        "stock": 95,
        "min_threshold": 40,
        "unit_cost_num": 420.00,             # ₹420.00 per 10 kg bag
        "unit_cost": format_inr(420.00),
        "location": "Storefront Shelf 3",
        "status": "IN_STOCK",
    },
    {
        "sku": "SKU-TEA-500G",
        "name": "Organic Black Tea 500 g",
        "category": "Beverages",
        "stock": 14,
        "min_threshold": 30,
        "unit_cost_num": 380.00,             # ₹380.00 per 500 g packet
        "unit_cost": format_inr(380.00),
        "location": "Storefront Shelf 1",
        "status": "LOW_STOCK",
    },
]

# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------
SAMPLE_SUPPLIERS = [
    {
        "id": "SUP-101",
        "name": "AgroGlobal Commodities Ltd",
        "category": "Grains & Bulk Agro",
        "reliability_score": "96.4%",
        "avg_lead_days": 4,
        "status": "ACTIVE",
        "contact": "orders@agroglobal.in",
    },
    {
        "id": "SUP-102",
        "name": "Apex Foodservice Logistics",
        "category": "FMCG & Staples",
        "reliability_score": "91.8%",
        "avg_lead_days": 2,
        "status": "ACTIVE",
        "contact": "dispatch@apexfood.in",
    },
    {
        "id": "SUP-103",
        "name": "Pacific Oils & Fats Corp",
        "category": "Edible Oils",
        "reliability_score": "88.2%",
        "avg_lead_days": 7,
        "status": "ACTIVE",
        "contact": "sales@pacific-oils.in",
    },
    {
        "id": "SUP-104",
        "name": "Delta Packaging Supplies",
        "category": "Packaging",
        "reliability_score": "74.0%",
        "avg_lead_days": 12,
        "status": "REVIEW_REQUIRED",
        "contact": "support@deltapack.in",
    },
]

# ---------------------------------------------------------------------------
# Purchase Orders — total_amount_num stored as raw INR numeric
# Realistic Indian wholesale PO values
#   PO-0089: 100x Rice 25kg @ ₹1,850 + 50x Sugar 50kg @ ₹2,200 = ₹2,95,000
#   PO-0088: 60x Flour 10kg @ ₹420 = ₹25,200
#   PO-0087: 120x Oil 5L @ ₹760 = ₹91,200
# ---------------------------------------------------------------------------
SAMPLE_PURCHASE_ORDERS = [
    {
        "po_number": "PO-2026-0089",
        "supplier": "AgroGlobal Commodities Ltd",
        "items": "Basmati Rice 25 kg (×100), Sugar 50 kg (×50)",
        "total_amount_num": 2_95_000.00,
        "total_amount": format_inr(2_95_000.00),
        "date_created": "2026-11-17",
        "status": "PENDING_APPROVAL",
        "flag": f"High Value (> {format_inr(4_00_000)})",
    },
    {
        "po_number": "PO-2026-0088",
        "supplier": "Apex Foodservice Logistics",
        "items": "All-Purpose Wheat Flour 10 kg (×60)",
        "total_amount_num": 25_200.00,
        "total_amount": format_inr(25_200.00),
        "date_created": "2026-11-16",
        "status": "APPROVED",
        "flag": "Auto-Validated",
    },
    {
        "po_number": "PO-2026-0087",
        "supplier": "Pacific Oils & Fats Corp",
        "items": "Sunflower Cooking Oil 5 L (×120)",
        "total_amount_num": 91_200.00,
        "total_amount": format_inr(91_200.00),
        "date_created": "2026-11-15",
        "status": "COMPLETED",
        "flag": "Delivered",
    },
]

# ---------------------------------------------------------------------------
# Activity Logs
# ---------------------------------------------------------------------------
SAMPLE_ACTIVITY_LOGS = [
    {
        "timestamp": "2026-11-17 18:32:10",
        "actor": "System Monitor",
        "action": "Inventory Scan Triggered",
        "details": "Identified 2 SKUs below safety stock threshold.",
    },
    {
        "timestamp": "2026-11-17 19:05:44",
        "actor": "Procurement Agent",
        "action": "Drafted Purchase Order PO-2026-0089",
        "details": f"Calculated suggested order: 100× Rice 25 kg, 50× Sugar 50 kg. Total: {format_inr(2_95_000.00)}.",
    },
    {
        "timestamp": "2026-11-17 19:10:02",
        "actor": "Demo Manager",
        "action": "PO-2026-0088 Approved",
        "details": f"User authorized PO-2026-0088 for {format_inr(25_200.00)} via web dashboard.",
    },
]
