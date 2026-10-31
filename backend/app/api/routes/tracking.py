"""
Tracking routes for GestureFlow AI backend.

Provides hand tracking management and result endpoints.
"""

import asyncio
import numpy as np
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.tracking import (
    TrackingConfigRequest,
    TrackingConfigResponse,
    TrackingResult,
    TrackingStatusResponse,
)
from app.schemas.common import ErrorResponse
from app.core.lifecycle import get_application_service

router = APIRouter(prefix="/tracking", tags=["Tracking"])


def get_tracking_service():
    """Get singleton tracking service from application service."""
    app_service = get_application_service()
    tracking_comp = app_service.get_component_status("tracking")

    from app.services.hand_tracking import HandTrackingService
    from app.api.routes.camera import get_camera_manager

    if tracking_comp is None:
        return HandTrackingService(get_camera_manager())

    instance = tracking_comp.metadata.get("instance")
    if instance is None:
        camera_manager = get_camera_manager()
        instance = HandTrackingService(camera_manager)
        tracking_comp.metadata["instance"] = instance
        tracking_comp.metadata["camera_manager"] = camera_manager

    return instance


@router.get(
    "/status",
    response_model=TrackingStatusResponse,
    summary="Get tracking status",
    description="Returns current tracking state, detector status, and statistics.",
    responses={
        200: {"description": "Tracking status retrieved successfully"},
        503: {"description": "Service not initialized"},
    },
)
async def get_tracking_status() -> TrackingStatusResponse:
    """
    Get tracking service status.

    Returns information about the tracking state, detector initialization,
    camera status, and processing statistics.
    """
    tracking_service = get_tracking_service()
    status_data = tracking_service.get_status()

    return TrackingStatusResponse(
        state=status_data["state"],
        camera_active=status_data["camera_active"],
        detector_initialized=status_data["detector_initialized"],
        last_tracking_time=status_data["last_tracking_time"],
        frames_processed=status_data["frames_processed"],
        avg_processing_time_ms=status_data["avg_processing_time_ms"],
        actual_inference_fps=status_data.get("actual_inference_fps", 0.0),
        camera_fps=status_data.get("camera_fps", 0.0),
        end_to_end_latency_ms=status_data.get("end_to_end_latency_ms", 0.0),
        frames_dropped=status_data.get("frames_dropped", 0),
        running_mode=status_data.get("running_mode", "VIDEO"),
        last_error=status_data["last_error"],
    )


@router.post(
    "/start",
    response_model=TrackingConfigResponse,
    summary="Start hand tracking",
    description="Starts the hand tracking pipeline with current or provided configuration.",
    responses={
        200: {"description": "Tracking started successfully"},
        400: {"description": "Invalid configuration"},
        409: {"description": "Tracking already active"},
        500: {"description": "Tracking initialization failed"},
        503: {"description": "Camera unavailable"},
    },
)
async def start_tracking(config: TrackingConfigRequest) -> TrackingConfigResponse:
    """
    Start hand tracking.

    Initializes the MediaPipe detector (if not already) and starts
    the camera capture and tracking pipeline.
    """
    tracking_service = get_tracking_service()

    # Apply configuration if provided (requires detector re-initialization)
    if config.max_hands is not None or config.detection_confidence is not None or \
       config.tracking_confidence is not None or config.model_complexity is not None:
        # Stop current tracking to reconfigure
        if tracking_service.is_active:
            tracking_service.stop()
        # Update settings for next initialization
        from app.core.config import settings as app_settings
        if config.max_hands is not None:
            app_settings.tracking_max_hands = config.max_hands
        if config.detection_confidence is not None:
            app_settings.tracking_detection_confidence = config.detection_confidence
        if config.tracking_confidence is not None:
            app_settings.tracking_tracking_confidence = config.tracking_confidence
        if config.model_complexity is not None:
            app_settings.tracking_model_complexity = config.model_complexity

    success = tracking_service.start()

    if success:
        app_service = get_application_service()
        app_service.set_component_state(
            "tracking",
            "running",
            metadata={"instance": tracking_service},
        )
        return TrackingConfigResponse(
            success=True,
            message="Hand tracking started successfully",
            applied_config=config,
        )
    else:
        app_service = get_application_service()
        app_service.set_component_state(
            "tracking",
            "error",
            error=tracking_service.get_status().get("last_error", "Unknown error"),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error={
                    "code": "TRACKING_START_FAILED",
                    "message": tracking_service.get_status().get("last_error", "Failed to start tracking"),
                }
            ).model_dump(),
        )


