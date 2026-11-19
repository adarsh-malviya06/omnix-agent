"""
OMNIX Unified Backend Client.
Provides a clean, typed bridge between the Streamlit presentation layer
and the FastAPI business service layer, supporting both direct service execution
and HTTP client connectivity.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from omnix.agents.orchestrator import MultiAgentOrchestrator
from omnix.core.currency import format_inr
from omnix.db.base import ApprovalAction, AuditEventType, PurchaseOrderStatus, RecommendationStatus
from omnix.db.models import (
    AuditLog,
    DemandHistory,
    Inventory,
    InventoryAlert,
    Location,
    Organization,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Recommendation,
    Supplier,
    SupplierProduct,
    SystemSetting,
    User,
)
from omnix.db.session import SessionLocal
from omnix.ml.forecasting_service import forecast_product_demand, load_demand_series
from omnix.rag.groq_service import GroqRAGService
from omnix.rag.retriever import retrieve_relevant_knowledge
from omnix.services.alert_service import (
    get_active_alerts,
    get_all_alerts,
    resolve_alert,
    scan_and_generate_inventory_alerts,
)
from omnix.services.inventory_service import (
    get_all_products,
    get_inventory_positions,
    get_low_stock_items,
    get_movement_history,
    get_out_of_stock_items,
    get_product_by_id,
    record_inventory_movement,
)
from omnix.services.procurement_service import (
    calculate_reorder_recommendation,
    create_procurement_recommendation,
    create_purchase_order_draft,
    get_dashboard_statistics,
    process_purchase_order_approval,
)
from omnix.services.settings_service import (
    get_all_settings,
    get_setting_value,
    set_setting_value,
)
from omnix.services.supplier_service import (
    compare_suppliers_for_product,
    get_all_suppliers,
    get_supplier_by_id,
    get_supplier_products,
)


class BackendClient:
    """Unified client providing backend services to the UI layer."""

    @staticmethod
    def get_dashboard_kpis() -> Dict[str, Any]:
        """Aggregate real-time business health metrics from database."""
        db: Session = SessionLocal()
        try:
            stats = get_dashboard_statistics(db)
            # Fetch pending recommendations count
            pending_recs = (
                db.query(Recommendation)
                .filter(Recommendation.status == RecommendationStatus.PENDING)
                .count()
            )
            # Fetch high stockout risks count
            low_items = get_low_stock_items(db)
            out_items = get_out_of_stock_items(db)
            risk_count = len(low_items) + len(out_items)

            return {
                "total_products": str(stats.total_products),
                "inventory_val": format_inr(stats.total_inventory_value),
                "low_stock_count": str(stats.low_stock_count),
                "out_of_stock_count": str(stats.out_of_stock_count),
                "stockout_risk_count": str(risk_count),
                "pending_approvals": str(stats.pending_approvals_count),
                "pending_recommendations": str(pending_recs),
                "total_suppliers": str(stats.total_suppliers),
            }
        finally:
            db.close()

    @staticmethod
    def get_inventory_table() -> List[Dict[str, Any]]:
        """Retrieve live inventory items formatted for data table display."""
        db: Session = SessionLocal()
        try:
            positions = get_inventory_positions(db)
            rows = []
            for itm in positions:
                rows.append({
                    "id": itm.id,
                    "sku": itm.product.sku,
                    "name": itm.product.name,
                    "category": itm.product.category,
                    "stock": itm.quantity_on_hand,
                    "reserved": itm.quantity_reserved,
                    "available": itm.quantity_available,
                    "min_threshold": itm.product.reorder_point,
                    "unit_cost": format_inr(itm.last_purchase_cost),
                    "location": itm.location.name,
                    "location_code": itm.location.code,
                    "status": "OUT_OF_STOCK" if itm.is_out_of_stock else ("LOW_STOCK" if itm.is_low_stock else "IN_STOCK"),
                })
            return rows
        finally:
            db.close()

    @staticmethod
    def get_suppliers_table() -> List[Dict[str, Any]]:
        """Retrieve live supplier records."""
        db: Session = SessionLocal()
        try:
            suppliers = get_all_suppliers(db)
            rows = []
            for s in suppliers:
                rows.append({
                    "id": s.id,
                    "code": s.code,
                    "name": s.name,
                    "contact_person": s.contact_person or "Operations Desk",
                    "contact_email": s.contact_email or "orders@" + s.code.lower() + ".in",
                    "contact_phone": s.contact_phone or "+91-9800000000",
                    "reliability_score": f"{s.reliability_score}%",
                    "avg_lead_days": f"{s.avg_lead_days} Days",
                    "payment_terms": s.payment_terms or "Standard",
                    "status": "ACTIVE" if s.is_active else "INACTIVE",
                })
            return rows
        finally:
            db.close()

    @staticmethod
    def get_purchase_orders_table() -> List[Dict[str, Any]]:
        """Retrieve live purchase orders."""
        db: Session = SessionLocal()
        try:
            orders = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()
            rows = []
            for po in orders:
                items_summary = ", ".join(
                    f"{itm.product.name} (×{itm.quantity})" for itm in po.items
                ) or "No line items"
                rows.append({
                    "id": po.id,
                    "po_number": po.po_number,
                    "supplier": po.supplier.name,
                    "supplier_id": po.supplier_id,
                    "items": items_summary,
                    "total_amount": format_inr(po.total_amount),
                    "raw_amount": float(po.total_amount),
                    "date_created": po.created_at.strftime("%Y-%m-%d"),
                    "status": po.status.value.upper(),
                    "destination": po.destination_location.name,
                })
            return rows
        finally:
            db.close()

    @staticmethod
    def get_recommendations_table() -> List[Dict[str, Any]]:
        """Retrieve active AI/rule-generated procurement recommendations."""
        db: Session = SessionLocal()
        try:
            recs = db.query(Recommendation).order_by(Recommendation.created_at.desc()).all()
            rows = []
            for r in recs:
                rows.append({
                    "id": r.id,
                    "product_id": r.product_id,
                    "product_name": r.product.name,
                    "product_sku": r.product.sku,
                    "location_name": r.location.name,
                    "location_id": r.location_id,
                    "suggested_supplier": r.suggested_supplier.name if r.suggested_supplier else "Best Rated Vendor",
                    "suggested_supplier_id": r.suggested_supplier_id,
                    "suggested_quantity": r.suggested_quantity,
                    "current_stock": r.current_stock,
                    "reorder_point": r.reorder_point,
                    "estimated_cost": format_inr(r.estimated_cost),
                    "raw_cost": float(r.estimated_cost),
                    "status": r.status.value.upper(),
                    "reasoning": r.reasoning or "Automated reorder threshold triggered.",
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
                })
            return rows
        finally:
            db.close()

    @staticmethod
    def get_audit_logs_table(limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve system audit logs."""
        db: Session = SessionLocal()
        try:
            logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
            return [
                {
                    "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "actor": l.actor,
                    "event_type": l.event_type.value,
                    "action": l.action,
                    "details": l.details or "N/A",
                }
                for l in logs
            ]
        finally:
            db.close()

    @staticmethod
    def approve_recommendation(
        recommendation_id: int, user_email: str = "admin@agrobulk.in", comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Human-in-the-Loop: Authorize a pending recommendation,
        convert it into an Approved Purchase Order, and record compliance audit log.
        """
        db: Session = SessionLocal()
        try:
            rec = db.query(Recommendation).filter_by(id=recommendation_id).first()
            if not rec:
                return {"success": False, "error": f"Recommendation #{recommendation_id} not found."}

            user = db.query(User).filter_by(email=user_email).first()
            if not user:
                user = db.query(User).first()

            # Create PO from recommendation
            po_count = db.query(PurchaseOrder).count() + 1
            po_number = f"PO-2026-{po_count:04d}"

            supplier_id = rec.suggested_supplier_id
            if not supplier_id:
                # Fallback to first supplier
                sup = db.query(Supplier).filter_by(organization_id=rec.organization_id).first()
                supplier_id = sup.id if sup else 1

            po = PurchaseOrder(
                organization_id=rec.organization_id,
                po_number=po_number,
                supplier_id=supplier_id,
                destination_location_id=rec.location_id,
                status=PurchaseOrderStatus.APPROVED,
                currency="INR",
                total_amount=rec.estimated_cost,
                notes=f"Auto-generated from Approved Recommendation #{rec.id}. Comments: {comments or 'Approved via dashboard'}",
            )
            db.add(po)
            db.flush()

            # Add line item
            poi = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=rec.product_id,
                quantity=rec.suggested_quantity,
                unit_price=rec.estimated_cost / Decimal(str(rec.suggested_quantity)) if rec.suggested_quantity > 0 else Decimal("0.00"),
                subtotal=rec.estimated_cost,
            )
            db.add(poi)

            # Update recommendation
            rec.status = RecommendationStatus.ACCEPTED
            rec.purchase_order_id = po.id

            # Add Audit Log
            audit = AuditLog(
                organization_id=rec.organization_id,
                user_id=user.id if user else None,
                event_type=AuditEventType.PO_APPROVED,
                actor=user.full_name if user else "Authorized Manager",
                action=f"Approved Recommendation #{rec.id} -> Generated {po_number}",
                details=f"Authorized order total {format_inr(rec.estimated_cost)} for {rec.suggested_quantity} units. Decision: {comments or 'Approved'}",
            )
            db.add(audit)

            db.commit()
            return {
                "success": True,
                "po_number": po_number,
                "message": f"Recommendation #{rec.id} authorized. Generated Purchase Order {po_number} for {format_inr(rec.estimated_cost)}.",
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @staticmethod
    def reject_recommendation(
        recommendation_id: int, user_email: str = "admin@agrobulk.in", reason: str = "Budget constraint"
    ) -> Dict[str, Any]:
        """Human-in-the-Loop: Reject a pending recommendation with mandatory reason."""
        db: Session = SessionLocal()
        try:
            rec = db.query(Recommendation).filter_by(id=recommendation_id).first()
            if not rec:
                return {"success": False, "error": f"Recommendation #{recommendation_id} not found."}

            user = db.query(User).filter_by(email=user_email).first()

            rec.status = RecommendationStatus.REJECTED

            audit = AuditLog(
                organization_id=rec.organization_id,
                user_id=user.id if user else None,
                event_type=AuditEventType.PO_REJECTED,
                actor=user.full_name if user else "Authorized Staff",
                action=f"Rejected Recommendation #{rec.id}",
                details=f"Rejection Reason: {reason}",
            )
            db.add(audit)
            db.commit()
            return {"success": True, "message": f"Recommendation #{rec.id} rejected. Audit log recorded."}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @staticmethod
    def trigger_inventory_scan() -> Dict[str, Any]:
        """Execute automated inventory deficit audit and generate new recommendations."""
        db: Session = SessionLocal()
        try:
            low_items = get_low_stock_items(db)
            out_items = get_out_of_stock_items(db)
            critical = low_items + out_items

            created_recs = []
            for itm in critical:
                # Check if pending recommendation already exists to avoid duplicates
                existing = (
                    db.query(Recommendation)
                    .filter_by(
                        product_id=itm.product_id,
                        location_id=itm.location_id,
                        status=RecommendationStatus.PENDING,
                    )
                    .first()
                )
                if not existing:
                    rec = create_procurement_recommendation(
                        db, product_id=itm.product_id, location_id=itm.location_id
                    )
                    created_recs.append(rec.product.name)

            return {
                "scanned_items": len(critical),
                "new_recommendations": len(created_recs),
                "items": created_recs,
            }
        finally:
            db.close()

    @staticmethod
    def ask_ai_assistant(query: str, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Route user chat query through the multi-agent LangGraph orchestrator."""
        orchestrator = MultiAgentOrchestrator()
        return orchestrator.run_query(query=query, product_id=product_id)

    # -------------------------------------------------------------------------
    # Settings & Policy Persistence
    # -------------------------------------------------------------------------
    @staticmethod
    def get_system_settings() -> Dict[str, Any]:
        """Retrieve all configuration settings from DB or defaults."""
        db: Session = SessionLocal()
        try:
            return get_all_settings(db)
        finally:
            db.close()

    @staticmethod
    def update_system_setting(key: str, value: Any, category: Optional[str] = None) -> bool:
        """Persist a single configuration setting to DB."""
        db: Session = SessionLocal()
        try:
            set_setting_value(db, key=key, value=value, category=category)
            return True
        finally:
            db.close()

    @staticmethod
    def save_system_settings(settings_dict: Dict[str, Any]) -> bool:
        """Persist multiple configuration settings to DB."""
        db: Session = SessionLocal()
        try:
            for k, v in settings_dict.items():
                set_setting_value(db, key=k, value=v)
            return True
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # Inventory Alerts & Monitoring
    # -------------------------------------------------------------------------
    @staticmethod
    def scan_inventory_alerts() -> List[Dict[str, Any]]:
        """Run inventory alert scan and return newly created alerts."""
        db: Session = SessionLocal()
        try:
            alerts = scan_and_generate_inventory_alerts(db)
            return [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "title": a.title,
                    "message": a.message,
                    "current_stock": a.current_stock,
                    "threshold": a.threshold_value,
                }
                for a in alerts
            ]
        finally:
            db.close()

    @staticmethod
    def get_active_alerts(limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve unresolved inventory alerts."""
        db: Session = SessionLocal()
        try:
            alerts = get_active_alerts(db, limit=limit)
            return [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "title": a.title,
                    "message": a.message,
                    "product_name": a.product.name,
                    "sku": a.product.sku,
                    "location": a.location.name,
                    "current_stock": a.current_stock,
                    "threshold": a.threshold_value,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for a in alerts
            ]
        finally:
            db.close()

    @staticmethod
    def resolve_alert(alert_id: int, resolved_by: str = "Manager", notes: Optional[str] = None) -> bool:
        """Mark an inventory alert as resolved."""
        db: Session = SessionLocal()
        try:
            resolve_alert(db, alert_id=alert_id, resolved_by=resolved_by, notes=notes)
            return True
        except Exception:
            return False
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # Analytics & Business Intelligence
    # -------------------------------------------------------------------------
    @staticmethod
    def get_analytics_kpis() -> Dict[str, Any]:
        """Compute real business analytics KPIs from database records."""
        db: Session = SessionLocal()
        try:
            stats = get_dashboard_statistics(db)
            # Total spend across all approved/ordered/completed POs
            total_spend = sum(
                float(po.total_amount)
                for po in db.query(PurchaseOrder).filter(
                    PurchaseOrder.status.in_([
                        PurchaseOrderStatus.APPROVED,
                        PurchaseOrderStatus.ORDERED,
                        PurchaseOrderStatus.RECEIVED,
                    ])
                ).all()
            )

            # Stock health counts
            low_count = len(get_low_stock_items(db))
            out_count = len(get_out_of_stock_items(db))
            all_inv = get_inventory_positions(db)
            healthy_count = max(0, len(all_inv) - low_count - out_count)

            return {
                "total_inventory_value": format_inr(stats.total_inventory_value),
                "raw_inventory_value": float(stats.total_inventory_value),
                "total_procurement_spend": format_inr(total_spend),
                "raw_spend": total_spend,
                "total_products": stats.total_products,
                "total_suppliers": stats.total_suppliers,
                "low_stock_count": low_count,
                "out_of_stock_count": out_count,
                "healthy_count": healthy_count,
            }
        finally:
            db.close()

    @staticmethod
    def get_product_demand_analytics(product_id: int, location_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract real historical sales from DemandHistory and compute ML forecast
        for a specific product using Scikit-Learn.
        """
        db: Session = SessionLocal()
        try:
            # Find default location if not specified
            if not location_id:
                inv = db.query(Inventory).filter_by(product_id=product_id).first()
                location_id = inv.location_id if inv else 1

            df, quality_notes = load_demand_series(db, product_id=product_id, location_id=location_id)

            if df.empty:
                return {
                    "has_data": False,
                    "notes": quality_notes,
                    "history": [],
                    "forecast": None,
                }

            # Forecast 14 days
            try:
                fc = forecast_product_demand(db, product_id=product_id, location_id=location_id, forecast_horizon_days=14)
                forecast_data = {
                    "model_name": fc.evaluation.model_name,
                    "mae": fc.evaluation.mae,
                    "rmse": fc.evaluation.rmse,
                    "daily_forecast": [
                        {"date": str(item.forecast_date), "demand": item.forecasted_demand}
                        for item in fc.daily_forecasts
                    ],
                    "total_forecast": fc.total_forecasted_demand,
                    "risk_level": fc.stockout_risk.risk_level,
                    "days_until_stockout": fc.stockout_risk.days_until_stockout,
                }
            except Exception as e:
                forecast_data = {"error": str(e)}

            history_items = [
                {"date": str(row["date"].date() if hasattr(row["date"], "date") else row["date"])[:10], "demand": float(row["demand"])}
                for _, row in df.iterrows()
            ]

            return {
                "has_data": True,
                "notes": quality_notes,
                "history": history_items,
                "forecast": forecast_data,
            }
        finally:
            db.close()

    @staticmethod
    def get_spend_by_supplier() -> List[Dict[str, Any]]:
        """Compute aggregated procurement spending per supplier."""
        db: Session = SessionLocal()
        try:
            pos = db.query(PurchaseOrder).all()
            supplier_spend: Dict[str, float] = {}
            for po in pos:
                name = po.supplier.name
                supplier_spend[name] = supplier_spend.get(name, 0.0) + float(po.total_amount)

            return [
                {"supplier": name, "total_spend": spend, "formatted_spend": format_inr(spend)}
                for name, spend in sorted(supplier_spend.items(), key=lambda x: x[1], reverse=True)
            ]
        finally:
            db.close()
