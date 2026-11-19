"""
LangGraph Multi-Agent Workflow Graph Assembly.
Connects Supervisor, Inventory, Supplier, and Procurement nodes with typed state routing.
"""

from typing import Dict, Literal
from langgraph.graph import END, START, StateGraph

from omnix.agents.nodes import (
    inventory_agent_node,
    procurement_agent_node,
    supplier_agent_node,
    supervisor_agent_node,
)
from omnix.agents.state import OmnixAgentState


def route_supervisor_next(state: OmnixAgentState) -> str:
    """
    Conditional edge function determining the next node from supervisor state.
    """
    current_step = state.get("current_step", "start")
    plan = state.get("plan", [])

    if current_step == "plan_ready" and plan:
        # Route to the first agent in plan
        first_agent = plan[0]
        return first_agent

    if current_step in ["inventory_complete", "supplier_complete", "procurement_complete"]:
        # If in a multi-step pipeline, find next target or return to supervisor
        if current_step == "inventory_complete":
            if "supplier_agent" in plan:
                return "supplier_agent"
            elif "procurement_agent" in plan:
                return "procurement_agent"
            return "supervisor_agent"

        elif current_step == "supplier_complete":
            if "procurement_agent" in plan:
                return "procurement_agent"
            return "supervisor_agent"

        elif current_step == "procurement_complete":
            return "supervisor_agent"

    return "supervisor_agent"


def build_multi_agent_graph():
    """
    Constructs and compiles the OMNIX Supervisor Multi-Agent LangGraph.
    """
    workflow = StateGraph(OmnixAgentState)

    # 1. Register Agent Nodes
    workflow.add_node("supervisor_agent", supervisor_agent_node)
    workflow.add_node("inventory_agent", inventory_agent_node)
    workflow.add_node("supplier_agent", supplier_agent_node)
    workflow.add_node("procurement_agent", procurement_agent_node)

    # 2. Add Edges
    # Entry point is always Supervisor
    workflow.add_edge(START, "supervisor_agent")

    # Conditional routing from Supervisor
    workflow.add_conditional_edges(
        "supervisor_agent",
        route_supervisor_next,
        {
            "inventory_agent": "inventory_agent",
            "supplier_agent": "supplier_agent",
            "procurement_agent": "procurement_agent",
            "supervisor_agent": END,  # When supervisor marks complete
        },
    )

    # Worker edges route to downstream worker or back to supervisor
    workflow.add_conditional_edges(
        "inventory_agent",
        route_supervisor_next,
        {
            "supplier_agent": "supplier_agent",
            "procurement_agent": "procurement_agent",
            "supervisor_agent": "supervisor_agent",
        },
    )

    workflow.add_conditional_edges(
        "supplier_agent",
        route_supervisor_next,
        {
            "procurement_agent": "procurement_agent",
            "supervisor_agent": "supervisor_agent",
        },
    )

    workflow.add_edge("procurement_agent", "supervisor_agent")

    return workflow.compile()
