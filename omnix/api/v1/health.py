"""
System, diagnostics, and health-check router for OMNIX Backend.
"""

from fastapi import APIRouter, Depends
from omnix.core.config import Settings, get_settings
from omnix.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["System & Diagnostics"])


@router.get("", response_model=HealthResponse)
async def check_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return runtime health status and metadata."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
