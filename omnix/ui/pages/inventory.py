"""
Inventory management page connected to live database records and real stock movement tracking.
"""

import pandas as pd
import streamlit as st
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_kpi_card, render_page_header


def render_inventory_page():
    """Render the Inventory Management view with real backend data and filtering."""
    render_page_header(
        title="Inventory Management",
        subtitle="Track stock levels, monitor warehouse locations, and audit SKU health",
    )

    # 1. Fetch live inventory
    raw_inv = BackendClient.get_inventory_table()

    total_skus = len(raw_inv)
    total_units = sum(i["stock"] for i in raw_inv)
    critical_low = sum(1 for i in raw_inv if i["status"] == "LOW_STOCK")
    out_of_stock = sum(1 for i in raw_inv if i["status"] == "OUT_OF_STOCK")

    # 2. Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total Active SKUs", str(total_skus), "In catalog")
    with c2:
        render_kpi_card("Total Physical Units", f"{total_units:,}", "Across all locations")
    with c3:
        render_kpi_card("Critical Low Stock", str(critical_low), "Below reorder threshold", "warning")
    with c4:
        render_kpi_card("Out of Stock", str(out_of_stock), "0 units available", "negative")

    # 3. Filter Toolbar & Live Table
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search_query = st.text_input("🔍 Search SKU or Product Name", placeholder="e.g. Rice, Sugar, Oil, Atta...")
    with f2:
        categories = ["All Categories"] + sorted(list(set(i["category"] for i in raw_inv))) if raw_inv else ["All Categories"]
        category_filter = st.selectbox("Category", categories)
    with f3:
        status_filter = st.selectbox("Stock Status", ["All Statuses", "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"])

    df = pd.DataFrame(raw_inv)
    if not df.empty:
        if search_query:
            df = df[df["name"].str.contains(search_query, case=False) | df["sku"].str.contains(search_query, case=False)]
        if category_filter != "All Categories":
            df = df[df["category"] == category_filter]
        if status_filter != "All Statuses":
            df = df[df["status"] == status_filter]

        st.dataframe(
            df[["sku", "name", "category", "location", "stock", "reserved", "available", "min_threshold", "unit_cost", "status"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "sku": "SKU Identifier",
                "name": "Product Name",
                "category": "Category",
                "location": "Facility",
                "stock": "On Hand",
                "reserved": "Reserved",
                "available": "Available",
                "min_threshold": "Safety Min",
                "unit_cost": "Cost / Unit",
                "status": "Health Status",
            },
        )
    else:
        st.info("No inventory data found.")

    st.markdown("</div>", unsafe_allow_html=True)

    # 4. Active Alerts & Governance Oversight
    active_alerts = BackendClient.get_active_alerts(limit=10)
    if active_alerts:
        with st.expander(f"⚠️ Active Inventory Alerts ({len(active_alerts)} unresolved)", expanded=False):
            alert_df = pd.DataFrame([
                {
                    "Alert ID": a["id"],
                    "Severity": a["severity"],
                    "Product": a["product_name"],
                    "Facility": a["location"],
                    "Current Stock": a["current_stock"],
                    "Safety Threshold": a["threshold"],
                    "Message": a["message"],
                    "Triggered At": a["created_at"],
                }
                for a in active_alerts
            ])
            st.dataframe(alert_df, use_container_width=True, hide_index=True)
