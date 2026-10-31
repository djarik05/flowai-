"""
Exceptions package for GestureFlow AI backend.

Exports custom exceptions and handler registration.
"""

from app.exceptions.handlers import (
    ApplicationStartupError,
    ConfigurationError,
    register_exception_handlers,
)

__all__ = [
    "ApplicationStartupError",
    "ConfigurationError",
    "register_exception_handlers",
]