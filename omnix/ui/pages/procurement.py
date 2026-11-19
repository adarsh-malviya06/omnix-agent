"""
Procurement and Purchase Orders page with Human-in-the-Loop approval workflows,
recommendation review, and purchase order lifecycle management.
"""

import pandas as pd
import streamlit as st
from omnix.core.currency import format_inr
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_kpi_card, render_page_header


def render_procurement_page():
    """Render Procurement Orders & Human-in-the-Loop Approval screen."""
    render_page_header(
        title="Procurement & Purchase Orders",
        subtitle="Review AI replenishment recommendations, compare quotes, and execute human approvals",
    )

    # 1. Fetch live tables
    recs = BackendClient.get_recommendations_table()
    orders = BackendClient.get_purchase_orders_table()

    pending_recs = [r for r in recs if r["status"] == "PENDING"]
    pending_orders = [o for o in orders if o["status"] == "PENDING_APPROVAL"]
    approved_orders = [o for o in orders if o["status"] in ["APPROVED", "COMPLETED", "ORDERED"]]

    total_pending_val = sum(r["raw_cost"] for r in pending_recs)

    # 2. Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Pending Recommendations", f"{len(pending_recs)} Action Items", f"{format_inr(total_pending_val)} total", "warning")
    with c2:
        render_kpi_card("Active Purchase Orders", f"{len(orders)} Orders", "In pipeline")
    with c3:
        render_kpi_card("Approved Orders", f"{len(approved_orders)} Orders", "Authorized", "positive")
    with c4:
        render_kpi_card("Approval Gate", "Enforced", "Mandatory human sign-off")

    # 3. Human Approval Gate: Actionable Pending Recommendations
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">⭐ Pending Procurement Recommendations (Human Authorization Gate)</div>', unsafe_allow_html=True)

    if pending_recs:
        st.write("The following items were identified by the multi-agent system as requiring replenishment. Review and decide:")

        for rec in pending_recs:
            with st.expander(f"📦 Recommendation #{rec['id']}: {rec['product_name']} ({rec['product_sku']}) — {rec['estimated_cost']}", expanded=True):
                col_det1, col_det2 = st.columns([2, 1])
                with col_det1:
                    st.markdown(f"**Facility:** {rec['location_name']}")
                    st.markdown(f"**Current Stock:** `{rec['current_stock']} units` (Safety Reorder Point: `{rec['reorder_point']} units`)")
                    st.markdown(f"**Suggested Order:** **{rec['suggested_quantity']} units** via **{rec['suggested_supplier']}**")
                    st.markdown(f"**Estimated Order Value:** **{rec['estimated_cost']}**")
                    st.info(f"💡 **Agent Reasoning:** {rec['reasoning']}")

                with col_det2:
                    st.markdown("##### Manager Decision")
                    decision_comment = st.text_input(
                        "Authorization Comments",
                        placeholder="e.g. Approved for warehouse replenishment",
                        key=f"comment_{rec['id']}",
                    )

                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✅ Approve", key=f"appr_{rec['id']}", type="primary", use_container_width=True):
                            res = BackendClient.approve_recommendation(
                                recommendation_id=rec["id"], comments=decision_comment
                            )
                            if res["success"]:
                                st.success(res["message"])
                                st.rerun()
                            else:
                                st.error(res.get("error", "Approval failed."))

                    with btn_col2:
                        if st.button("❌ Reject", key=f"rej_{rec['id']}", use_container_width=True):
                            res = BackendClient.reject_recommendation(
                                recommendation_id=rec["id"], reason=decision_comment or "Rejected by manager"
                            )
                            if res["success"]:
                                st.warning(res["message"])
                                st.rerun()
                            else:
                                st.error(res.get("error", "Rejection failed."))
    else:
        st.success("✅ No pending purchase recommendations requiring immediate authorization. All inventory positions are compliant.")

    st.markdown("</div>", unsafe_allow_html=True)

    # 4. Master Purchase Orders Registry
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">Purchase Order Master Registry</div>', unsafe_allow_html=True)

    if orders:
        orders_df = pd.DataFrame(orders)
        st.dataframe(
            orders_df[["po_number", "supplier", "items", "destination", "total_amount", "date_created", "status"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "po_number": "PO Number",
                "supplier": "Vendor Name",
                "items": "Line Items",
                "destination": "Destination Facility",
                "total_amount": "Total Amount (INR)",
                "date_created": "Date Issued",
                "status": "PO Status",
            },
        )
    else:
        st.info("No purchase orders found.")

    st.markdown("</div>", unsafe_allow_html=True)
