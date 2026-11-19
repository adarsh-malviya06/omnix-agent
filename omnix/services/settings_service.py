"""
System Settings Service.
Provides persistent configuration stored in the database with validation,
type casting, and fallback to application environment settings.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from omnix.core.config import get_settings
from omnix.core.exceptions import BusinessRuleViolationException
from omnix.db.models.setting import SystemSetting

DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "max_auto_approval_limit": {
        "value": "75000.00",
        "type": float,
        "category": "governance",
        "description": "Maximum purchase order value (INR) eligible for automated single-tier approval.",
    },
    "high_value_threshold": {
        "value": "400000.00",
        "type": float,
        "category": "governance",
        "description": "High-value purchase threshold (INR) requiring multi-level management sign-off.",
    },
    "low_stock_threshold": {
        "value": "20",
        "type": int,
        "category": "inventory",
        "description": "Default safety buffer units added to reorder point calculations.",
    },
    "safety_stock_threshold": {
        "value": "14",
        "type": int,
        "category": "inventory",
        "description": "Standard safety stock coverage target in days of average demand.",
    },
    "stockout_risk_threshold": {
        "value": "7",
        "type": int,
        "category": "inventory",
        "description": "Stockout risk window in days: products depleting within this window are flagged HIGH_RISK.",
    },
}


def get_setting_value(db: Session, key: str, default: Optional[Any] = None) -> Any:
    """
    Retrieve a persistent setting by key, cast to its registered type.
    Falls back to environment setting or DEFAULT_CONFIG if not yet stored in DB.
    """
    row = db.query(SystemSetting).filter_by(key=key).first()
    spec = DEFAULT_CONFIG.get(key, {})
    cast_type = spec.get("type", str)

    if row is not None:
        try:
            return cast_type(row.value)
        except (ValueError, TypeError):
            return row.value

    # Check BaseSettings from environment
    app_settings = get_settings()
    if hasattr(app_settings, key):
        return getattr(app_settings, key)

    if key in DEFAULT_CONFIG:
        return cast_type(DEFAULT_CONFIG[key]["value"])

    return default


def set_setting_value(
    db: Session, key: str, value: Any, category: Optional[str] = None, description: Optional[str] = None
) -> SystemSetting:
    """
    Persist or update a setting in the database with input validation.
    """
    str_val = str(value).strip()

    # Input validation
    if key in ["max_auto_approval_limit", "high_value_threshold"]:
        try:
            num = float(str_val)
            if num < 0:
                raise BusinessRuleViolationException(f"Setting '{key}' cannot be negative.")
        except ValueError:
            raise BusinessRuleViolationException(f"Setting '{key}' must be a valid numeric amount.")

    elif key in ["low_stock_threshold", "safety_stock_threshold", "stockout_risk_threshold"]:
        try:
            num = int(float(str_val))
            if num < 0:
                raise BusinessRuleViolationException(f"Setting '{key}' cannot be negative.")
            str_val = str(num)
        except ValueError:
            raise BusinessRuleViolationException(f"Setting '{key}' must be a valid integer.")

    spec = DEFAULT_CONFIG.get(key, {})
    cat = category or spec.get("category", "governance")
    desc = description or spec.get("description")

    row = db.query(SystemSetting).filter_by(key=key).first()
    if row:
        row.value = str_val
        if category:
            row.category = cat
        if description:
            row.description = desc
    else:
        row = SystemSetting(key=key, value=str_val, category=cat, description=desc)
        db.add(row)

    db.commit()
    db.refresh(row)
    return row


def get_all_settings(db: Session) -> Dict[str, Any]:
    """
    Retrieve all configuration settings (database-persisted + defaults).
    """
    result = {}
    for key, spec in DEFAULT_CONFIG.items():
        result[key] = get_setting_value(db, key)

    # Include any additional arbitrary keys in DB
    extra_rows = db.query(SystemSetting).all()
    for r in extra_rows:
        if r.key not in result:
            result[r.key] = r.value

    return result
