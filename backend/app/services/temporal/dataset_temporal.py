"""
Dedicated storage and sequence collection service for Phase 5 Temporal Gestures.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas.temporal import TemporalCollectionStatus, TemporalSequenceSample
from app.services.temporal.temporal_config import TEMPORAL_GESTURE_CATALOG

logger = logging.getLogger(__name__)


class TemporalDatasetService:
    """Manages recording, validation, and disk persistence of temporal gesture sequences."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or (settings.backend_dir / "datasets" / "temporal")
        self._lock = threading.Lock()
        self._ensure_directories()

        # Ongoing collection session state
        self._is_collecting = False
        self._active_gesture_id: Optional[str] = None
        self._active_session_id: Optional[str] = None
        self._target_sequences = 10
        self._collected_count = 0

        # Buffer for sequence currently being recorded
        self._current_sequence_frames: List[Dict[str, Any]] = []
        self._current_sequence_timestamps: List[float] = []
        self._current_handedness: str = "Right"

    def _ensure_directories(self) -> None:
        """Create storage folders for all standard dynamic gestures."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for gid in TEMPORAL_GESTURE_CATALOG.keys():
            (self.base_dir / gid).mkdir(parents=True, exist_ok=True)

    def start_collection(
        self,
        gesture_id: str,
        session_id: Optional[str] = None,
        target_sequences: int = 10,
    ) -> TemporalCollectionStatus:
        """Start a new temporal sequence recording session."""
        with self._lock:
            if gesture_id not in TEMPORAL_GESTURE_CATALOG:
                raise ValueError(f"Unknown temporal gesture ID '{gesture_id}'.")

            self._is_collecting = True
            self._active_gesture_id = gesture_id
            self._active_session_id = session_id or f"session_temporal_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            self._target_sequences = target_sequences
            self._collected_count = 0
            self._current_sequence_frames.clear()
            self._current_sequence_timestamps.clear()

            return self.get_collection_status()

    def record_frame(
        self,
        landmarks: Any,
        timestamp: float,
        handedness: str = "Right",
    ) -> None:
        """Record an incoming landmark frame into the active sequence."""
        with self._lock:
            if not self._is_collecting:
                return

            raw_pts = []
            for pt in landmarks:
                if isinstance(pt, dict):
                    raw_pts.append({"x": pt.get("x"), "y": pt.get("y"), "z": pt.get("z", 0.0)})
                elif isinstance(pt, (list, tuple)):
                    raw_pts.append({"x": pt[0], "y": pt[1], "z": pt[2] if len(pt) > 2 else 0.0})
                else:
                    raw_pts.append({"x": getattr(pt, "x", 0.0), "y": getattr(pt, "y", 0.0), "z": getattr(pt, "z", 0.0)})

            if len(raw_pts) == 21:
                self._current_sequence_frames.append(raw_pts)
                self._current_sequence_timestamps.append(timestamp)
                self._current_handedness = handedness

    def commit_sequence(self) -> Optional[TemporalSequenceSample]:
        """
        Validate and persist the currently accumulated sequence to disk.
        Returns the saved sample, or None if rejected.
        """
        with self._lock:
            if not self._is_collecting or not self._active_gesture_id:
                return None

            frame_count = len(self._current_sequence_frames)
            if frame_count < 8:
                # Reject incomplete/too short sequences
                self._current_sequence_frames.clear()
                self._current_sequence_timestamps.clear()
                return None

            dt_ms = (self._current_sequence_timestamps[-1] - self._current_sequence_timestamps[0]) * 1000.0
            if dt_ms < 120.0:
                self._current_sequence_frames.clear()
                self._current_sequence_timestamps.clear()
                return None

            g_def = TEMPORAL_GESTURE_CATALOG[self._active_gesture_id]
            sample_id = f"seq_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
            sample = TemporalSequenceSample(
                sample_id=sample_id,
                gesture_id=self._active_gesture_id,
                gesture_name=g_def.name,
                handedness=self._current_handedness,
                session_id=self._active_session_id or "default_session",
                duration_ms=round(dt_ms, 2),
                frame_count=frame_count,
                timestamps=list(self._current_sequence_timestamps),
                landmarks_sequence=list(self._current_sequence_frames),
                camera_metadata={"width": 640, "height": 480, "fps": 30.0},
                dataset_version="1.0.0",
            )

            # Save JSON atomically
            g_dir = self.base_dir / self._active_gesture_id
            g_dir.mkdir(parents=True, exist_ok=True)
            save_path = g_dir / f"{sample_id}.json"

            temp_path = save_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(sample.model_dump(), f, indent=2)
            temp_path.replace(save_path)

            self._collected_count += 1
            self._current_sequence_frames.clear()
            self._current_sequence_timestamps.clear()

            logger.info("Saved temporal sequence '%s' for gesture %s (%d frames)", sample_id, self._active_gesture_id, frame_count)
            return sample

    def stop_collection(self) -> TemporalCollectionStatus:
        """Stop current sequence collection."""
        with self._lock:
            self._is_collecting = False
            self._current_sequence_frames.clear()
            self._current_sequence_timestamps.clear()
            return self.get_collection_status()

    def get_collection_status(self) -> TemporalCollectionStatus:
        """Return the current collection status."""
        return TemporalCollectionStatus(
            is_collecting=self._is_collecting,
            gesture_id=self._active_gesture_id,
            session_id=self._active_session_id,
            target_sequences=self._target_sequences,
            collected_sequences=self._collected_count,
            current_sequence_frames=len(self._current_sequence_frames),
        )

    def get_dataset_stats(self) -> Dict[str, Any]:
        """Aggregate statistics across all stored dynamic gesture sequences."""
        with self._lock:
            stats = {
                "total_sequences": 0,
                "total_frames": 0,
                "gestures": {},
            }

            for gid, g_def in TEMPORAL_GESTURE_CATALOG.items():
                g_dir = self.base_dir / gid
                seq_files = list(g_dir.glob("*.json")) if g_dir.exists() else []
                total_f = 0
                total_dur = 0.0

                for f_path in seq_files:
                    try:
                        with open(f_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        total_f += data.get("frame_count", 0)
                        total_dur += data.get("duration_ms", 0.0)
                    except Exception:
                        continue

                count = len(seq_files)
                stats["total_sequences"] += count
                stats["total_frames"] += total_f
                stats["gestures"][gid] = {
                    "id": gid,
                    "name": g_def.name,
                    "sequence_count": count,
                    "total_frames": total_f,
                    "avg_duration_ms": round(total_dur / max(1, count), 1),
                    "is_experimental": g_def.is_experimental,
                }

            return stats


# Singleton
_temporal_dataset_service: Optional[TemporalDatasetService] = None
_tds_lock = threading.Lock()


def get_temporal_dataset_service() -> TemporalDatasetService:
    global _temporal_dataset_service
    if _temporal_dataset_service is None:
        with _tds_lock:
            if _temporal_dataset_service is None:
                _temporal_dataset_service = TemporalDatasetService()
    return _temporal_dataset_service
