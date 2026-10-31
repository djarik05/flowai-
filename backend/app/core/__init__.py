"""
Core package for GestureFlow AI backend.

Exports configuration, logging, and lifecycle management.
"""

from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.core.lifecycle import get_application_service, initialize_application, lifespan, shutdown_application

__all__ = [
    "settings",
    "get_logger",
    "setup_logging",
    "initialize_application",
    "shutdown_application",
    "lifespan",
    "get_application_service",
]