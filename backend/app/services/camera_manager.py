"""
Webcam Manager Service for GestureFlow AI.

Provides robust camera capture with threading, error handling,
and resource management.
"""

import logging
import platform
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple

import cv2
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class CameraState(str, Enum):
    """Camera state enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CAPTURING = "capturing"
    ERROR = "error"


@dataclass
class CameraInfo:
    """Camera device information."""

    index: int
    name: str = ""
    width: int = 0
    height: int = 0
    fps: float = 0.0
    backend: str = ""
    available: bool = False


@dataclass
class CameraStatus:
    """Current camera status."""

    state: CameraState = CameraState.DISCONNECTED
    camera_index: int = 0
    actual_width: int = 0
    actual_height: int = 0
    actual_fps: float = 0.0
    backend: str = ""
    is_capturing: bool = False
    last_frame_time: Optional[datetime] = None
    frames_captured: int = 0
    frames_dropped: int = 0
    last_error: Optional[str] = None
    devices: List[CameraInfo] = field(default_factory=list)
    owner: str = "none"


class CameraManager:
    """
    Manages webcam capture with background thread.

    Features:
    - Thread-safe frame capture
    - Automatic camera discovery
    - Configurable resolution and FPS
    - Frame mirroring support
    - Graceful error handling and recovery
    - Resource cleanup on shutdown
    """

    def __init__(self) -> None:
        """Initialize the camera manager."""
        self._lock = threading.RLock()
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._camera: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_capture_time: float = 0.0
        self._frame_seq: int = 0
        self._fps_window: deque = deque(maxlen=30)
        self._frame_ready = threading.Event()
        self._status = CameraStatus()
        self._initialized = False
        self._owner: str = "none"

    @staticmethod
    def _get_windows_camera_names() -> List[str]:
        """Query Windows PnP / WMI for physical camera device friendly names."""
        if platform.system() != "Windows":
            return []
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                'Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -in @("Camera", "Image") } | Select-Object -ExpandProperty Caption'
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                names = [line.strip() for line in res.stdout.splitlines() if line.strip()]
                return names
        except Exception as e:
            logger.debug("Windows camera enumeration note: %s", e)
        return []

    def discover_cameras(self, max_index: int = 10) -> List[CameraInfo]:
        """
        Discover available camera devices.

        Args:
            max_index: Maximum camera index to probe

        Returns:
            List of discovered camera info
        """
        windows_names = self._get_windows_camera_names()
        devices = []
        for i in range(max_index):
            try:
                cap = cv2.VideoCapture(i, settings.camera_backend_flag)
                if cap.isOpened():
                    # Try to get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    backend = int(cap.get(cv2.CAP_PROP_BACKEND))

                    # Map real Windows camera device friendly name if available, with clear fallback
                    if i < len(windows_names) and windows_names[i]:
                        name = windows_names[i]
                    else:
                        name = f"Camera {i} (Name unavailable)"

                    devices.append(CameraInfo(
                        index=i,
                        name=str(name),
                        width=width,
                        height=height,
                        fps=fps if fps > 0 else 0.0,
                        backend=str(backend),
                        available=True,
                    ))
                    logger.info(
                        "Discovered camera %d: %s (%dx%d @ %.1f fps)",
                        i, name, width, height, fps
                    )
                cap.release()
            except Exception as e:
                logger.debug("Failed to probe camera %d: %s", i, e)

        self._status.devices = devices
        return devices

    def get_status(self) -> CameraStatus:
        """Get current camera status."""
        with self._lock:
            return CameraStatus(
                state=self._status.state,
                camera_index=self._status.camera_index,
                actual_width=self._status.actual_width,
                actual_height=self._status.actual_height,
                actual_fps=self._status.actual_fps,
                backend=self._status.backend,
                is_capturing=self._status.is_capturing,
                last_frame_time=self._status.last_frame_time,
                frames_captured=self._status.frames_captured,
                frames_dropped=self._status.frames_dropped,
                last_error=self._status.last_error,
                devices=self._status.devices.copy(),
                owner=self._owner,
            )

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest captured frame (thread-safe copy).

        Returns:
            Latest frame as numpy array, or None if no frame available
        """
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
            return None

    def get_latest_frame_with_metadata(self) -> Tuple[Optional[np.ndarray], float, int]:
        """
        Get the latest captured frame with capture timestamp and sequence number.
        Avoids redundant memory copies for internal worker pipelines.

        Returns:
            Tuple of (frame_array, capture_timestamp, frame_sequence_number)
        """
        with self._lock:
            return self._latest_frame, self._latest_capture_time, self._frame_seq

    def wait_for_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Wait for a new frame to be available.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Latest frame or None if timeout
        """
        if self._frame_ready.wait(timeout=timeout):
            return self.get_latest_frame()
        return None

    def start(
        self,
        camera_index: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fps: Optional[float] = None,
    ) -> bool:
        """
        Start camera capture with configurable resolution and framerate.

        Args:
            camera_index: Camera index to use (None = use config default)
            width: Target frame width (default: settings.camera_width / 640)
            height: Target frame height (default: settings.camera_height / 480)
            fps: Target capture FPS (default: settings.camera_fps / 30)

        Returns:
            True if started successfully
        """
        with self._lock:
            if self._status.is_capturing:
                logger.warning("Camera already capturing")
                return False

            index = camera_index if camera_index is not None else settings.camera_index
            target_width = width or settings.camera_width
            target_height = height or settings.camera_height
            target_fps = fps or settings.camera_fps

            self._status.camera_index = index
            self._status.state = CameraState.CONNECTING
            self._status.last_error = None
            self._fps_window.clear()
            self._frame_seq = 0

            try:
                # Initialize camera
                backend_flag = settings.camera_backend_flag
                self._camera = cv2.VideoCapture(index, backend_flag)

                if not self._camera.isOpened():
                    raise RuntimeError(f"Failed to open camera index {index}")

                # Set camera properties
                self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
                self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
                self._camera.set(cv2.CAP_PROP_FPS, target_fps)

                # Get actual properties
                actual_width = int(self._camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self._camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = self._camera.get(cv2.CAP_PROP_FPS)
                backend = int(self._camera.get(cv2.CAP_PROP_BACKEND))

                self._status.actual_width = actual_width
                self._status.actual_height = actual_height
                self._status.actual_fps = actual_fps if actual_fps > 0 else 0.0
                self._status.backend = str(backend)

                # Verify camera is working by reading a test frame
                ret, test_frame = self._camera.read()
                if not ret or test_frame is None:
                    raise RuntimeError("Camera opened but cannot read frames")

                logger.info(
                    "Camera started: index=%d, %dx%d @ %.1f fps, backend=%d",
                    index, actual_width, actual_height, actual_fps, backend
                )

                # Start capture thread
                self._stop_event.clear()
                self._capture_thread = threading.Thread(
                    target=self._capture_loop,
                    name="CameraCapture",
                    daemon=True,
                )
                self._capture_thread.start()

                self._status.state = CameraState.CAPTURING
                self._status.is_capturing = True
                self._initialized = True
                self._owner = "backend"
                self._status.owner = "backend"

                return True

            except Exception as e:
                error_msg = f"Failed to start camera: {e}"
                logger.error(error_msg, exc_info=True)
                self._status.state = CameraState.ERROR
                self._status.last_error = error_msg
                self._cleanup_camera()
                return False

    def stop(self) -> bool:
        """
        Stop camera capture and release resources.

        Returns:
            True if stopped successfully
        """
        with self._lock:
            if not self._status.is_capturing and self._camera is None:
                logger.debug("Camera already stopped")
                if self._owner == "backend":
                    self._owner = "none"
                    self._status.owner = "none"
                return True

            logger.info("Stopping camera capture")
            self._stop_event.set()

            # Wait for capture thread to finish
            if self._capture_thread and self._capture_thread.is_alive():
                self._capture_thread.join(timeout=2.0)
                if self._capture_thread.is_alive():
                    logger.warning("Capture thread did not stop gracefully")

            self._cleanup_camera()
            self._status.state = CameraState.DISCONNECTED
            self._status.is_capturing = False
            self._initialized = False
            if self._owner == "backend":
                self._owner = "none"
            self._status.owner = self._owner

            logger.info("Camera stopped successfully")
            return True

    def claim_ownership(self, owner: str = "browser") -> bool:
        """
        Claim physical camera ownership for 'browser' or 'backend'.
        If 'browser' is claimed, immediately stops any running backend capture
        to release the hardware device.

        Args:
            owner: 'browser' or 'backend'

        Returns:
            True if claimed successfully
        """
        with self._lock:
            if owner == "browser":
                if self._status.is_capturing or self._camera is not None:
                    logger.info("Stopping backend camera to release device for browser")
                    self.stop()
                self._owner = "browser"
                self._status.owner = "browser"
                return True
            elif owner == "backend":
                self._owner = "backend"
                self._status.owner = "backend"
                return True
            return False

    def release_ownership(self, owner: Optional[str] = None) -> bool:
        """
        Release physical camera ownership.

        Args:
            owner: Specific owner releasing ownership, or None to release regardless

        Returns:
            True if released successfully
        """
        with self._lock:
            if owner is None or self._owner == owner:
                if self._status.is_capturing or self._camera is not None:
                    self.stop()
                self._owner = "none"
                self._status.owner = "none"
            return True

    def get_owner(self) -> str:
        """Get the current camera owner identifier."""
        with self._lock:
            return self._owner

    def _cleanup_camera(self) -> None:
        """Internal cleanup of camera resources."""
        if self._camera:
            try:
                self._camera.release()
            except Exception as e:
                logger.error("Error releasing camera: %s", e)
            finally:
                self._camera = None

        self._latest_frame = None
        self._frame_ready.clear()

    def _capture_loop(self) -> None:
        """Background capture loop (runs in separate thread)."""
        logger.debug("Capture loop started")
        frame_interval = 1.0 / settings.camera_fps if settings.camera_fps > 0 else 1.0 / 30.0

        while not self._stop_event.is_set():
            loop_start = time.time()

            try:
                if self._camera is None or not self._camera.isOpened():
                    logger.error("Camera disconnected during capture")
                    with self._lock:
                        self._status.state = CameraState.ERROR
                        self._status.last_error = "Camera disconnected"
                    break

                ret, frame = self._camera.read()

                if not ret or frame is None:
                    self._status.frames_dropped += 1
                    if self._status.frames_dropped > 10:
                        logger.warning("Multiple frames dropped, camera may be failing")
                    time.sleep(0.01)
                    continue

                # Apply mirroring if enabled
                if settings.camera_mirror:
                    frame = cv2.flip(frame, 1)

                capture_time = time.time()
                self._fps_window.append(capture_time)
                if len(self._fps_window) > 1:
                    duration = self._fps_window[-1] - self._fps_window[0]
                    if duration > 0:
                        self._status.actual_fps = round((len(self._fps_window) - 1) / duration, 1)

                # Update latest frame (thread-safe, latest-frame-wins)
                with self._lock:
                    self._frame_seq += 1
                    self._latest_frame = frame
                    self._latest_capture_time = capture_time
                    self._status.last_frame_time = datetime.now()
                    self._status.frames_captured += 1

                # Signal frame ready
                self._frame_ready.set()

            except Exception as e:
                logger.error("Error in capture loop: %s", e, exc_info=True)
                with self._lock:
                    self._status.state = CameraState.ERROR
                    self._status.last_error = f"Capture error: {e}"
                break

            # Maintain frame rate without artificial sleep if camera blocks natively
            elapsed = time.time() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0.002:
                time.sleep(sleep_time)

        logger.debug("Capture loop ended")

    def is_healthy(self) -> bool:
        """Check if camera is healthy and capturing."""
        with self._lock:
            return (
                self._status.is_capturing
                and self._camera is not None
                and self._camera.isOpened()
                and self._status.state == CameraState.CAPTURING
            )

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.stop()
        except Exception:
            pass