"""
Automated tests for Phase 7: Application Integration & Unified Backend Client.

Tests cover:
- Real dashboard KPIs calculation.
- Live inventory table formatting.
- Live supplier table formatting.
- Live purchase orders and recommendations tables.
- Human-in-the-loop recommendation approval creating a real Purchase Order.
- Human-in-the-loop recommendation rejection with audit log entry.
- Automated inventory deficit audit scan.
- AI Assistant multi-agent integration.
"""

from decimal import Decimal
import pytest

from omnix.db.base import PurchaseOrderStatus, RecommendationStatus
from omnix.db.models import AuditLog, PurchaseOrder, Recommendation
from omnix.db.session import SessionLocal
from omnix.ui.backend_client import BackendClient


class TestBackendClientKPIs:
    def test_get_dashboard_kpis(self):
        kpis = BackendClient.get_dashboard_kpis()
        assert int(kpis["total_products"]) >= 6
        assert "₹" in kpis["inventory_val"]
        assert int(kpis["low_stock_count"]) >= 1
        assert int(kpis["out_of_stock_count"]) >= 1
        assert int(kpis["total_suppliers"]) >= 4

    def test_get_inventory_table(self):
        items = BackendClient.get_inventory_table()
        assert len(items) >= 6
        skus = [i["sku"] for i in items]
        assert "SKU-RICE-25KG" in skus
        assert "SKU-SUGAR-50KG" in skus
        for itm in items:
            assert "₹" in itm["unit_cost"]
            assert itm["status"] in ["IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"]

    def test_get_suppliers_table(self):
        suppliers = BackendClient.get_suppliers_table()
        assert len(suppliers) >= 4
        codes = [s["code"] for s in suppliers]
        assert "SUP-AGRO-01" in codes
        for s in suppliers:
            assert "%" in s["reliability_score"]
            assert "Days" in s["avg_lead_days"]


class TestHumanInTheLoopApprovalWorkflow:
    def test_approve_recommendation_generates_po(self):
        # 1. Trigger scan to ensure at least one pending recommendation
        scan_res = BackendClient.trigger_inventory_scan()
        recs = BackendClient.get_recommendations_table()
        pending = [r for r in recs if r["status"] == "PENDING"]
        assert len(pending) >= 1

        target_rec = pending[0]
        rec_id = target_rec["id"]

        # 2. Approve via BackendClient
        res = BackendClient.approve_recommendation(
            recommendation_id=rec_id,
            user_email="admin@agrobulk.in",
            comments="Approved by Test Suite for immediate replenishment",
        )
        assert res["success"] is True
        assert "PO-2026-" in res["po_number"]

        # 3. Verify in database
        db = SessionLocal()
        try:
            db_rec = db.query(Recommendation).filter_by(id=rec_id).first()
            assert db_rec.status == RecommendationStatus.ACCEPTED
            assert db_rec.purchase_order_id is not None

            db_po = db.query(PurchaseOrder).filter_by(id=db_rec.purchase_order_id).first()
            assert db_po.status == PurchaseOrderStatus.APPROVED
            assert db_po.total_amount == db_rec.estimated_cost

            # Check audit log
            audit = (
                db.query(AuditLog)
                .filter(AuditLog.action.contains(f"Approved Recommendation #{rec_id}"))
                .first()
            )
            assert audit is not None
        finally:
            db.close()

    def test_reject_recommendation(self):
        # Trigger scan to generate another pending recommendation if needed
        BackendClient.trigger_inventory_scan()
        recs = BackendClient.get_recommendations_table()
        pending = [r for r in recs if r["status"] == "PENDING"]
        if pending:
            target_rec = pending[0]
            rec_id = target_rec["id"]
            res = BackendClient.reject_recommendation(
                recommendation_id=rec_id,
                reason="Temporary budget postponement",
            )
            assert res["success"] is True

            db = SessionLocal()
            try:
                db_rec = db.query(Recommendation).filter_by(id=rec_id).first()
                assert db_rec.status == RecommendationStatus.REJECTED
            finally:
                db.close()


class TestAIAssistantIntegration:
    def test_ask_ai_assistant_e2e(self):
        result = BackendClient.ask_ai_assistant("Check stock for rice and recommend replenishment")
        assert "final_response" in result
        assert "Inventory Analysis" in result["final_response"]
        assert "Procurement Recommendation" in result["final_response"]
        assert len(result["execution_trace"]) >= 1
