"""
Analytics and Demand Forecasting visualization page.
Backed entirely by live database records and Scikit-Learn predictive modeling.
"""

import pandas as pd
import streamlit as st
from omnix.core.currency import format_inr
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_kpi_card, render_page_header


def render_analytics_page():
    """Render the Analytics & Demand Trends view using live database metrics."""
    render_page_header(
        title="Business Analytics & Forecasts",
        subtitle="Historical demand patterns, ML predictive models, and procurement spending distribution",
    )

    # 1. Fetch real analytics KPIs
    kpis = BackendClient.get_analytics_kpis()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total Inventory Value", kpis["total_inventory_value"], "Live asset valuation", "positive")
    with c2:
        render_kpi_card("Procurement Spend", kpis["total_procurement_spend"], "Approved & issued POs")
    with c3:
        render_kpi_card("Active Catalog SKUs", str(kpis["total_products"]), "Active trade catalog")
    with c4:
        render_kpi_card("Supplier Network", str(kpis["total_suppliers"]), "Approved active vendors")

    # 2. Stock Health Distribution
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">Inventory Health Breakdown</div>', unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    with h1:
        st.metric("Healthy Stock Positions", f"{kpis['healthy_count']} SKUs")
    with h2:
        st.metric("Low-Stock Alerts", f"{kpis['low_stock_count']} SKUs", delta="-Deficit", delta_color="inverse")
    with h3:
        st.metric("Out of Stock Depletions", f"{kpis['out_of_stock_count']} SKUs", delta="-Critical", delta_color="inverse")
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. Product Demand History & ML Predictive Modeling
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="omnix-panel-title">Product Demand Trends & Machine Learning Forecast</div>',
        unsafe_allow_html=True,
    )

    inv_items = BackendClient.get_inventory_table()
    if inv_items:
        # Group products uniquely by ID
        unique_prods = {}
        for itm in inv_items:
            key = f"{itm['name']} ({itm['sku']}) - {itm['location']}"
            unique_prods[key] = (itm["id"], itm["name"], itm["sku"])

        selected_label = st.selectbox(
            "Select SKU to Inspect Demand History & ML Projections",
            list(unique_prods.keys()),
            index=0,
        )
        selected_prod_id = unique_prods[selected_label][0]

        # Fetch live analytics and ML forecast
        prod_analytics = BackendClient.get_product_demand_analytics(selected_prod_id)

        if prod_analytics["has_data"]:
            history = prod_analytics["history"]
            hist_df = pd.DataFrame(history)

            f1, f2 = st.columns([3, 1])
            with f1:
                hist_chart = hist_df.copy()
                hist_chart["date"] = pd.to_datetime(hist_chart["date"]).dt.strftime("%b %d")
                hist_chart = hist_chart.set_index("date")
                st.line_chart(hist_chart["demand"], color="#2563EB")
                st.caption(f"Historical Daily Consumption (from live DemandHistory). {prod_analytics['notes']}")

            with f2:
                fc = prod_analytics.get("forecast") or {}
                if "error" in fc:
                    st.warning(f"Forecasting notice: {fc['error']}")
                else:
                    st.markdown("**ML Model Pipeline:**")
                    st.write(f"🏷️ `{fc.get('model_name', 'Ridge Regression')}`")
                    st.write(f"📏 **Holdout MAE:** `{fc.get('mae', 'N/A')}`")
                    st.write(f"📐 **Holdout RMSE:** `{fc.get('rmse', 'N/A')}`")
                    st.write(f"⚠️ **Risk Level:** `{fc.get('risk_level', 'N/A')}`")
                    if fc.get("days_until_stockout"):
                        st.write(f"⏳ **Days to Stockout:** `{fc['days_until_stockout']} days`")
                    st.write(f"📦 **14-Day Forecast:** `{fc.get('total_forecast', 0.0)} units`")

            # Future 14-day projection table
            if fc and "daily_forecast" in fc and fc["daily_forecast"]:
                with st.expander("📅 View 14-Day Forward Projections", expanded=False):
                    proj_df = pd.DataFrame(fc["daily_forecast"])
                    proj_df.columns = ["Projected Date", "Forecasted Demand (Units)"]
                    st.dataframe(proj_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                f"ℹ️ {prod_analytics['notes']} (Insufficient historical records to train ML regression models)."
            )
    else:
        st.info("No active catalog items available.")

    st.markdown("</div>", unsafe_allow_html=True)

    # 4. Spend Distribution by Supplier
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">Procurement Spend by Vendor</div>', unsafe_allow_html=True)

    supplier_spend = BackendClient.get_spend_by_supplier()
    if supplier_spend:
        spend_df = pd.DataFrame(supplier_spend)
        st.dataframe(
            spend_df[["supplier", "formatted_spend"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "supplier": "Vendor Name",
                "formatted_spend": "Total Spend (INR)",
            },
        )
    else:
        st.info("No supplier purchase transactions recorded yet.")

    st.markdown("</div>", unsafe_allow_html=True)
