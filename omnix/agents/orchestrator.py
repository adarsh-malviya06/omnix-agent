"""
High-level Multi-Agent orchestration service for API and UI consumption.
"""

from typing import Any, Dict, Optional

from omnix.agents.workflow import build_multi_agent_graph
from omnix.agents.state import OmnixAgentState


class MultiAgentOrchestrator:
    """Service wrapper for compiled LangGraph agent executions."""

    def __init__(self):
        self.graph = build_multi_agent_graph()

    def run_query(
        self,
        query: str,
        product_id: Optional[int] = None,
        product_sku: Optional[str] = None,
        location_id: Optional[int] = None,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute the multi-agent graph with initial state and return synthesized results.
        """
        initial_state: OmnixAgentState = {
            "user_query": query,
            "organization_id": organization_id,
            "product_id": product_id,
            "product_sku": product_sku,
            "location_id": location_id,
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
            "loop_count": 0,
        }

        # Execute LangGraph state machine
        final_state = self.graph.invoke(initial_state)

        return {
            "query": query,
            "final_response": final_state.get("final_response"),
            "plan": final_state.get("plan"),
            "execution_trace": final_state.get("execution_trace"),
            "inventory_data": final_state.get("inventory_data"),
            "forecasting_data": final_state.get("forecasting_data"),
            "supplier_data": final_state.get("supplier_data"),
            "procurement_data": final_state.get("procurement_data"),
        }
