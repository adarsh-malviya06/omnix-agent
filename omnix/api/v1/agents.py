"""
FastAPI router for Multi-Agent LangGraph operations.
"""

from fastapi import APIRouter

from omnix.agents.orchestrator import MultiAgentOrchestrator
from omnix.schemas.agent import AgentRunRequest, AgentRunResponse

router = APIRouter(prefix="/agents", tags=["Multi-Agent Orchestration"])


@router.post("/run", response_model=AgentRunResponse)
def run_agents(request: AgentRunRequest):
    """
    Trigger LangGraph multi-agent orchestration across Supervisor,
    Inventory, Supplier, and Procurement agents.
    """
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run_query(
        query=request.query,
        product_id=request.product_id,
        product_sku=request.product_sku,
        location_id=request.location_id,
        organization_id=request.organization_id,
    )
    return AgentRunResponse(
        query=result["query"],
        final_response=result["final_response"],
        plan=result["plan"] or [],
        execution_trace=result["execution_trace"] or [],
        inventory_data=result["inventory_data"],
        forecasting_data=result["forecasting_data"],
        supplier_data=result["supplier_data"],
        procurement_data=result["procurement_data"],
    )
