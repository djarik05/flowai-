"""
Mouse Control API routes for GestureFlow AI backend (Phase 6A).
"""

import logging

from fastapi import APIRouter, HTTPException, status
from app.schemas.mouse import (
    CursorPointRequest,
    MouseSettingsUpdateRequest,
    MouseStatusResponse,
)
from app.services.mouse_controller import get_mouse_controller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mouse", tags=["Mouse Control"])


@router.get(
    "/status",
    response_model=MouseStatusResponse,
    summary="Get mouse control status",
    description="Returns live mouse controller status, settings, and telemetry.",
)
async def get_mouse_status() -> MouseStatusResponse:
    """Get mouse control status."""
    ctrl = get_mouse_controller()
    return ctrl.get_status()


@router.post(
    "/enable",
    response_model=MouseStatusResponse,
    summary="Enable mouse control",
    description="Enables desktop cursor control via hand tracking.",
)
async def enable_mouse_control() -> MouseStatusResponse:
    """
    Enable desktop cursor control.
    Starts MouseController worker thread. Camera lifecycle is completely independent.
    """
    ctrl = get_mouse_controller()
    ctrl.start()
    return ctrl.get_status()


@router.post(
    "/disable",
    response_model=MouseStatusResponse,
    summary="Disable mouse control",
    description="Disables desktop cursor control immediately.",
)
async def disable_mouse_control() -> MouseStatusResponse:
    """
    Disable desktop cursor control.
    Immediately halts cursor movement. Does NOT stop camera or hand tracking
    so preview and gestures continue uninterrupted (Requirement 7).
    """
    ctrl = get_mouse_controller()
    ctrl.stop()
    return ctrl.get_status()


@router.post(
    "/emergency-stop",
    response_model=MouseStatusResponse,
    summary="Emergency stop mouse control",
    description="Immediately halts all desktop cursor movement and disables mouse control safely.",
)
async def emergency_stop_mouse() -> MouseStatusResponse:
    """
    Emergency stop mouse controller immediately.
    Halts all OS cursor movement and transitions controller to disabled state.
    """
    ctrl = get_mouse_controller()
    ctrl.stop()
    return ctrl.get_status()


@router.put(
    "/settings",
    response_model=MouseStatusResponse,
    summary="Update mouse settings",
    description="Updates cursor sensitivity, smoothing alpha, tracking margins, and timeout.",
)
async def update_mouse_settings(request: MouseSettingsUpdateRequest) -> MouseStatusResponse:
    """Update mouse settings."""
    ctrl = get_mouse_controller()
    ctrl.update_settings(**request.model_dump(exclude_unset=True))
    return ctrl.get_status()


@router.post(
    "/click",
    summary="Trigger left mouse click",
    description="Explicitly triggers a safe left click using current cursor position if enabled and not in cooldown.",
)
async def trigger_left_click() -> dict:
    """Trigger left mouse click."""
    ctrl = get_mouse_controller()
    clicked = ctrl.trigger_left_click()
    return {"success": clicked, "enabled": ctrl.is_enabled, "click_count": ctrl.get_status().click_count}


@router.post(
    "/click-right",
    summary="Trigger right mouse click",
    description="Explicitly triggers a safe right click using current cursor position if enabled and not in cooldown.",
)
async def trigger_right_click() -> dict:
    """Trigger right mouse click."""
    ctrl = get_mouse_controller()
    clicked = ctrl.trigger_right_click()
    return {"success": clicked, "enabled": ctrl.is_enabled, "right_click_count": ctrl.get_status().right_click_count}


@router.post(
    "/cursor-point",
    summary="Feed normalized cursor point",
    description="Enqueues a normalized index fingertip position and optional pinch distance asynchronously.",
)
async def feed_cursor_point(request: CursorPointRequest) -> dict:
    """Feed normalized cursor point."""
    ctrl = get_mouse_controller()
    clicked = False
    if ctrl.is_enabled:
        clicked = ctrl.on_landmark_point(
            request.x,
            request.y,
            capture_time=request.timestamp,
            pinch_distance=request.pinch_distance,
            thumb_x=request.thumb_x,
            thumb_y=request.thumb_y,
            right_pinch_distance=request.right_pinch_distance,
            middle_x=request.middle_x,
            middle_y=request.middle_y,
        )
    return {"success": True, "enabled": ctrl.is_enabled, "clicked": clicked}
