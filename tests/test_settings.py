"""
Unit tests for Persistent System Settings service and database storage.
"""

import pytest
from omnix.core.exceptions import BusinessRuleViolationException
from omnix.db.models.setting import SystemSetting
from omnix.db.session import SessionLocal
from omnix.services.settings_service import (
    get_all_settings,
    get_setting_value,
    set_setting_value,
)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    # Cleanup test settings if any created
    session.query(SystemSetting).filter(
        SystemSetting.key.in_(["test_key", "custom_threshold"])
    ).delete()
    session.commit()
    session.close()


def test_get_setting_default_fallback(db):
    val = get_setting_value(db, "max_auto_approval_limit")
    assert isinstance(val, (float, int))
    assert val > 0


def test_set_and_get_setting_persistence(db):
    set_setting_value(db, "custom_threshold", "12345.00", category="testing")
    retrieved = get_setting_value(db, "custom_threshold")
    assert retrieved == "12345.00"

    # Update value
    set_setting_value(db, "custom_threshold", "54321.00")
    updated = get_setting_value(db, "custom_threshold")
    assert updated == "54321.00"


def test_setting_validation_rejects_negative_spending_limit(db):
    with pytest.raises(BusinessRuleViolationException):
        set_setting_value(db, "max_auto_approval_limit", -500.0)


def test_setting_validation_rejects_non_numeric_spending_limit(db):
    with pytest.raises(BusinessRuleViolationException):
        set_setting_value(db, "max_auto_approval_limit", "not_a_number")


def test_get_all_settings_contains_core_keys(db):
    all_settings = get_all_settings(db)
    assert "max_auto_approval_limit" in all_settings
    assert "high_value_threshold" in all_settings
    assert "low_stock_threshold" in all_settings
    assert "safety_stock_threshold" in all_settings
    assert "stockout_risk_threshold" in all_settings
