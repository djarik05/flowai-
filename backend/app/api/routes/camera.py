"""
Camera routes for GestureFlow AI backend.

Provides camera management endpoints.
"""

from fastapi import APIRouter, HTTPException, status

from typing import Optional

from app.schemas.camera import (
    CameraConfigRequest,
    CameraConfigResponse,
    CameraStatusResponse,
    CameraOwnershipRequest,
    CameraOwnershipResponse,
)
from app.schemas.common import ErrorResponse
from app.core.lifecycle import get_application_service

router = APIRouter(prefix="/camera", tags=["Camera"])


def get_camera_manager():
    """Get singleton camera manager from application service."""
    from app.services.camera_manager import CameraManager
    try:
        app_service = get_application_service()
        camera_comp = app_service.get_component_status("camera")
        if camera_comp is None:
            return CameraManager()
        instance = camera_comp.metadata.get("instance")
        if instance is None:
            instance = CameraManager()
            camera_comp.metadata["instance"] = instance
        return instance
    except RuntimeError:
        return CameraManager()


@router.get(
    "/status",
    response_model=CameraStatusResponse,
    summary="Get camera status",
    description="Returns current camera state, configuration, and discovered devices.",
    responses={
        200: {"description": "Camera status retrieved successfully"},
        503: {"description": "Service not initialized"},
    },
)
async def get_camera_status() -> CameraStatusResponse:
    """
    Get camera status.

    Returns information about the current camera state, active configuration,
    and list of discovered camera devices.
    """
    app_service = get_application_service()
    camera_status = app_service.get_component_status("camera")

    if camera_status is None or camera_status.metadata.get("instance") is None:
        # Return default status if camera not initialized
        return CameraStatusResponse(
            state="disconnected",
            camera_index=0,
            devices=[],
            owner="none",
        )

    camera_manager = camera_status.metadata["instance"]
    status_data = camera_manager.get_status()

    return CameraStatusResponse(
        state=status_data.state.value,
        camera_index=status_data.camera_index,
        actual_width=status_data.actual_width,
        actual_height=status_data.actual_height,
        actual_fps=status_data.actual_fps,
        backend=status_data.backend,
        is_capturing=status_data.is_capturing,
        last_frame_time=status_data.last_frame_time,
        frames_captured=status_data.frames_captured,
        frames_dropped=status_data.frames_dropped,
        last_error=status_data.last_error,
        devices=[
            {
                "index": d.index,
                "name": d.name,
                "width": d.width,
                "height": d.height,
                "fps": d.fps,
                "backend": d.backend,
                "available": d.available,
            }
            for d in status_data.devices
        ],
        owner=status_data.owner,
    )


@router.get(
    "/devices",
    summary="List available cameras",
    description="Returns list of discovered camera devices.",
    responses={
        200: {"description": "Camera devices listed successfully"},
    },
)
async def list_camera_devices() -> dict:
    """
    List available camera devices.

    Discovers and returns information about available camera devices.
    Note: Device name discovery is platform-dependent and may be limited.
    """
    app_service = get_application_service()
    camera_status = app_service.get_component_status("camera")

    if camera_status is None or camera_status.metadata.get("instance") is None:
        # Create temporary manager for discovery
        from app.services.camera_manager import CameraManager
        temp_manager = CameraManager()
        devices = temp_manager.discover_cameras()
        return {
            "devices": [
                {
                    "index": d.index,
                    "name": d.name,
                    "width": d.width,
                    "height": d.height,
                    "fps": d.fps,
                    "backend": d.backend,
                    "available": d.available,
                }
                for d in devices
            ],
            "note": "Devices discovered via temporary probe",
        }

    camera_manager = camera_status.metadata["instance"]
    devices = camera_manager.discover_cameras()

    return {
        "devices": [
            {
                "index": d.index,
                "name": d.name,
                "width": d.width,
                "height": d.height,
                "fps": d.fps,
                "backend": d.backend,
                "available": d.available,
            }
            for d in devices
        ],
    }