@router.post(
    "/stop",
    response_model=TrackingConfigResponse,
    summary="Stop hand tracking",
    description="Stops hand tracking and releases tracking resources.",
    responses={
        200: {"description": "Tracking stopped successfully"},
        409: {"description": "Tracking not active"},
    },
)
async def stop_tracking() -> TrackingConfigResponse:
    """
    Stop hand tracking.

    Stops the tracking pipeline and releases the MediaPipe detector.
    Camera capture continues unless explicitly stopped.
    """
    tracking_service = get_tracking_service()
    success = tracking_service.stop()

    app_service = get_application_service()
    app_service.set_component_state("tracking", "not_initialized")

    return TrackingConfigResponse(
        success=success,
        message="Hand tracking stopped successfully" if success else "Tracking was already stopped",
    )


@router.get(
    "/result",
    response_model=TrackingResult,
    summary="Get latest tracking result",
    description="Returns the latest structured hand tracking result.",
    responses={
        200: {"description": "Tracking result retrieved successfully"},
        204: {"description": "No result available yet"},
        503: {"description": "Service not initialized"},
    },
)
async def get_tracking_result() -> TrackingResult:
    """
    Get latest tracking result.

    Returns the most recent hand tracking result with landmarks,
    handedness, and timing information.
    Does not start a new capture session.
    """
    tracking_service = get_tracking_service()
    result = tracking_service.get_latest_result()

    if result is None:
        # Return empty result with status indicating no data yet
        return TrackingResult(
            status="not_initialized" if not tracking_service.is_active else "active",
            frame_width=0,
            frame_height=0,
            hands_detected=0,
            hands=[],
            processing_time_ms=0.0,
            error="No tracking result available yet" if not tracking_service.is_active else None,
        )

    return result


@router.get(
    "/stream",
    summary="Live video stream with MediaPipe hand landmark tracking",
    description="Streams MJPEG video feed with real-time hand landmarks, skeletons, and HUD.",
    responses={
        200: {
            "content": {"multipart/x-mixed-replace; boundary=frame": {}},
            "description": "Continuous MJPEG multipart video stream",
        }
    },
)
async def stream_tracking_video(
    max_frames: int | None = None,
    camera_index: int | None = None,
):
    """Stream live webcam frames with MediaPipe hand landmark tracking."""
    tracking_service = get_tracking_service()
    if camera_index is not None and tracking_service._camera_manager:
        current_idx = tracking_service._camera_manager.get_status().camera_index
        if current_idx != camera_index and tracking_service.is_active:
            tracking_service.stop()
            from app.core.config import settings as app_settings
            app_settings.camera_index = camera_index
            tracking_service.start()
        elif not tracking_service.is_active:
            from app.core.config import settings as app_settings
            app_settings.camera_index = camera_index
            tracking_service.start()
    elif not tracking_service.is_active:
        tracking_service.start()

    async def generate_frames():
        sent = 0
        while True:
            if max_frames is not None and sent >= max_frames:
                break
            frame = tracking_service.get_latest_annotated_frame()
            if frame is None:
                # Fallback to blank frame if waiting
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            try:
                import cv2
                ret, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + jpeg.tobytes()
                        + b"\r\n"
                    )
                    sent += 1
            except Exception:
                pass
            await asyncio.sleep(0.033)

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )