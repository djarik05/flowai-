"""
Hand Tracking Service for GestureFlow AI.

Uses MediaPipe Tasks API (HandLandmarker) for real-time hand landmark detection.
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple

import cv2
import numpy as np

try:
    from mediapipe import Image as mp_Image, ImageFormat as mp_ImageFormat
except ImportError:
    mp_Image = None
    mp_ImageFormat = None

from app.core.config import settings
from app.services.camera_manager import CameraManager

logger = logging.getLogger(__name__)


class TrackingState(str, Enum):
    """Tracking state enumeration."""

    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),       # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17),                                # Palm base
]

HAND_COLORS = [
    (0, 255, 0),    # Green (Hand 1 / Right)
    (255, 128, 0),  # Blue (Hand 2 / Left)
    (0, 0, 255),    # Red
    (255, 255, 0),  # Cyan
]


@dataclass
class Landmark:
    """Normalized hand landmark."""

    index: int
    x: float  # Normalized [0, 1]
    y: float  # Normalized [0, 1]
    z: float  # Normalized depth
    pixel_x: int  # Pixel coordinates
    pixel_y: int


@dataclass
class DetectedHand:
    """Detected hand with landmarks and metadata."""

    hand_id: int
    landmarks: List[Landmark]
    handedness: str = "Unknown"  # "Left" or "Right"
    handedness_confidence: float = 0.0
    bounding_box: Optional[Dict[str, int]] = None  # x, y, width, height in pixels
    timestamp: datetime = field(default_factory=datetime.now)
    gesture_id: Optional[str] = None
    gesture_name: Optional[str] = None
    gesture_confidence: Optional[float] = None
    temporal_gesture_id: Optional[str] = None
    temporal_gesture_name: Optional[str] = None
    temporal_gesture_confidence: Optional[float] = None
    temporal_state: Optional[str] = None
    movement_speed: Optional[float] = None
    movement_direction: Optional[str] = None


@dataclass
class TrackingResult:
    """Complete tracking result for a frame."""

    status: TrackingState = TrackingState.NOT_INITIALIZED
    frame_width: int = 0
    frame_height: int = 0
    hands_detected: int = 0
    hands: List[DetectedHand] = field(default_factory=list)
    temporal_events: List[Any] = field(default_factory=list)
    frame_timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class HandTrackingService:
    """
    Hand tracking service using MediaPipe Tasks HandLandmarker.

    Features:
    - Real-time hand landmark detection
    - Configurable detection parameters
    - Thread-safe result access
    - Automatic camera integration
    - Graceful error handling
    """

    def __init__(
        self,
        camera_manager: Optional[CameraManager] = None,
        model_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the hand tracking service."""
        self._camera_manager = camera_manager
        self._custom_model_path: Optional[Path] = Path(model_path) if model_path else None
        self._landmarker = None
        self._tracking_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._inference_lock = threading.Lock()

        self._status = TrackingState.NOT_INITIALIZED
        self._latest_result: Optional[TrackingResult] = None
        self._latest_annotated_frame: Optional[np.ndarray] = None
        self._result_ready = threading.Event()
        self._result_cond = threading.Condition(self._lock)
        self._result_seq: int = 0
        self._initialized = False
        self._last_error: Optional[str] = None

        # Tracking stats & latency telemetry
        self._frames_processed = 0
        self._total_processing_time = 0.0
        self._last_tracking_time: Optional[datetime] = None
        self._last_timestamp_ms: int = 0
        self._last_processed_seq: int = -1
        self._dropped_frames: int = 0
        self._latest_latency_ms: float = 0.0
        self._avg_inference_ms: float = 0.0
        self._actual_inference_fps: float = 0.0
        self._latency_window: deque = deque(maxlen=30)
        self._inference_fps_window: deque = deque(maxlen=30)

    @property
    def status(self) -> TrackingState:
        """Get current tracking state."""
        with self._lock:
            return self._status

    @property
    def is_active(self) -> bool:
        """Check if tracking is active."""
        with self._lock:
            return self._status == TrackingState.ACTIVE

    @property
    def is_initialized(self) -> bool:
        """Check if detector is initialized."""
        with self._lock:
            return self._initialized and self._landmarker is not None

    def get_status(self) -> Dict[str, Any]:
        """Get detailed tracking status with performance telemetry."""
        with self._lock:
            avg_processing_time = (
                self._total_processing_time / self._frames_processed
                if self._frames_processed > 0 else 0.0
            )
            camera_fps = 0.0
            camera_active = False
            if self._camera_manager:
                camera_active = self._camera_manager.is_healthy()
                camera_fps = getattr(self._camera_manager.get_status(), "actual_fps", 0.0)

            return {
                "state": self._status.value,
                "camera_active": camera_active,
                "detector_initialized": self.is_initialized,
                "last_tracking_time": self._last_tracking_time.isoformat() if self._last_tracking_time else None,
                "frames_processed": self._frames_processed,
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "actual_inference_fps": round(self._actual_inference_fps, 1),
                "camera_fps": round(camera_fps, 1),
                "end_to_end_latency_ms": round(self._latest_latency_ms, 2),
                "frames_dropped": self._dropped_frames,
                "running_mode": "VIDEO",
                "last_error": self._last_error,
            }

    def get_latest_result(self) -> Optional[TrackingResult]:
        """Get the latest tracking result (thread-safe copy)."""
        with self._lock:
            if self._latest_result is not None:
                # Create a copy to avoid mutation
                return TrackingResult(
                    status=self._latest_result.status,
                    frame_width=self._latest_result.frame_width,
                    frame_height=self._latest_result.frame_height,
                    hands_detected=self._latest_result.hands_detected,
                    hands=[DetectedHand(
                        hand_id=h.hand_id,
                        landmarks=[Landmark(
                            index=l.index,
                            x=l.x, y=l.y, z=l.z,
                            pixel_x=l.pixel_x, pixel_y=l.pixel_y
                        ) for l in h.landmarks],
                        handedness=h.handedness,
                        handedness_confidence=h.handedness_confidence,
                        bounding_box=h.bounding_box.copy() if h.bounding_box else None,
                        timestamp=h.timestamp,
                    ) for h in self._latest_result.hands],
                    frame_timestamp=self._latest_result.frame_timestamp,
                    processing_time_ms=self._latest_result.processing_time_ms,
                    error=self._latest_result.error,
                )
            return None

    def wait_for_result(self, timeout: float = 1.0) -> Optional[TrackingResult]:
        """
        Wait for a new tracking result.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Latest tracking result or None if timeout
        """
        if self._result_ready.wait(timeout=timeout):
            return self.get_latest_result()
        return None

    def wait_for_next_result(
        self, last_seq: int = -1, timeout: float = 0.5
    ) -> Tuple[Optional[TrackingResult], int]:
        """
        Wait for a new tracking result newer than last_seq.

        Args:
            last_seq: Sequence number of the previous result
            timeout: Maximum wait time in seconds

        Returns:
            Tuple of (TrackingResult or None, current_seq)
        """
        with self._result_cond:
            if self._result_seq > last_seq and self._latest_result is not None:
                return self.get_latest_result(), self._result_seq
            self._result_cond.wait(timeout=timeout)
            return self.get_latest_result(), self._result_seq

    def get_latest_annotated_frame(self) -> Optional[np.ndarray]:
        """Get the latest processed frame with hand landmark annotations."""
        with self._lock:
            if self._latest_annotated_frame is not None:
                return self._latest_annotated_frame.copy()
            return None

    def annotate_frame(
        self,
        frame: np.ndarray,
        result: Optional[TrackingResult] = None,
        fps: float = 0.0,
    ) -> np.ndarray:
        """Draw 21 landmarks and skeleton lines on frame (clean, zero raster text overlay)."""
        annotated = frame.copy()

        if result is None:
            result = self.get_latest_result()

        if result and result.hands:
            for idx, hand in enumerate(result.hands):
                color = HAND_COLORS[idx % len(HAND_COLORS)]
                pts = [(lm.pixel_x, lm.pixel_y) for lm in hand.landmarks]

                for i, j in HAND_CONNECTIONS:
                    if i < len(pts) and j < len(pts):
                        try:
                            cv2.line(annotated, pts[i], pts[j], color, 2)
                        except Exception:
                            pass

                for px, py in pts:
                    try:
                        cv2.circle(annotated, (px, py), 4, color, -1)
                        cv2.circle(annotated, (px, py), 4, (255, 255, 255), 1)
                    except Exception:
                        pass

        return annotated

    def initialize(self) -> bool:
        """
        Initialize the MediaPipe HandLandmarker.

        Returns:
            True if initialized successfully
        """
        with self._lock:
            if self._initialized and self._landmarker is not None:
                logger.warning("Hand tracking already initialized")
                return True

            self._status = TrackingState.INITIALIZING
            self._last_error = None

            try:
                # Resolve and validate model path
                model_asset_path = self._get_model_path()

                # Import MediaPipe Tasks
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision

                # Create HandLandmarker options with VIDEO mode for sequential temporal tracking
                base_options = python.BaseOptions(
                    model_asset_path=model_asset_path
                )

                try:
                    running_mode = vision.RunningMode.VIDEO
                except AttributeError:
                    running_mode = vision.RunningMode.IMAGE

                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    running_mode=running_mode,
                    num_hands=settings.tracking_max_hands,
                    min_hand_detection_confidence=settings.tracking_detection_confidence,
                    min_hand_presence_confidence=settings.tracking_tracking_confidence,
                    min_tracking_confidence=settings.tracking_tracking_confidence,
                )

                self._landmarker = vision.HandLandmarker.create_from_options(options)
                self._initialized = True
                self._status = TrackingState.ACTIVE
                logger.info(
                    "Hand tracking initialized (Tasks API %s mode): model=%s, max_hands=%d, detection_conf=%.2f, tracking_conf=%.2f",
                    "VIDEO" if running_mode == vision.RunningMode.VIDEO else "IMAGE",
                    model_asset_path,
                    settings.tracking_max_hands,
                    settings.tracking_detection_confidence,
                    settings.tracking_tracking_confidence,
                )
                return True

            except ImportError as e:
                error_msg = f"MediaPipe Tasks not available: {e}"
                logger.error(error_msg)
                self._status = TrackingState.ERROR
                self._last_error = error_msg
                return False
            except Exception as e:
                error_msg = f"Failed to initialize hand tracking: {e}"
                logger.error(error_msg, exc_info=True)
                self._status = TrackingState.ERROR
                self._last_error = error_msg
                return False

    def _get_model_path(self) -> str:
        """Get the resolved absolute path to the hand landmarker model.

        Resolution order:
        1. Custom model_path passed to constructor (if any).
        2. Configured settings.resolved_model_path (HAND_LANDMARKER_MODEL_PATH or default).

        Relative paths are resolved relative to the backend project directory.

        Raises:
            FileNotFoundError: If the model file is missing, not a regular file,
                or empty.
        """
        if self._custom_model_path is not None:
            model_path = self._custom_model_path
            if not model_path.is_absolute():
                model_path = (settings.backend_dir / model_path).resolve()
        else:
            model_path = settings.resolved_model_path

        if not model_path.exists():
            raise FileNotFoundError(
                f"Hand landmarker model not found at: {model_path}\n"
                "Please download the official model file to: backend/models/hand_landmarker.task\n"
                "Official download URL: "
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            )

        if not model_path.is_file():
            raise FileNotFoundError(
                f"Hand landmarker model path is not a file: {model_path}"
            )

        if model_path.stat().st_size == 0:
            raise FileNotFoundError(
                f"Hand landmarker model file is empty (0 bytes): {model_path}"
            )

        return str(model_path.resolve())

    def start(self, camera_manager: Optional[CameraManager] = None) -> bool:
        """
        Start the tracking pipeline.

        Args:
            camera_manager: Optional camera manager to use

        Returns:
            True if started successfully
        """
        with self._lock:
            if self._tracking_thread is not None and self._tracking_thread.is_alive():
                logger.warning("Tracking already active")
                return True

            if camera_manager:
                self._camera_manager = camera_manager

            if not self._camera_manager:
                error_msg = "No camera manager provided"
                logger.error(error_msg)
                self._status = TrackingState.ERROR
                self._last_error = error_msg
                return False

            # Initialize detector if needed
            if not self.is_initialized:
                if not self.initialize():
                    return False

            # Start camera if not already capturing
            cam_status = self._camera_manager.get_status()
            if not cam_status.is_capturing and not self._camera_manager.is_healthy():
                if not self._camera_manager.start():
                    error_msg = "Failed to start camera"
                    logger.error(error_msg)
                    self._status = TrackingState.ERROR
                    self._last_error = error_msg
                    return False

            # Start tracking thread
            self._stop_event.clear()
            self._tracking_thread = threading.Thread(
                target=self._tracking_loop,
                name="HandTracking",
                daemon=True,
            )
            self._tracking_thread.start()

            self._status = TrackingState.ACTIVE
            logger.info("Hand tracking started")
            return True

    def stop(self) -> bool:
        """
        Stop tracking and release resources cleanly.
        Thread-safe, idempotent, and guarantees no in-flight futures
        are scheduled on MediaPipe tasks during or after shutdown.

        Returns:
            True if stopped successfully
        """
        with self._lock:
            if self._status in (TrackingState.NOT_INITIALIZED, TrackingState.STOPPED):
                logger.debug("Tracking already stopped")
                return True

            logger.info("Stopping hand tracking")
            self._status = TrackingState.STOPPED
            self._stop_event.set()

        # Wake up any blocked camera wait
        if self._camera_manager and hasattr(self._camera_manager, "_frame_ready"):
            self._camera_manager._frame_ready.set()

        # Wait for thread outside of lock to avoid deadlock
        if self._tracking_thread and self._tracking_thread.is_alive():
            self._tracking_thread.join(timeout=3.0)
            if self._tracking_thread.is_alive():
                logger.warning("Tracking thread did not stop gracefully")

        with self._inference_lock:
            with self._lock:
                # Release detector under inference lock to ensure zero concurrent execution
                if self._landmarker:
                    try:
                        self._landmarker.close()
                    except Exception as e:
                        logger.error("Error closing MediaPipe landmarker: %s", e)
                    finally:
                        self._landmarker = None

                self._initialized = False
                self._status = TrackingState.STOPPED
                self._latest_result = None
                self._latest_annotated_frame = None
                self._result_ready.clear()

                try:
                    from app.services.mouse_controller import get_mouse_controller
                    get_mouse_controller().on_tracking_loss()
                except Exception:
                    pass

                logger.info("Hand tracking stopped")
                return True

    def _update_telemetry(self, processing_time_ms: float, latency_ms: float) -> None:
        """Update rolling telemetry metrics."""
        self._latest_latency_ms = latency_ms
        self._latency_window.append(latency_ms)

        now = time.time()
        self._inference_fps_window.append(now)
        if len(self._inference_fps_window) > 1:
            duration = self._inference_fps_window[-1] - self._inference_fps_window[0]
            if duration > 0:
                self._actual_inference_fps = round((len(self._inference_fps_window) - 1) / duration, 1)

        if self._avg_inference_ms > 0:
            self._avg_inference_ms = round(processing_time_ms * 0.15 + self._avg_inference_ms * 0.85, 2)
        else:
            self._avg_inference_ms = round(processing_time_ms, 2)

    def _tracking_loop(self) -> None:
        """Background tracking loop (runs in separate worker thread with latest-frame-wins strategy)."""
        logger.debug("Tracking loop started")
        last_seq = -1

        while not self._stop_event.is_set():
            try:
                # Latest-frame-wins: wait on frame signal from camera
                if self._camera_manager:
                    if not self._camera_manager._frame_ready.wait(timeout=0.1):
                        continue
                    self._camera_manager._frame_ready.clear()

                    # Extract metadata without copy
                    frame, capture_time, seq = self._camera_manager.get_latest_frame_with_metadata()
                else:
                    frame = None
                    capture_time = time.time()
                    seq = 0

                if frame is None or seq == last_seq:
                    continue

                # Record dropped frames from camera queue if inference took longer than a camera tick
                if last_seq != -1 and seq > last_seq + 1:
                    self._dropped_frames += (seq - last_seq - 1)
                last_seq = seq

                # Process frame
                result = self._process_frame(frame, capture_time=capture_time)
                annotated = self.annotate_frame(frame, result, fps=self._actual_inference_fps)

                # Update latest result (thread-safe)
                with self._lock:
                    self._latest_result = result
                    self._latest_annotated_frame = annotated
                    self._last_tracking_time = result.frame_timestamp
                    self._frames_processed += 1
                    self._total_processing_time += result.processing_time_ms
                    self._result_seq += 1

                # Signal result ready
                self._result_ready.set()
                with self._result_cond:
                    self._result_cond.notify_all()

            except Exception as e:
                logger.error("Error in tracking loop: %s", e, exc_info=True)
                with self._lock:
                    self._status = TrackingState.ERROR
                    self._last_error = f"Tracking error: {e}"
                break

        logger.debug("Tracking loop ended")

    def _process_frame(self, frame: np.ndarray, capture_time: Optional[float] = None) -> TrackingResult:
        """
        Process a single frame for hand landmarks using MediaPipe Tasks API.

        Args:
            frame: Input frame (BGR format from OpenCV)
            capture_time: System timestamp (time.time()) when camera captured frame

        Returns:
            TrackingResult with detected hands
        """
        start_time = time.perf_counter()
        frame_timestamp = datetime.now()

        frame_height, frame_width = frame.shape[:2]

        try:
            if self._stop_event.is_set() or self._status == TrackingState.STOPPED:
                return TrackingResult(
                    status=TrackingState.STOPPED,
                    frame_width=frame_width,
                    frame_height=frame_height,
                    frame_timestamp=frame_timestamp,
                )

            if self._landmarker is None:
                return TrackingResult(
                    status=TrackingState.ERROR,
                    frame_width=frame_width,
                    frame_height=frame_height,
                    frame_timestamp=frame_timestamp,
                    error="Detector not initialized",
                )

            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create MediaPipe Image
            if mp_Image is not None and mp_ImageFormat is not None:
                mp_image = mp_Image(image_format=mp_ImageFormat.SRGB, data=rgb_frame)
            else:
                from mediapipe import Image, ImageFormat
                mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)

            # Monotonic timestamp for VIDEO mode
            curr_timestamp_ms = int(time.time() * 1000)
            if curr_timestamp_ms <= self._last_timestamp_ms:
                curr_timestamp_ms = self._last_timestamp_ms + 1
            self._last_timestamp_ms = curr_timestamp_ms

            # Process with MediaPipe safely guarded by inference lock
            with self._inference_lock:
                if self._stop_event.is_set() or self._landmarker is None:
                    return TrackingResult(
                        status=TrackingState.STOPPED,
                        frame_width=frame_width,
                        frame_height=frame_height,
                        frame_timestamp=frame_timestamp,
                    )
                if hasattr(self._landmarker, "detect_for_video"):
                    results = self._landmarker.detect_for_video(mp_image, curr_timestamp_ms)
                else:
                    results = self._landmarker.detect(mp_image)

            hands = []
            temporal_events: List[Any] = []
            if results and results.hand_landmarks:
                for hand_idx, (hand_landmarks, handedness) in enumerate(
                    zip(results.hand_landmarks, results.handedness)
                ):
                    # Extract handedness
                    hand_label = "Unknown"
                    hand_confidence = 0.0
                    if handedness:
                        hand_label = handedness[0].category_name or "Unknown"
                        hand_confidence = handedness[0].score or 0.0

                    # Extract landmarks
                    landmarks = []
                    pixel_coords = []

                    for idx, landmark in enumerate(hand_landmarks):
                        # Normalized coordinates
                        x = max(0.0, min(1.0, landmark.x))
                        y = max(0.0, min(1.0, landmark.y))
                        z = landmark.z

                        # Pixel coordinates
                        pixel_x = int(x * frame_width)
                        pixel_y = int(y * frame_height)

                        landmarks.append(Landmark(
                            index=idx,
                            x=x,
                            y=y,
                            z=z,
                            pixel_x=pixel_x,
                            pixel_y=pixel_y,
                        ))
                        pixel_coords.append((pixel_x, pixel_y))

                    # Calculate bounding box
                    if pixel_coords:
                        xs = [p[0] for p in pixel_coords]
                        ys = [p[1] for p in pixel_coords]
                        bounding_box = {
                            "x": min(xs),
                            "y": min(ys),
                            "width": max(xs) - min(xs),
                            "height": max(ys) - min(ys),
                        }
                    else:
                        bounding_box = None

                    # Real-time static gesture classification
                    gesture_id = None
                    gesture_name = None
                    gesture_conf = None
                    try:
                        from app.services.classifier_service import get_classifier_service
                        cls_svc = get_classifier_service()
                        if cls_svc.is_model_loaded:
                            pred = cls_svc.predict_landmarks(landmarks, handedness=hand_label)
                            if pred.is_recognized:
                                gesture_id = pred.gesture_id
                                gesture_name = pred.gesture_name
                                gesture_conf = pred.confidence
                    except Exception:
                        pass

                    # Real-time Phase 5 temporal gesture recognition
                    temporal_gid = None
                    temporal_gname = None
                    temporal_conf = None
                    temporal_state = None
                    movement_spd = None
                    movement_dir = None

                    try:
                        from app.services.temporal import get_temporal_engine, get_temporal_dataset_service
                        t_engine = get_temporal_engine()
                        event, telem = t_engine.process_hand(
                            hand_id=hand_idx,
                            handedness=hand_label,
                            landmarks=landmarks,
                            timestamp=frame_timestamp.timestamp(),
                            static_gesture_id=gesture_id,
                            static_gesture_name=gesture_name,
                        )
                        temporal_state = telem.state.value if hasattr(telem.state, "value") else str(telem.state)
                        movement_spd = telem.velocity.get("speed", 0.0)
                        movement_dir = telem.direction

                        if event:
                            temporal_gid = event.gesture_id
                            temporal_gname = event.gesture_name
                            temporal_conf = event.confidence
                            temporal_events.append(event)

                        tds = get_temporal_dataset_service()
                        if tds.get_collection_status().is_collecting:
                            tds.record_frame(landmarks, timestamp=frame_timestamp.timestamp(), handedness=hand_label)
                    except Exception as te:
                        logger.debug("Temporal tracking hook exception: %s", te)

                    hands.append(DetectedHand(
                        hand_id=hand_idx,
                        landmarks=landmarks,
                        handedness=hand_label,
                        handedness_confidence=hand_confidence,
                        bounding_box=bounding_box,
                        timestamp=frame_timestamp,
                        gesture_id=gesture_id,
                        gesture_name=gesture_name,
                        gesture_confidence=gesture_conf,
                        temporal_gesture_id=temporal_gid,
                        temporal_gesture_name=temporal_gname,
                        temporal_gesture_confidence=temporal_conf,
                        temporal_state=temporal_state,
                        movement_speed=movement_spd,
                        movement_direction=movement_dir,
                    ))

            if hands:
                try:
                    from app.services.mouse_controller import get_mouse_controller
                    m_ctrl = get_mouse_controller()
                    if m_ctrl.is_enabled and len(hands[0].landmarks) > 8:
                        index_tip = hands[0].landmarks[8]
                        thumb_tip = hands[0].landmarks[4] if len(hands[0].landmarks) > 4 else None
                        middle_tip = hands[0].landmarks[12] if len(hands[0].landmarks) > 12 else None
                        p_dist = None
                        rp_dist = None
                        tx = None
                        ty = None
                        mx = None
                        my = None
                        if thumb_tip:
                            p_dist = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
                            tx = thumb_tip.x
                            ty = thumb_tip.y
                            if middle_tip:
                                rp_dist = math.hypot(middle_tip.x - thumb_tip.x, middle_tip.y - thumb_tip.y)
                                mx = middle_tip.x
                                my = middle_tip.y
                        m_ctrl.on_landmark_point(
                            index_tip.x,
                            index_tip.y,
                            capture_time=capture_time or time.time(),
                            pinch_distance=p_dist,
                            thumb_x=tx,
                            thumb_y=ty,
                            right_pinch_distance=rp_dist,
                            middle_x=mx,
                            middle_y=my,
                        )
                except Exception:
                    pass
            else:
                try:
                    from app.services.temporal import get_temporal_engine
                    get_temporal_engine().process_no_hands(timestamp=frame_timestamp.timestamp())
                except Exception:
                    pass
                try:
                    from app.services.mouse_controller import get_mouse_controller
                    m_ctrl = get_mouse_controller()
                    if m_ctrl.is_enabled:
                        m_ctrl.on_tracking_loss()
                except Exception:
                    pass

            processing_time = (time.perf_counter() - start_time) * 1000.0  # ms
            latency_ms = (time.time() - capture_time) * 1000.0 if capture_time else processing_time

            self._update_telemetry(processing_time, latency_ms)

            return TrackingResult(
                status=TrackingState.ACTIVE,
                frame_width=frame_width,
                frame_height=frame_height,
                hands_detected=len(hands),
                hands=hands,
                temporal_events=temporal_events,
                frame_timestamp=frame_timestamp,
                processing_time_ms=round(processing_time, 2),
            )

        except RuntimeError as e:
            processing_time = (time.perf_counter() - start_time) * 1000.0
            if "cannot schedule new futures after shutdown" in str(e).lower() or "shutdown" in str(e).lower():
                logger.debug("MediaPipe Tasks executor shutdown caught during stop: %s", e)
                return TrackingResult(
                    status=TrackingState.STOPPED,
                    frame_width=frame_width,
                    frame_height=frame_height,
                    frame_timestamp=frame_timestamp,
                    processing_time_ms=round(processing_time, 2),
                    error="Detector shut down",
                )
            logger.error("Runtime error in frame processing: %s", e, exc_info=True)
            return TrackingResult(
                status=TrackingState.ERROR,
                frame_width=frame_width,
                frame_height=frame_height,
                frame_timestamp=frame_timestamp,
                processing_time_ms=round(processing_time, 2),
                error=str(e),
            )
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000.0
            logger.error("Error processing frame: %s", e, exc_info=True)
            return TrackingResult(
                status=TrackingState.ERROR,
                frame_width=frame_width,
                frame_height=frame_height,
                frame_timestamp=frame_timestamp,
                processing_time_ms=round(processing_time, 2),
                error=str(e),
            )

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            if hasattr(self, "_stop_event") and self._stop_event is not None:
                self._stop_event.set()
            if hasattr(self, "_landmarker") and self._landmarker is not None:
                try:
                    self._landmarker.close()
                except Exception:
                    pass
                self._landmarker = None
        except Exception:
            pass