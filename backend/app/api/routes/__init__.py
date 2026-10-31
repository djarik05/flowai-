"""
Routes package for GestureFlow AI backend.

Exports all route modules.
"""

from app.api.routes import camera, health, status, tracking

__all__ = ["camera", "health", "status", "tracking"]