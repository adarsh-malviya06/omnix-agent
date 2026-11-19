"""
API v1 Router registry with complete operational endpoints.
"""

from fastapi import APIRouter
from omnix.api.v1.agents import router as agents_router
from omnix.api.v1.forecasting import router as forecasting_router
from omnix.api.v1.health import router as health_router
from omnix.api.v1.inventory import router as inventory_router
from omnix.api.v1.knowledge import router as knowledge_router
from omnix.api.v1.procurement import router as procurement_router
from omnix.api.v1.suppliers import router as suppliers_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(suppliers_router)
api_v1_router.include_router(procurement_router)
api_v1_router.include_router(forecasting_router)
api_v1_router.include_router(knowledge_router)
api_v1_router.include_router(agents_router)
