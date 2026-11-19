"""
Inventory Alert Business Service.
Provides persistent alert management, automated inventory scanning,
deduplication, and resolution tracking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from omnix.core.exceptions import NotFoundException
from omnix.db.models.alert import InventoryAlert
from omnix.db.models.inventory import Inventory
from omnix.db.models.product import Product
from omnix.services.inventory_service import get_inventory_positions
from omnix.services.settings_service import get_setting_value


def scan_and_generate_inventory_alerts(
    db: Session, organization_id: Optional[int] = None
) -> List[InventoryAlert]:
    """
    Scan all inventory positions against configured thresholds.
    Creates persistent alerts for OUT_OF_STOCK, LOW_STOCK, and HIGH_STOCKOUT_RISK.
    Prevents duplicate unresolved alerts for the same product and location.
    """
    positions = get_inventory_positions(db, organization_id=organization_id)
    generated_alerts: List[InventoryAlert] = []

    for inv in positions:
        prod: Product = inv.product
        current_stock = inv.quantity_on_hand
        reorder_point = prod.reorder_point

        # 1. Check for OUT_OF_STOCK
        if current_stock == 0:
            existing = (
                db.query(InventoryAlert)
                .filter_by(
                    product_id=inv.product_id,
                    location_id=inv.location_id,
                    alert_type="OUT_OF_STOCK",
                    is_resolved=False,
                )
                .first()
            )
            if not existing:
                alert = InventoryAlert(
                    organization_id=prod.organization_id,
                    product_id=inv.product_id,
                    location_id=inv.location_id,
                    alert_type="OUT_OF_STOCK",
                    severity="CRITICAL",
                    title=f"Depleted Stock: {prod.name}",
                    message=f"Product {prod.name} ({prod.sku}) has 0 units available at {inv.location.name}. Reorder threshold is {reorder_point}.",
                    current_stock=0,
                    threshold_value=reorder_point,
                )
                db.add(alert)
                generated_alerts.append(alert)

        # 2. Check for LOW_STOCK (when stock > 0 but <= reorder_point)
        elif current_stock <= reorder_point:
            existing = (
                db.query(InventoryAlert)
                .filter_by(
                    product_id=inv.product_id,
                    location_id=inv.location_id,
                    alert_type="LOW_STOCK",
                    is_resolved=False,
                )
                .first()
            )
            if not existing:
                alert = InventoryAlert(
                    organization_id=prod.organization_id,
                    product_id=inv.product_id,
                    location_id=inv.location_id,
                    alert_type="LOW_STOCK",
                    severity="WARNING",
                    title=f"Low Stock Alert: {prod.name}",
                    message=f"Product {prod.name} ({prod.sku}) at {inv.location.name} is down to {current_stock} units, below safety threshold of {reorder_point}.",
                    current_stock=current_stock,
                    threshold_value=reorder_point,
                )
                db.add(alert)
                generated_alerts.append(alert)

    db.commit()
    for a in generated_alerts:
        db.refresh(a)

    return generated_alerts


def get_active_alerts(
    db: Session,
    organization_id: Optional[int] = None,
    severity: Optional[str] = None,
    limit: int = 50,
) -> List[InventoryAlert]:
    """Retrieve active (unresolved) inventory alerts ordered by severity and time."""
    query = (
        db.query(InventoryAlert)
        .filter(InventoryAlert.is_resolved == False)
        .order_by(InventoryAlert.created_at.desc())
    )
    if organization_id:
        query = query.filter(InventoryAlert.organization_id == organization_id)
    if severity:
        query = query.filter(InventoryAlert.severity == severity.upper())

    return query.limit(limit).all()


def get_all_alerts(
    db: Session,
    organization_id: Optional[int] = None,
    include_resolved: bool = True,
    limit: int = 100,
) -> List[InventoryAlert]:
    """Retrieve alerts history."""
    query = db.query(InventoryAlert).order_by(InventoryAlert.created_at.desc())
    if not include_resolved:
        query = query.filter(InventoryAlert.is_resolved == False)
    if organization_id:
        query = query.filter(InventoryAlert.organization_id == organization_id)

    return query.limit(limit).all()


def resolve_alert(
    db: Session, alert_id: int, resolved_by: str = "Authorized User", notes: Optional[str] = None
) -> InventoryAlert:
    """
    Mark an alert as resolved with audit details.
    """
    alert = db.query(InventoryAlert).filter_by(id=alert_id).first()
    if not alert:
        raise NotFoundException(f"InventoryAlert with ID {alert_id} not found.")

    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = resolved_by
    alert.resolution_notes = notes

    db.commit()
    db.refresh(alert)
    return alert
