"""
Reusable enterprise UI building blocks for OMNIX Streamlit pages.
"""

from typing import Optional
import streamlit as st


def render_page_header(title: str, subtitle: str, action_label: Optional[str] = None) -> bool:
    """Renders a standard enterprise top-level header with title and subtitle."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"<h1 style='margin-bottom: 0.25rem; font-size: 1.75rem; font-weight: 700; color: #0F172A;'>{title}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #64748B; font-size: 0.95rem; margin-top: 0; margin-bottom: 1.5rem;'>{subtitle}</p>", unsafe_allow_html=True)
    with col2:
        if action_label:
            return st.button(action_label, type="primary", use_container_width=True)
    return False


def render_kpi_card(title: str, value: str, subtext: str = "", trend: str = "neutral"):
    """
    Renders a clean white KPI card matching standard SaaS dashboards.
    """
    trend_color = "#64748B"
    if trend == "positive":
        trend_color = "#059669"
    elif trend == "negative":
        trend_color = "#DC2626"
    elif trend == "warning":
        trend_color = "#D97706"

    html = f"""
    <div class="omnix-kpi-card">
        <div class="omnix-kpi-title">{title}</div>
        <div class="omnix-kpi-value">{value}</div>
        <div class="omnix-kpi-sub" style="color: {trend_color};">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Returns HTML for a standardized colored status badge."""
    s = status.upper()
    if s in ["IN_STOCK", "ACTIVE", "APPROVED", "COMPLETED", "ON_TIME"]:
        return f'<span class="badge-success">{status.replace("_", " ")}</span>'
    elif s in ["LOW_STOCK", "PENDING", "PENDING_APPROVAL", "REVIEW_REQUIRED"]:
        return f'<span class="badge-warning">{status.replace("_", " ")}</span>'
    elif s in ["OUT_OF_STOCK", "REJECTED", "FAILED", "HIGH_RISK"]:
        return f'<span class="badge-danger">{status.replace("_", " ")}</span>'
    else:
        return f'<span class="badge-info">{status.replace("_", " ")}</span>'
