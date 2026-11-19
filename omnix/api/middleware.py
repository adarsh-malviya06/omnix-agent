"""
FastAPI error handlers converting domain exceptions to standardized JSON responses.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from omnix.core.exceptions import OmnixException


async def omnix_exception_handler(request: Request, exc: OmnixException) -> JSONResponse:
    """Handle custom domain exceptions gracefully."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled server exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred processing your request.",
            "details": str(exc) if hasattr(exc, "__str__") else {},
            "path": str(request.url.path),
        },
    )
