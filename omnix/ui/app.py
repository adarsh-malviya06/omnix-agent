"""
OMNIX Agent - Streamlit Application Entrypoint.
Orchestrates sidebar navigation and page routing.
"""
import textwrap
import streamlit as st
from omnix.ui.styles import CUSTOM_CSS
from omnix.ui.pages.overview import render_overview_page
from omnix.ui.pages.inventory import render_inventory_page
from omnix.ui.pages.suppliers import render_suppliers_page
from omnix.ui.pages.procurement import render_procurement_page
from omnix.ui.pages.ai_assistant import render_ai_assistant_page
from omnix.ui.pages.analytics import render_analytics_page
from omnix.ui.pages.activity_logs import render_activity_logs_page
from omnix.ui.pages.settings import render_settings_page

# Page Configuration
st.set_page_config(
    page_title="OMNIX Agent | Procurement & Inventory Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom enterprise CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Inline SVG logo for the OMNIX brand mark

_OMNIX_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 40 40"
     width="38"
     height="38">
    <rect width="40" height="40" rx="10" fill="#2563EB"/>
    <text x="50%" y="54%"
          dominant-baseline="central"
          text-anchor="middle"
          font-family="Arial, sans-serif"
          font-size="17"
          font-weight="800"
          fill="#FFFFFF">OX</text>
</svg>
"""



def main():
    """Main routing and sidebar navigation."""
    with st.sidebar:

        st.html(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 8px 20px 8px;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 16px;
        ">
            {_OMNIX_LOGO_SVG}
            <div>
                <div style="
                    font-size: 20px;
                    font-weight: 750;
                    color: #0F172A;
                    letter-spacing: -0.5px;
                ">OMNIX Agent</div>
                <div style="
                    font-size: 11px;
                    color: #64748B;
                    font-weight: 500;
                ">Operations Intelligence</div>
            </div>
        </div>
        """)



        pages = {
            "Overview": "📊",
            "Inventory": "📦",
            "Suppliers": "🚚",
            "Procurement & Purchase Orders": "📑",
            "AI Assistant": "🤖",
            "Analytics": "📈",
            "Activity Logs": "📝",
            "Settings": "⚙️",
        }

        selection = st.radio(
            "Navigation",
            options=list(pages.keys()),
            format_func=lambda x: f"{pages[x]}  {x}",
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.75rem; color: #94A3B8; line-height: 1.4;">
            <strong>OMNIX Platform v1.0.0</strong><br>
            Enterprise Wholesale & Retail Operations
        </div>
        """, unsafe_allow_html=True)

    # Page dispatch map
    _page_renderers = {
        "Overview": render_overview_page,
        "Inventory": render_inventory_page,
        "Suppliers": render_suppliers_page,
        "Procurement & Purchase Orders": render_procurement_page,
        "AI Assistant": render_ai_assistant_page,
        "Analytics": render_analytics_page,
        "Activity Logs": render_activity_logs_page,
        "Settings": render_settings_page,
    }

    # Route based on navigation selection with error handling
    renderer = _page_renderers.get(selection)
    if renderer:
        try:
            renderer()
        except Exception as exc:
            st.error(f"Error rendering **{selection}** page: {exc}")
            st.exception(exc)
    else:
        st.warning(f"Unknown page: {selection}")


if __name__ == "__main__":
    main()
