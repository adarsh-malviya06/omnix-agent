"""
FastAPI application entry point for OMNIX Backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omnix.api.middleware import generic_exception_handler, omnix_exception_handler
from omnix.api.v1 import api_v1_router
from omnix.core.config import get_settings
from omnix.core.exceptions import OmnixException


def create_app() -> FastAPI:
    """Application factory for OMNIX Backend API."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-Agent Procurement & Inventory Intelligence Platform Backend",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS configuration for cross-origin local access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(OmnixException, omnix_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Root health redirect/status
    @app.get("/", tags=["System & Diagnostics"])
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "docs": "/docs" if settings.debug else "disabled",
        }

    # Register API Routers
    app.include_router(api_v1_router)

    return app


app = create_app()
