"""
Thread-safe bounded temporal frame buffer for hand landmark observations.
"""

from collections import deque
from dataclasses import dataclass, field
import math
import threading
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.services.temporal.temporal_config import TemporalConfig


@dataclass
class TemporalObservation:
    """A single snapshot of a hand's spatial state at a monotonic timestamp."""
    timestamp: float                       # Monotonic seconds
    landmarks: List[Tuple[float, float, float]] # 21 (x, y, z)
    wrist: Tuple[float, float, float]      # Point 0
    palm_center: Tuple[float, float, float]# Point 9 (Middle MCP)
    centroid: Tuple[float, float, float]   # Mean of all 21 points
    palm_scale: float                      # Distance between wrist and middle MCP
    handedness: str                        # "Left" or "Right"
    static_gesture_id: Optional[str] = None
    static_gesture_name: Optional[str] = None


class TemporalFrameBuffer:
    """
    Maintains a bounded window of recent hand landmark observations.
    
    Guarantees:
    - Bounded memory (fixed capacity deque)
    - Time-window eviction (discards data older than max duration)
    - Tracking discontinuity handling (clears buffer if time gap > threshold)
    - Thread-safe mutation and query
    """

    def __init__(
        self,
        max_size: int = TemporalConfig.BUFFER_MAX_SIZE,
        max_duration_s: float = TemporalConfig.BUFFER_MAX_DURATION_S,
        discontinuity_threshold_s: float = TemporalConfig.DISCONTINUITY_THRESHOLD_S,
    ):
        self._max_size = max_size
        self._max_duration_s = max_duration_s
        self._discontinuity_threshold_s = discontinuity_threshold_s

        self._buffer: deque[TemporalObservation] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._last_timestamp: float = 0.0

    def append(
        self,
        timestamp: float,
        landmarks: Any,
        handedness: str = "Right",
        static_gesture_id: Optional[str] = None,
        static_gesture_name: Optional[str] = None,
    ) -> bool:
        """
        Extract key reference points and append an observation to the buffer.
        
        Returns:
            True if successfully added, False if invalid or rejected.
        """
        # 1. Parse and validate 21 landmarks
        coords = self._extract_points(landmarks)
        if not coords or len(coords) != 21:
            return False

        with self._lock:
            # 2. Check for time discontinuity (e.g. tracking lost and resumed)
            if self._buffer and (timestamp - self._last_timestamp > self._discontinuity_threshold_s):
                self._buffer.clear()

            # Monotonic sanity check
            if self._buffer and timestamp <= self._last_timestamp:
                timestamp = self._last_timestamp + 0.001

            # 3. Compute reference points
            wrist = coords[0]
            palm_center = coords[9]
            arr = np.array(coords, dtype=np.float32)
            centroid = (float(np.mean(arr[:, 0])), float(np.mean(arr[:, 1])), float(np.mean(arr[:, 2])))

            # Palm scale (wrist to middle MCP distance)
            scale = math.sqrt(
                (palm_center[0] - wrist[0]) ** 2
                + (palm_center[1] - wrist[1]) ** 2
                + (palm_center[2] - wrist[2]) ** 2
            )
            scale = max(scale, 1e-4)

            obs = TemporalObservation(
                timestamp=timestamp,
                landmarks=coords,
                wrist=wrist,
                palm_center=palm_center,
                centroid=centroid,
                palm_scale=scale,
                handedness=handedness,
                static_gesture_id=static_gesture_id,
                static_gesture_name=static_gesture_name,
            )

            self._buffer.append(obs)
            self._last_timestamp = timestamp

            # 4. Evict observations older than max_duration_s
            while len(self._buffer) > 1 and (timestamp - self._buffer[0].timestamp > self._max_duration_s):
                self._buffer.popleft()

            return True

    def get_observations(self, duration_s: Optional[float] = None) -> List[TemporalObservation]:
        """Return list of observations within the specified duration window (or all)."""
        with self._lock:
            if not self._buffer:
                return []
            if duration_s is None:
                return list(self._buffer)

            latest_t = self._buffer[-1].timestamp
            min_t = latest_t - duration_s
            return [obs for obs in self._buffer if obs.timestamp >= min_t]

    def get_trajectory_points(
        self,
        target: str = "centroid",
        duration_s: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Return timestamps (N,) and 3D coordinate array (N, 3) for the specified reference point.
        target can be 'centroid', 'wrist', or 'palm_center'.
        """
        observations = self.get_observations(duration_s=duration_s)
        if not observations:
            return np.empty((0,), dtype=np.float32), np.empty((0, 3), dtype=np.float32)

        times = np.array([obs.timestamp for obs in observations], dtype=np.float32)

        if target == "wrist":
            pts = [obs.wrist for obs in observations]
        elif target == "palm_center":
            pts = [obs.palm_center for obs in observations]
        else:
            pts = [obs.centroid for obs in observations]

        return times, np.array(pts, dtype=np.float32)

    def get_duration_ms(self) -> float:
        """Return the temporal span of the buffer in milliseconds."""
        with self._lock:
            if len(self._buffer) < 2:
                return 0.0
            return (self._buffer[-1].timestamp - self._buffer[0].timestamp) * 1000.0

    def clear(self) -> None:
        """Clear all buffered observations."""
        with self._lock:
            self._buffer.clear()
            self._last_timestamp = 0.0

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)

    @property
    def latest_observation(self) -> Optional[TemporalObservation]:
        """Return the most recent observation in the buffer."""
        with self._lock:
            return self._buffer[-1] if self._buffer else None

    @staticmethod
    def _extract_points(landmarks: Any) -> Optional[List[Tuple[float, float, float]]]:
        """Extract finite (x, y, z) coordinates for all 21 points."""
        if not landmarks or len(landmarks) != 21:
            return None

        coords = []
        for pt in landmarks:
            if isinstance(pt, dict):
                x = pt.get("x")
                y = pt.get("y")
                z = pt.get("z", 0.0)
            elif isinstance(pt, (list, tuple)):
                x = pt[0] if len(pt) > 0 else None
                y = pt[1] if len(pt) > 1 else None
                z = pt[2] if len(pt) > 2 else 0.0
            else:
                x = getattr(pt, "x", None)
                y = getattr(pt, "y", None)
                z = getattr(pt, "z", 0.0)

            if x is None or y is None:
                return None
            try:
                x_f, y_f, z_f = float(x), float(y), float(z or 0.0)
                if not (math.isfinite(x_f) and math.isfinite(y_f) and math.isfinite(z_f)):
                    return None
                coords.append((x_f, y_f, z_f))
            except (ValueError, TypeError):
                return None

        return coords
