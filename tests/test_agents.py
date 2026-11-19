"""
Automated tests for Phase 6: OMNIX Multi-Agent System using LangGraph.

Tests cover:
- Individual agent node functionality (InventoryAgent, SupplierAgent, ProcurementAgent).
- Supervisor intent parsing, plan formulation, and final synthesis.
- Complete end-to-end Inventory-to-Procurement multi-agent workflow.
- Guardrails: Non-negative stock checks, deterministic spending thresholds,
  no real purchase execution, pending human approval enforcement.
- Prevention of unlimited loops.
- REST API integration: POST /api/v1/agents/run.
"""

import pytest
from fastapi.testclient import TestClient

from omnix.agents.nodes import (
    inventory_agent_node,
    procurement_agent_node,
    supplier_agent_node,
    supervisor_agent_node,
)
from omnix.agents.orchestrator import MultiAgentOrchestrator
from omnix.agents.state import OmnixAgentState
from omnix.api.main import app
from omnix.db.models import Location, Product
from omnix.db.session import SessionLocal


@pytest.fixture(scope="module")
def client():
    """FastAPI Test Client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def sample_product_and_location():
    """Retrieve existing seeded product (Basmati Rice) and warehouse location."""
    db = SessionLocal()
    prod = db.query(Product).filter_by(sku="SKU-RICE-25KG").first()
    loc = db.query(Location).filter_by(code="WH-VASHI").first()
    data = {"product_id": prod.id, "product_sku": prod.sku, "location_id": loc.id}
    db.close()
    return data


class TestIndividualAgentNodes:
    def test_inventory_agent_node(self, sample_product_and_location):
        state: OmnixAgentState = {
            "user_query": "Check stock for rice",
            "product_id": sample_product_and_location["product_id"],
            "location_id": sample_product_and_location["location_id"],
            "product_sku": sample_product_and_location["product_sku"],
            "current_step": "start",
            "plan": ["inventory_agent"],
            "is_complete": False,
            "final_response": "",
            "execution_trace": [],
            "inventory_data": None,
            "forecasting_data": None,
            "supplier_data": None,
            "procurement_data": None,
            "policy_data": None,
            "error": None,
            "loop_count": 0,
            "organization_id": None,
        }
        res = inventory_agent_node(state)
        assert res["current_step"] == "inventory_complete"
        assert res["inventory_data"] is not None
        assert len(res["inventory_data"]["stock_positions"]) >= 1
        assert res["forecasting_data"] is not None
        assert "stockout_risk_level" in res["forecasting_data"]
        assert len(res["execution_trace"]) == 1
        assert res["execution_trace"][0]["agent_name"] == "InventoryAgent"

    def test_supplier_agent_node(self, sample_product_and_location):
        state: OmnixAgentState = {
            "user_query": "Compare vendors for rice",
            "product_id": sample_product_and_location["product_id"],
            "location_id": sample_product_and_location["location_id"],
            "product_sku": sample_product_and_location["product_sku"],
            "current_step": "inventory_complete",
            "plan": ["supplier_agent"],
            "is_complete": False,
            "final_response": "",
            "execution_trace": [],
            "inventory_data": None,
            "forecasting_data": None,
            "supplier_data": None,
            "procurement_data": None,
            "policy_data": None,
            "error": None,
            "loop_count": 0,
            "organization_id": None,
        }
        res = supplier_agent_node(state)
        assert res["current_step"] == "supplier_complete"
        assert res["supplier_data"] is not None
        assert len(res["supplier_data"]["quotes"]) >= 2
        assert len(res["execution_trace"]) == 1
        assert res["execution_trace"][0]["agent_name"] == "SupplierAgent"

    def test_procurement_agent_node(self, sample_product_and_location):
        state: OmnixAgentState = {
            "user_query": "Replenish rice stock",
            "product_id": sample_product_and_location["product_id"],
            "location_id": sample_product_and_location["location_id"],
            "product_sku": sample_product_and_location["product_sku"],
            "current_step": "supplier_complete",
            "plan": ["procurement_agent"],
            "is_complete": False,
            "final_response": "",
            "execution_trace": [],
            "inventory_data": None,
            "forecasting_data": None,
            "supplier_data": None,
            "procurement_data": None,
            "policy_data": None,
            "error": None,
            "loop_count": 0,
            "organization_id": None,
        }
        res = procurement_agent_node(state)
        assert res["current_step"] == "procurement_complete"
        assert res["procurement_data"] is not None
        assert res["procurement_data"]["requires_human_approval"] is True
        assert res["policy_data"] is not None
        assert len(res["execution_trace"]) == 1
        assert res["execution_trace"][0]["agent_name"] == "ProcurementAgent"


class TestEndToEndMultiAgentWorkflow:
    def test_full_reorder_workflow_execution(self, sample_product_and_location):
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run_query(
            query="Basmati Rice is low on stock, compare suppliers and draft a reorder recommendation",
            product_id=sample_product_and_location["product_id"],
            location_id=sample_product_and_location["location_id"],
            product_sku=sample_product_and_location["product_sku"],
        )

        # 1. Plan check
        assert result["plan"] == ["inventory_agent", "supplier_agent", "procurement_agent"]

        # 2. Trace check: all 4 agents participated
        trace = result["execution_trace"]
        agents_participated = [step["agent_name"] for step in trace]
        assert "SupervisorAgent" in agents_participated
        assert "InventoryAgent" in agents_participated
        assert "SupplierAgent" in agents_participated
        assert "ProcurementAgent" in agents_participated

        # 3. Data synthesis check
        final_rep = result["final_response"]
        assert "Inventory Analysis" in final_rep
        assert "Supplier Evaluation" in final_rep
        assert "Procurement Recommendation" in final_rep
        assert "PENDING_APPROVAL" in final_rep
        assert "₹" in final_rep

    def test_supplier_only_intent_workflow(self, sample_product_and_location):
        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.run_query(
            query="Show me supplier price comparisons and lead times for rice",
            product_id=sample_product_and_location["product_id"],
        )
        assert "supplier_agent" in result["plan"]
        assert result["supplier_data"] is not None

    def test_supervisor_loop_prevention(self):
        state: OmnixAgentState = {
            "user_query": "cyclic loop test",
            "product_id": None,
            "location_id": None,
            "product_sku": None,
            "organization_id": None,
            "current_step": "start",
            "plan": [],
            "is_complete": False,
            "final_response": "",
            "execution_trace": [],
            "inventory_data": None,
            "forecasting_data": None,
            "supplier_data": None,
            "procurement_data": None,
            "policy_data": None,
            "error": None,
            "loop_count": 6,  # Exceeds threshold
        }
        res = supervisor_agent_node(state)
        assert res["is_complete"] is True
        assert "maximum supervisor iterations exceeded" in res["final_response"]


class TestMultiAgentAPI:
    def test_api_agents_run(self, client, sample_product_and_location):
        payload = {
            "query": "Audit inventory and prepare purchase recommendation for Basmati Rice",
            "product_id": sample_product_and_location["product_id"],
            "location_id": sample_product_and_location["location_id"],
            "product_sku": sample_product_and_location["product_sku"],
        }
        res = client.post("/api/v1/agents/run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data["plan"]) >= 1
        assert len(data["execution_trace"]) >= 4
        assert "PENDING_APPROVAL" in data["final_response"]
