"""
Unit tests for Business Analytics and Demand Trends backend data aggregations.
"""

from omnix.ui.backend_client import BackendClient


def test_analytics_kpis_structure():
    kpis = BackendClient.get_analytics_kpis()
    assert "total_inventory_value" in kpis
    assert "total_procurement_spend" in kpis
    assert "total_products" in kpis
    assert "total_suppliers" in kpis
    assert "healthy_count" in kpis
    assert "low_stock_count" in kpis
    assert "out_of_stock_count" in kpis

    # Confirm INR formatting
    assert kpis["total_inventory_value"].startswith("₹")
    assert kpis["total_procurement_spend"].startswith("₹")
    assert kpis["total_products"] >= 0


def test_spend_by_supplier_aggregation():
    spend_list = BackendClient.get_spend_by_supplier()
    assert isinstance(spend_list, list)
    for entry in spend_list:
        assert "supplier" in entry
        assert "total_spend" in entry
        assert "formatted_spend" in entry
        assert entry["formatted_spend"].startswith("₹")


def test_product_demand_analytics():
    inv = BackendClient.get_inventory_table()
    if inv:
        prod_id = inv[0]["id"]
        analytics = BackendClient.get_product_demand_analytics(prod_id)
        assert "has_data" in analytics
        assert "notes" in analytics
        assert "history" in analytics
        if analytics["has_data"]:
            assert isinstance(analytics["history"], list)