@router.post(
    "/start",
    response_model=CameraConfigResponse,
    summary="Start camera capture",
    description="Starts camera capture with current or provided configuration.",
    responses={
        200: {"description": "Camera started successfully"},
        400: {"description": "Invalid configuration"},
        409: {"description": "Camera already capturing"},
        500: {"description": "Camera initialization failed"},
    },
)
async def start_camera(config: CameraConfigRequest) -> CameraConfigResponse:
    """
    Start camera capture.

    Starts the camera with the provided configuration or defaults.
    Validates the configuration and prevents duplicate capture sessions.
    """
    app_service = get_application_service()
    camera_status = app_service.get_component_status("camera")

    if camera_status is None or camera_status.metadata.get("instance") is None:
        from app.services.camera_manager import CameraManager
        camera_manager = CameraManager()
        camera_status.metadata["instance"] = camera_manager
    else:
        camera_manager = camera_status.metadata["instance"]

    # Apply configuration if provided (for future use)
    # Note: Current implementation uses settings from config.py
    # This endpoint accepts config for future extensibility

    success = camera_manager.start()

    if success:
        app_service.set_component_state(
            "camera",
            "ready",
            metadata={"instance": camera_manager},
        )
        return CameraConfigResponse(
            success=True,
            message="Camera started successfully",
            applied_config=config,
        )
    else:
        app_service.set_component_state(
            "camera",
            "error",
            error=camera_manager.get_status().last_error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error={
                    "code": "CAMERA_START_FAILED",
                    "message": camera_manager.get_status().last_error or "Failed to start camera",
                }
            ).model_dump(),
        )


@router.post(
    "/stop",
    response_model=CameraConfigResponse,
    summary="Stop camera capture",
    description="Stops camera capture and releases resources safely.",
    responses={
        200: {"description": "Camera stopped successfully"},
        409: {"description": "Camera not capturing"},
    },
)
async def stop_camera() -> CameraConfigResponse:
    """
    Stop camera capture.

    Stops the camera capture session and releases all resources.
    Repeated stop requests are handled gracefully.
    """
    # Scenario D: Auto-disable mouse control when camera stops
    try:
        from app.services.mouse_controller import get_mouse_controller
        m_ctrl = get_mouse_controller()
        if m_ctrl.is_enabled:
            m_ctrl.stop()
    except Exception:
        pass

    try:
        from app.api.routes.tracking import get_tracking_service
        t_svc = get_tracking_service()
        if t_svc.is_active:
            t_svc.stop()
    except Exception:
        pass

    app_service = get_application_service()
    camera_status = app_service.get_component_status("camera")

    if camera_status is None or camera_status.metadata.get("instance") is None:
        return CameraConfigResponse(
            success=True,
            message="Camera already stopped",
        )

    camera_manager = camera_status.metadata["instance"]
    success = camera_manager.stop()

    app_service.set_component_state("camera", "not_initialized")

    return CameraConfigResponse(
        success=success,
        message="Camera stopped successfully" if success else "Camera was already stopped",
    )


@router.get(
    "/owner",
    summary="Get camera hardware owner",
    description="Returns which pipeline currently owns the hardware camera: 'none', 'browser', or 'backend'.",
)
async def get_camera_owner() -> dict:
    """Get current physical camera owner."""
    camera_manager = get_camera_manager()
    return {"owner": camera_manager.get_owner()}


@router.post(
    "/claim",
    response_model=CameraOwnershipResponse,
    summary="Claim camera hardware ownership",
    description="Claims physical camera ownership for browser or backend, releasing backend capture if browser claims.",
)
async def claim_camera_ownership(request: CameraOwnershipRequest) -> CameraOwnershipResponse:
    """Claim camera ownership."""
    camera_manager = get_camera_manager()
    success = camera_manager.claim_ownership(request.owner)
    return CameraOwnershipResponse(
        success=success,
        owner=camera_manager.get_owner(),
        message=f"Ownership claimed for {request.owner}" if success else "Failed to claim ownership",
    )


@router.post(
    "/release",
    response_model=CameraOwnershipResponse,
    summary="Release camera hardware ownership",
    description="Releases camera hardware ownership and stops active backend capture.",
)
async def release_camera_ownership(request: Optional[CameraOwnershipRequest] = None) -> CameraOwnershipResponse:
    """Release camera ownership."""
    try:
        from app.services.mouse_controller import get_mouse_controller
        m_ctrl = get_mouse_controller()
        if m_ctrl.is_enabled:
            m_ctrl.stop()
    except Exception:
        pass

    try:
        from app.api.routes.tracking import get_tracking_service
        t_svc = get_tracking_service()
        if t_svc.is_active:
            t_svc.stop()
    except Exception:
        pass

    camera_manager = get_camera_manager()
    owner_to_release = request.owner if request else None
    success = camera_manager.release_ownership(owner_to_release)
    return CameraOwnershipResponse(
        success=success,
        owner=camera_manager.get_owner(),
        message="Camera ownership released successfully",
    )
