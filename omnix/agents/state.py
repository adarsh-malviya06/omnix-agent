"""
Shared Typed Workflow State for OMNIX Multi-Agent LangGraph Architecture.
"""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class AgentActionLog(BaseModel):
    """Immutable log entry capturing each agent's execution step and decision."""
    agent_name: str
    action: str
    details: str
    timestamp: Optional[str] = None


class OmnixAgentState(TypedDict):
    """
    State shared across the Supervisor, Inventory, Supplier, and Procurement agents.
    Every agent reads and mutates typed slices of this state.
    """
    # User Request Context
    user_query: str
    organization_id: Optional[int]
    product_id: Optional[int]
    product_sku: Optional[str]
    location_id: Optional[int]

    # Supervisor Orchestration
    current_step: str
    plan: List[str]
    is_complete: bool
    final_response: str
    execution_trace: List[Dict[str, Any]]

    # Agent Data Payloads
    inventory_data: Optional[Dict[str, Any]]
    forecasting_data: Optional[Dict[str, Any]]
    supplier_data: Optional[Dict[str, Any]]
    procurement_data: Optional[Dict[str, Any]]
    policy_data: Optional[Dict[str, Any]]

    # Error handling & guardrails
    error: Optional[str]
    loop_count: int
