"""
Standardized Pydantic schemas for health, system status, and common API contracts.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Service status indicator")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC server timestamp",
    )
    environment: str = Field(..., description="Active runtime environment")


class ErrorResponse(BaseModel):
    """Standardized API error response payload."""
    error: bool = Field(default=True, description="Always true for error responses")
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable explanation of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Contextual debug details")
