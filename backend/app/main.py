"""
Main application entry point for GestureFlow AI backend.

Creates and configures the FastAPI application with all routes,
middleware, exception handlers, and lifecycle management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.lifecycle import lifespan
from app.core.logging_config import setup_logging
from app.exceptions import register_exception_handlers

# Setup logging before creating app
setup_logging()
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="GestureFlow AI - Webcam-based AI Gesture Controller Backend",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Store settings in app state for access in exception handlers
    app.state.settings = settings

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Root health check endpoint alias
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def root_health_check():
        return {
            "status": "ok",
            "application": settings.app_name,
            "version": settings.app_version,
        }

    # Include API router
    app.include_router(api_router)

    logger.info(
        "FastAPI application created",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "api_prefix": settings.api_prefix,
            "cors_origins": settings.cors_allowed_origins,
        },
    )

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )