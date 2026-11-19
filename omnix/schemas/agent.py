"""
Pydantic schemas for Multi-Agent requests and execution telemetry.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """User operational prompt to trigger LangGraph multi-agent execution."""
    query: str = Field(..., description="Operational question or task for OMNIX agents")
    product_id: Optional[int] = Field(None, description="Optional target product ID")
    product_sku: Optional[str] = Field(None, description="Optional target SKU code")
    location_id: Optional[int] = Field(None, description="Optional target warehouse/store location")
    organization_id: Optional[int] = Field(None, description="Optional tenant boundary")


class AgentExecutionStep(BaseModel):
    """Execution telemetry record for an individual agent."""
    agent_name: str
    action: str
    details: str
    timestamp: str


class AgentRunResponse(BaseModel):
    """Consolidated multi-agent execution response."""
    query: str
    final_response: str
    plan: List[str]
    execution_trace: List[AgentExecutionStep]
    inventory_data: Optional[Dict[str, Any]] = None
    forecasting_data: Optional[Dict[str, Any]] = None
    supplier_data: Optional[Dict[str, Any]] = None
    procurement_data: Optional[Dict[str, Any]] = None
