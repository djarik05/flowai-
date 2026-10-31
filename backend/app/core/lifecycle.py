"""
Application lifecycle management for GestureFlow AI backend.

Handles startup and shutdown events, initialization of services,
and graceful resource cleanup.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.services.application_service import ApplicationService

logger = get_logger(__name__)


# Global application service instance
_application_service: ApplicationService | None = None


def get_application_service() -> ApplicationService:
    """
    Get the global application service instance.

    Returns:
        ApplicationService instance

    Raises:
        RuntimeError: If service has not been initialized
    """
    if _application_service is None:
        raise RuntimeError("Application service not initialized. Call initialize_application() first.")
    return _application_service


async def initialize_application() -> None:
    """
    Initialize the application on startup.

    Performs:
    - Configuration validation
    - Logging setup
    - Application service initialization
    - Marks backend as ready
    """
    global _application_service

    logger.info("Starting GestureFlow AI backend initialization")

    # Validate configuration
    logger.info(
        "Configuration loaded",
        extra={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "api_host": settings.api_host,
            "api_port": settings.api_port,
            "api_prefix": settings.api_prefix,
        },
    )

    # Initialize application service
    _application_service = ApplicationService()
    await _application_service.initialize()

    logger.info("GestureFlow AI backend initialized successfully")


async def shutdown_application() -> None:
    """
    Shutdown the application gracefully.

    Performs:
    - Logs shutdown event
    - Releases resources from application service
    - Marks application as shutting down
    """
    global _application_service

    logger.info("Shutting down GestureFlow AI backend")

    if _application_service:
        await _application_service.shutdown()
        _application_service = None

    logger.info("GestureFlow AI backend shutdown complete")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager for startup/shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None during application lifetime
    """
    # Startup
    await initialize_application()
    try:
        yield
    finally:
        # Shutdown
        await shutdown_application()