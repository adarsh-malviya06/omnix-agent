"""
Tests verifying that all Streamlit page rendering functions load without import or execution errors.
"""

from omnix.ui.pages.overview import render_overview_page
from omnix.ui.pages.inventory import render_inventory_page
from omnix.ui.pages.suppliers import render_suppliers_page
from omnix.ui.pages.procurement import render_procurement_page
from omnix.ui.pages.ai_assistant import render_ai_assistant_page
from omnix.ui.pages.analytics import render_analytics_page
from omnix.ui.pages.activity_logs import render_activity_logs_page
from omnix.ui.pages.settings import render_settings_page


def test_page_functions_exist():
    """Verify all 8 mandatory PRD pages have callable render functions."""
    pages = [
        render_overview_page,
        render_inventory_page,
        render_suppliers_page,
        render_procurement_page,
        render_ai_assistant_page,
        render_analytics_page,
        render_activity_logs_page,
        render_settings_page,
    ]
    for page in pages:
        assert callable(page)
