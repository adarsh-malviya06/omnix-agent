"""
Unit tests for Persistent Inventory Alerts service, deduplication, and resolution.
"""

import pytest
from omnix.db.models.alert import InventoryAlert
from omnix.db.models.inventory import Inventory
from omnix.db.session import SessionLocal
from omnix.services.alert_service import (
    get_active_alerts,
    get_all_alerts,
    resolve_alert,
    scan_and_generate_inventory_alerts,
)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    # Cleanup any alerts created during test
    session.query(InventoryAlert).delete()
    session.commit()
    session.close()


def test_scan_generates_alerts_for_deficit_items(db):
    alerts = scan_and_generate_inventory_alerts(db)
    # Check that any generated alert has valid fields
    for a in alerts:
        assert a.id is not None
        assert a.alert_type in ["LOW_STOCK", "OUT_OF_STOCK", "HIGH_STOCKOUT_RISK"]
        assert a.severity in ["WARNING", "CRITICAL"]
        assert not a.is_resolved


def test_alert_deduplication_prevents_duplicate_active_alerts(db):
    # First scan
    scan1 = scan_and_generate_inventory_alerts(db)
    count1 = len(scan1)

    # Second scan immediately after
    scan2 = scan_and_generate_inventory_alerts(db)
    count2 = len(scan2)

    # Should not duplicate active unresolved alerts
    assert count2 == 0


def test_resolve_alert_marks_resolved_with_timestamp(db):
    scan_and_generate_inventory_alerts(db)
    active = get_active_alerts(db)
    if not active:
        # Create a mock alert if inventory happened to be fully healthy
        inv = db.query(Inventory).first()
        alert = InventoryAlert(
            product_id=inv.product_id,
            location_id=inv.location_id,
            alert_type="LOW_STOCK",
            severity="WARNING",
            title="Test Alert",
            message="Test Message",
            current_stock=5,
            threshold_value=20,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        target_id = alert.id
    else:
        target_id = active[0].id

    # Resolve alert
    resolved = resolve_alert(db, alert_id=target_id, resolved_by="Test Admin", notes="Restocked")
    assert resolved.is_resolved is True
    assert resolved.resolved_at is not None
    assert resolved.resolved_by == "Test Admin"

    # Verify excluded from active alerts
    remaining_active = get_active_alerts(db)
    assert all(a.id != target_id for a in remaining_active)
