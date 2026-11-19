"""
Overview page for OMNIX Agent.
Connected to live backend services, real database metrics, and automated inventory audit scan.
"""

import pandas as pd
import streamlit as st
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_kpi_card, render_page_header


def render_overview_page():
    """Render the operations overview dashboard using real backend data."""
    # 1. Page Header with Interactive Inventory Scan Action
    scan_triggered = render_page_header(
        title="Operations Overview",
        subtitle="Real-time multi-agent business monitoring across inventory, suppliers, and procurement",
        action_label="Run Inventory Audit Scan",
    )

    if scan_triggered:
        with st.spinner("Executing multi-agent inventory scan across warehouses..."):
            res = BackendClient.trigger_inventory_scan()
            new_alerts = BackendClient.scan_inventory_alerts()
            alert_msg = f" Generated {len(new_alerts)} persistent alert(s)." if new_alerts else ""
            if res["new_recommendations"] > 0:
                st.toast(
                    f"Scan complete: Found {res['scanned_items']} deficit items. Generated {res['new_recommendations']} replenishment recommendations!{alert_msg}",
                    icon="✅",
                )
            else:
                st.toast(
                    f"Scan complete: Found {res['scanned_items']} low-stock items. Recommendations up-to-date.{alert_msg}",
                    icon="ℹ️",
                )
            st.rerun()

    # 2. Fetch Live Dashboard Metrics
    kpis = BackendClient.get_dashboard_kpis()

    # 3. KPI Cards Row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card("Total Products", kpis["total_products"], "Active catalog SKUs", "positive")
    with k2:
        render_kpi_card("Total Inventory Value", kpis["inventory_val"], "Live asset valuation", "positive")
    with k3:
        render_kpi_card("Low-Stock SKUs", kpis["low_stock_count"], "Below safety threshold", "warning")
    with k4:
        render_kpi_card("Out of Stock", kpis["out_of_stock_count"], "Depleted stock positions", "negative")
    with k5:
        render_kpi_card("Pending Approvals", kpis["pending_approvals"], "Requires authorization", "warning")

    # 4. Active Persistent Alerts (if any)
    active_alerts = BackendClient.get_active_alerts(limit=5)
    if active_alerts:
        st.markdown("""
        <div class="omnix-panel" style="border-left: 4px solid #D97706;">
            <div class="omnix-panel-title">
                <span>⚠️ Active Inventory Alerts & Warnings</span>
                <span style="font-size: 0.8rem; color: #D97706; font-weight: 600;">Requires Attention</span>
            </div>
        """, unsafe_allow_html=True)
        for alert in active_alerts:
            acol1, acol2 = st.columns([4, 1])
            with acol1:
                badge = "🚨 CRITICAL" if alert["severity"] == "CRITICAL" else "⚠️ WARNING"
                st.markdown(f"**{badge}**: **{alert['title']}** — {alert['message']}")
            with acol2:
                if st.button("Resolve", key=f"res_alert_{alert['id']}", use_container_width=True):
                    BackendClient.resolve_alert(alert["id"], resolved_by="Operations Manager")
                    st.toast(f"Alert #{alert['id']} marked as resolved.", icon="✅")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 5. Main Section: Real Inventory Positions & Pending POs
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("""
        <div class="omnix-panel">
            <div class="omnix-panel-title">
                <span>Current Stock Levels & Deficit Status</span>
                <span style="font-size: 0.8rem; color: #64748B;">Live Warehouse Records</span>
            </div>
        """, unsafe_allow_html=True)

        inv_data = BackendClient.get_inventory_table()
        if inv_data:
            inv_df = pd.DataFrame(inv_data)
            st.dataframe(
                inv_df[["sku", "name", "location", "stock", "min_threshold", "unit_cost", "status"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "sku": "SKU",
                    "name": "Product Name",
                    "location": "Facility",
                    "stock": "On Hand",
                    "min_threshold": "Safety Min",
                    "unit_cost": "Unit Cost",
                    "status": "Health Status",
                },
            )
        else:
            st.info("No inventory records found. Please seed the database.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="omnix-panel">
            <div class="omnix-panel-title">
                <span>Active Purchase Orders</span>
                <span style="font-size: 0.8rem; color: #64748B;">Audit Gate</span>
            </div>
        """, unsafe_allow_html=True)

        po_data = BackendClient.get_purchase_orders_table()
        if po_data:
            for po in po_data[:4]:
                badge_color = "#FEF3C7" if po["status"] == "PENDING_APPROVAL" else "#DEF7EC"
                text_color = "#92400E" if po["status"] == "PENDING_APPROVAL" else "#03543F"
                st.markdown(f"""
                <div style="border-bottom: 1px solid #F1F5F9; padding: 0.75rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #0F172A; font-size: 0.9rem;">{po["po_number"]}</strong>
                        <span style="background: {badge_color}; color: {text_color}; padding: 0.15rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">
                            {po["status"]}
                        </span>
                    </div>
                    <div style="color: #64748B; font-size: 0.825rem; margin-top: 0.2rem;">{po["supplier"]} &bull; {po["total_amount"]}</div>
                    <div style="color: #475569; font-size: 0.8rem; margin-top: 0.2rem;">{po["items"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No purchase orders recorded yet.")
        st.markdown("</div>", unsafe_allow_html=True)
