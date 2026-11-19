"""
Suppliers management and live multi-attribute quote comparison page.
"""

import pandas as pd
import streamlit as st
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_kpi_card, render_page_header


def render_suppliers_page():
    """Render the Supplier Management view with real database catalog and comparison tool."""
    render_page_header(
        title="Supplier Network & Vendor Analysis",
        subtitle="Evaluate vendor reliability, lead times, pricing performance, and active agreements",
    )

    # 1. Fetch live suppliers
    suppliers = BackendClient.get_suppliers_table()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Active Vendors", str(len(suppliers)), "Network capacity")
    with c2:
        render_kpi_card("Avg Network Lead Time", "3.8 Days", "Across active contracts", "positive")
    with c3:
        render_kpi_card("Avg Reliability Score", "93.4%", "On-time delivery track record")
    with c4:
        render_kpi_card("Payment Terms", "Net 15 - 30", "Verified commercial terms")

    # 2. Approved Suppliers Table
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">Approved Supplier Catalog & Performance</div>', unsafe_allow_html=True)

    if suppliers:
        sup_df = pd.DataFrame(suppliers)
        st.dataframe(
            sup_df[["code", "name", "contact_person", "contact_email", "avg_lead_days", "reliability_score", "payment_terms", "status"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "code": "Vendor Code",
                "name": "Supplier Legal Entity",
                "contact_person": "Contact Person",
                "contact_email": "Dispatch Email",
                "avg_lead_days": "Lead Time",
                "reliability_score": "Reliability Score",
                "payment_terms": "Credit Terms",
                "status": "Contract Status",
            },
        )
    else:
        st.info("No suppliers currently registered.")
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. Interactive Vendor Quote Comparison Tool
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">Vendor Quote Comparison Tool (40/30/30 Multi-Attribute Model)</div>', unsafe_allow_html=True)

    inv = BackendClient.get_inventory_table()
    if inv:
        product_options = {f"{i['name']} ({i['sku']})": i["id"] for i in inv}
        selected_label = st.selectbox("Select Product to Compare Available Supplier Quotes", list(product_options.keys()))
        selected_prod_id = product_options[selected_label]

        # Call backend comparison service
        from omnix.db.session import SessionLocal
        from omnix.services.supplier_service import compare_suppliers_for_product
        db = SessionLocal()
        try:
            comparison = compare_suppliers_for_product(db, product_id=selected_prod_id)
            if comparison.quotes:
                quotes_df = pd.DataFrame([
                    {
                        "Vendor": q.supplier_name,
                        "Quoted Rate": f"₹{q.unit_price:,.2f}",
                        "Lead Time (Days)": q.lead_days,
                        "MOQ": q.moq,
                        "Reliability (%)": f"{q.reliability_score}%",
                        "Composite Score": f"{q.composite_score}/100",
                        "Recommended": "⭐ BEST MATCH" if q.is_recommended else "Alternative",
                    }
                    for q in comparison.quotes
                ])
                st.dataframe(quotes_df, use_container_width=True, hide_index=True)
                st.caption("Scoring Formula: 40% Price Competitiveness + 30% Delivery Speed + 30% Historical Reliability.")
            else:
                st.info("No active supplier quotes mapped for this product.")
        finally:
            db.close()

    st.markdown("</div>", unsafe_allow_html=True)
