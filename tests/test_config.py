"""
Unit tests for application settings and configuration.
"""

from omnix.core.config import Settings, get_settings


def test_settings_initialization():
    """Verify settings defaults load safely."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "OMNIX Agent"
    assert settings.api_port == 8000
    assert settings.streamlit_port == 8501
    # Currency defaults must be INR
    assert settings.default_currency == "INR"
    assert settings.max_auto_approval_limit == 75_000.00
    assert settings.high_value_threshold == 4_00_000.00
