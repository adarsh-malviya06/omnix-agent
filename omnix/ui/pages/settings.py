"""
System Settings and operational policy configurations with persistent database storage.
"""

import streamlit as st
from omnix.core.config import get_settings
from omnix.core.currency import CURRENCY_CODE, CURRENCY_SYMBOL
from omnix.ui.backend_client import BackendClient
from omnix.ui.components import render_page_header


def render_settings_page():
    """Render the Settings and Governance parameters screen."""
    render_page_header(
        title="Settings & Governance",
        subtitle="Configure procurement policies, spending thresholds, model endpoints, and database connection",
    )

    app_settings = get_settings()
    stored_settings = BackendClient.get_system_settings()

    # Form for persistent settings
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">Procurement Policy & Approval Thresholds</div>', unsafe_allow_html=True)

    with st.form("settings_form"):
        c1, c2 = st.columns(2)
        with c1:
            auto_val = st.number_input(
                f"Auto-Validation Limit ({CURRENCY_SYMBOL})",
                min_value=0.0,
                max_value=50_00_000.0,
                value=float(stored_settings.get("max_auto_approval_limit", app_settings.max_auto_approval_limit)),
                step=5000.0,
                help=f"Orders below this amount ({CURRENCY_CODE}) qualify for streamlined review.",
            )
        with c2:
            high_val = st.number_input(
                f"High-Value Order Threshold ({CURRENCY_SYMBOL})",
                min_value=10_000.0,
                max_value=1_00_00_000.0,
                value=float(stored_settings.get("high_value_threshold", app_settings.high_value_threshold)),
                step=25_000.0,
                help=f"Orders above this amount ({CURRENCY_CODE}) strictly require multi-level human authorization.",
            )

        st.markdown('<div class="omnix-panel-title" style="margin-top: 1rem;">Inventory Monitoring & Safety Buffers</div>', unsafe_allow_html=True)
        i1, i2, i3 = st.columns(3)
        with i1:
            low_stock_buf = st.number_input(
                "Safety Buffer Units (Reorder Buffer)",
                min_value=0,
                max_value=500,
                value=int(stored_settings.get("low_stock_threshold", 20)),
                step=5,
                help="Extra units added as a safety cushion when evaluating low-stock warnings.",
            )
        with i2:
            safety_days = st.number_input(
                "Safety Stock Coverage (Days)",
                min_value=1,
                max_value=60,
                value=int(stored_settings.get("safety_stock_threshold", 14)),
                step=1,
                help="Desired days of forward demand coverage to retain in warehouse stock.",
            )
        with i3:
            stockout_days = st.number_input(
                "Stockout Risk Window (Days)",
                min_value=1,
                max_value=30,
                value=int(stored_settings.get("stockout_risk_threshold", 7)),
                step=1,
                help="Positions predicted to deplete within this number of days are flagged as HIGH RISK.",
            )

        submitted = st.form_submit_button("Save Policy Settings", type="primary")
        if submitted:
            try:
                BackendClient.save_system_settings({
                    "max_auto_approval_limit": auto_val,
                    "high_value_threshold": high_val,
                    "low_stock_threshold": low_stock_buf,
                    "safety_stock_threshold": safety_days,
                    "stockout_risk_threshold": stockout_days,
                })
                st.success("✅ Governance policies and thresholds successfully saved to database. Settings will persist across restarts.")
            except Exception as e:
                st.error(f"Error saving settings: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Runtime and System Info
    st.markdown('<div class="omnix-panel">', unsafe_allow_html=True)
    st.markdown('<div class="omnix-panel-title">System & AI Model Runtime</div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.text_input("Active LLM Model", value=app_settings.llm_model, disabled=True)
        st.text_input("Environment", value=app_settings.environment, disabled=True)
    with c4:
        st.text_input("Database URI", value=app_settings.database_url, disabled=True)
        st.text_input("Vector Knowledge Path", value=app_settings.chroma_persist_directory, disabled=True)

    st.markdown('<div class="omnix-panel-title" style="margin-top: 1rem;">Currency Configuration</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.text_input("Active Currency Code", value=app_settings.default_currency, disabled=True)
    with cc2:
        st.text_input("Currency Symbol", value=CURRENCY_SYMBOL, disabled=True)

    st.markdown("</div>", unsafe_allow_html=True)
