"""
Dataset Collector Service for GestureFlow AI.

Manages automated live sample capture sessions using existing CameraManager
and HandTrackingService. Captures, labels, and persists 21-point hand landmark data.
"""

import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Optional

from app.schemas.dataset import (
    CollectionStatusResponse,
    DatasetSample,
    LandmarkCoord,
)
from app.services.camera_manager import CameraManager
from app.services.dataset_service import DatasetService
from app.services.hand_tracking import HandTrackingService

logger = logging.getLogger(__name__)


class DatasetCollector:
    """
    Automated live dataset collector for hand gestures.

    Reuses existing CameraManager and HandTrackingService to capture
    and label MediaPipe 21 hand landmarks per frame without duplication.
    """

    def __init__(
        self,
        dataset_service: DatasetService,
        camera_manager: Optional[CameraManager] = None,
        tracking_service: Optional[HandTrackingService] = None,
    ) -> None:
        """Initialize the dataset collector."""
        self._lock = threading.RLock()
        self._dataset_service = dataset_service
        self._camera_manager = camera_manager or CameraManager()
        self._tracking_service = tracking_service or HandTrackingService(self._camera_manager)

        # Session state
        self._status = "idle"  # idle, collecting, paused, completed, cancelled, error
        self._session_id: Optional[str] = None
        self._gesture_id: Optional[str] = None
        self._gesture_name: Optional[str] = None
        self._target_samples: int = 0
        self._collected_samples: int = 0
        self._sample_interval_s: float = 0.15
        self._last_error: Optional[str] = None
        self._last_handedness: str = "Unknown"
        self._hand_detected: bool = False
        self._current_fps: float = 30.0

        # Background thread control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

    @property
    def is_active(self) -> bool:
        """Check if collection is currently running or paused."""
        with self._lock:
            return self._status in ("starting", "collecting", "paused", "stopping")

    def get_status(self) -> CollectionStatusResponse:
        """Get current collection session telemetry and progress."""
        with self._lock:
            progress = 0.0
            if self._target_samples > 0:
                progress = min(100.0, round((self._collected_samples / self._target_samples) * 100, 1))

            return CollectionStatusResponse(
                session_id=self._session_id,
                gesture_id=self._gesture_id,
                gesture_name=self._gesture_name,
                status=self._status,
                state=self._status,
                target_samples=self._target_samples,
                collected_samples=self._collected_samples,
                progress_percent=progress,
                progress_pct=progress,
                hand_detected=self._hand_detected,
                handedness=self._last_handedness,
                fps=self._current_fps,
                last_error=self._last_error,
            )

    def start_collection(
        self,
        gesture_id: str,
        gesture_name: str,
        target_samples: int = 50,
        sample_interval_ms: int = 150,
        camera_index: Optional[int] = None,
    ) -> bool:
        """
        Start an automated dataset collection session.

        Args:
            gesture_id: Gesture ID being recorded
            gesture_name: Display name of the gesture
            target_samples: Number of samples to collect
            sample_interval_ms: Milliseconds between saved samples
            camera_index: Optional camera index to capture from

        Returns:
            True if collection started successfully
        """
        with self._lock:
            if self.is_active:
                logger.warning("Collection session already active (%s, state=%s)", self._session_id, self._status)
                return False

            self._status = "starting"

            # Ensure camera & tracking pipeline are running
            if not self._tracking_service.is_active:
                logger.info("Starting hand tracking for dataset collection")
                if not self._tracking_service.start(self._camera_manager):
                    self._status = "error"
                    self._last_error = self._tracking_service.get_status().get("last_error", "Camera failed to start")
                    return False

            self._session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            self._gesture_id = gesture_id
            self._gesture_name = gesture_name
            self._target_samples = target_samples
            self._collected_samples = 0
            self._sample_interval_s = max(0.03, sample_interval_ms / 1000.0)
            self._last_error = None
            self._status = "collecting"

            self._stop_event.clear()
            self._pause_event.clear()

            self._thread = threading.Thread(
                target=self._run_collection,
                name="DatasetCollectorThread",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                "Started dataset collection for %s (%s): target=%d, interval=%.2fs",
                gesture_name,
                gesture_id,
                target_samples,
                self._sample_interval_s,
            )
            return True

    def pause_collection(self) -> bool:
        """Pause live sample recording."""
        with self._lock:
            if self._status != "collecting":
                return False
            self._pause_event.set()
            self._status = "paused"
            logger.info("Paused collection session %s", self._session_id)
            return True

    def resume_collection(self) -> bool:
        """Resume paused sample recording."""
        with self._lock:
            if self._status != "paused":
                return False
            self._pause_event.clear()
            self._status = "collecting"
            logger.info("Resumed collection session %s", self._session_id)
            return True

    def stop_collection(self) -> bool:
        """Cancel and stop the current collection session."""
        with self._lock:
            if not self.is_active:
                return True

            self._stop_event.set()
            self._pause_event.clear()
            self._status = "stopping"

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.5)

        with self._lock:
            if self._status == "stopping":
                self._status = "cancelled"

        logger.info("Stopped collection session %s", self._session_id)
        return True

    def _run_collection(self) -> None:
        """Background thread capture loop with reliable persistence and validation."""
        logger.debug("Collection capture loop started for session %s", self._session_id)
        last_capture_time = 0.0
        last_seq = -1

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.05)
                continue

            try:
                # Wait for next frame result with monotonic sequence check
                raw_res = None
                if hasattr(self._tracking_service, "wait_for_next_result"):
                    res_tuple = self._tracking_service.wait_for_next_result(last_seq=last_seq, timeout=0.2)
                    if isinstance(res_tuple, tuple) and len(res_tuple) == 2:
                        result, seq = res_tuple
                        if result is None or seq == last_seq:
                            continue
                        last_seq = seq
                    else:
                        result = res_tuple
                else:
                    result = self._tracking_service.wait_for_result(timeout=0.2)

                if result is None:
                    continue

                with self._lock:
                    proc_time = getattr(result, "processing_time_ms", 0)
                    if isinstance(proc_time, (int, float)) and proc_time > 0:
                        self._current_fps = round(1000.0 / proc_time, 1)

                    # Update hand detection telemetry
                    hands = getattr(result, "hands", None)
                    if not hands or not isinstance(hands, list) or len(hands) == 0:
                        self._hand_detected = False
                        time.sleep(0.01)
                        continue

                    self._hand_detected = True
                    primary_hand = hands[0]
                    self._last_handedness = getattr(primary_hand, "handedness", "Unknown")

                    # Rate limit sample captures according to configured interval
                    now = time.time()
                    if (now - last_capture_time) < self._sample_interval_s:
                        time.sleep(0.005)
                        continue

                    # Validate primary hand landmarks
                    lm_list = getattr(primary_hand, "landmarks", [])
                    if not lm_list or len(lm_list) != 21:
                        logger.warning("Rejecting frame: hand detected but landmark count is %d (expected 21)", len(lm_list))
                        continue

                    # Validate coordinate values
                    import math
                    valid_coords = True
                    landmarks: List[LandmarkCoord] = []
                    for lm in lm_list:
                        if not math.isfinite(lm.x) or not math.isfinite(lm.y) or (lm.z is not None and not math.isfinite(lm.z)):
                            valid_coords = False
                            break
                        landmarks.append(
                            LandmarkCoord(
                                index=lm.index,
                                x=max(0.0, min(1.0, float(lm.x))),
                                y=max(0.0, min(1.0, float(lm.y))),
                                z=float(lm.z) if lm.z is not None else 0.0,
                            )
                        )

                    if not valid_coords or len(landmarks) != 21:
                        logger.warning("Rejecting frame: non-finite or corrupted landmark coordinates")
                        continue

                    # If secondary hand is present, preserve it in features
                    features_dict = None
                    if len(hands) > 1:
                        secondary_hand = hands[1]
                        sec_lms = getattr(secondary_hand, "landmarks", [])
                        if len(sec_lms) == 21:
                            features_dict = {
                                "secondary_hand": {
                                    "handedness": getattr(secondary_hand, "handedness", "Unknown"),
                                    "confidence": getattr(secondary_hand, "handedness_confidence", 0.0),
                                    "landmarks": [
                                        {"index": s_lm.index, "x": float(s_lm.x), "y": float(s_lm.y), "z": float(s_lm.z)}
                                        for s_lm in sec_lms
                                    ]
                                }
                            }

                    sample_id = f"s_{int(now * 1000)}_{uuid.uuid4().hex[:6]}"
                    sample = DatasetSample(
                        sample_id=sample_id,
                        gesture_id=str(self._gesture_id),
                        gesture_name=str(self._gesture_name),
                        timestamp=datetime.now().isoformat(),
                        handedness=str(primary_hand.handedness),
                        handedness_confidence=float(getattr(primary_hand, "handedness_confidence", 1.0)),
                        landmarks=landmarks,
                        session_id=str(self._session_id),
                        features=features_dict,
                    )

                    try:
                        self._dataset_service.save_sample(sample)
                        self._collected_samples += 1
                        last_capture_time = now
                        logger.info(
                            "Sample captured and persisted successfully (%d/%d): id=%s, gesture=%s",
                            self._collected_samples,
                            self._target_samples,
                            sample_id,
                            self._gesture_id,
                        )
                    except Exception as exc:
                        logger.error("Failed to persist sample %s: %s", sample_id, exc)

                    # Check completion
                    if self._collected_samples >= self._target_samples:
                        self._status = "completed"
                        logger.info(
                            "Collection session %s completed: %d samples saved for %s",
                            self._session_id,
                            self._collected_samples,
                            self._gesture_name,
                        )
                        break

            except Exception as e:
                logger.error("Error in collection capture loop: %s", e, exc_info=True)
                with self._lock:
                    self._status = "error"
                    self._last_error = str(e)
                break

        logger.debug("Collection capture loop exited with status: %s", self._status)
