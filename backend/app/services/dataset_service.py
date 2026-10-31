"""
Dataset Service for GestureFlow AI.

Manages on-disk dataset storage in backend/datasets/samples/{gesture_id}/{sample_id}.json.
Provides thread-safe persistence, querying, deletion, validation, and export (CSV/JSON).
"""

import csv
import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.schemas.dataset import (
    DatasetSample,
    DatasetSampleSummary,
    DatasetStatsResponse,
    DatasetValidationReport,
    LandmarkCoord,
    ValidationIssue,
)

logger = logging.getLogger(__name__)


class DatasetService:
    """Manages dataset sample storage, statistics, validation, and exports."""

    def __init__(self, dataset_dir: Optional[Path] = None) -> None:
        """Initialize dataset service with base directory."""
        self._lock = threading.RLock()
        self._base_dir = Path(dataset_dir) if dataset_dir else settings.resolved_dataset_dir
        self._samples_dir = self._base_dir / "samples"
        self._exports_dir = self._base_dir / "exports"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create sample and export directories if they do not exist."""
        with self._lock:
            self._samples_dir.mkdir(parents=True, exist_ok=True)
            self._exports_dir.mkdir(parents=True, exist_ok=True)

    @property
    def samples_dir(self) -> Path:
        """Root directory for sample JSON files."""
        return self._samples_dir

    @property
    def dataset_dir(self) -> Path:
        """Root dataset directory."""
        return self._dataset_dir

    def save_sample(self, sample: DatasetSample) -> DatasetSample:
        """
        Save a dataset sample atomically.

        Args:
            sample: Complete DatasetSample model

        Returns:
            Saved DatasetSample

        Raises:
            ValueError: If sample_id already exists or validation fails
        """
        with self._lock:
            # Rigorous integrity validation before persisting
            if not sample.sample_id or not sample.sample_id.strip():
                raise ValueError("sample_id must be a non-empty string.")
            if not sample.gesture_id or not sample.gesture_id.strip():
                raise ValueError("gesture_id must be a non-empty string.")
            if len(sample.landmarks) != 21:
                raise ValueError(f"Sample must contain exactly 21 landmarks, got {len(sample.landmarks)}.")

            import math
            for lm in sample.landmarks:
                if not math.isfinite(lm.x) or not math.isfinite(lm.y):
                    raise ValueError(f"Landmark {lm.index} has non-finite coordinates: x={lm.x}, y={lm.y}")
                if lm.z is not None and not math.isfinite(lm.z):
                    raise ValueError(f"Landmark {lm.index} has non-finite depth: z={lm.z}")

            gesture_dir = self._samples_dir / sample.gesture_id
            gesture_dir.mkdir(parents=True, exist_ok=True)

            sample_file = gesture_dir / f"{sample.sample_id}.json"
            if sample_file.exists():
                raise ValueError(f"Sample with ID '{sample.sample_id}' already exists.")

            temp_file = sample_file.with_suffix(".tmp")
            try:
                logger.debug("Persistence started: sample_id=%s, gesture=%s", sample.sample_id, sample.gesture_id)
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(sample.model_dump(), f, indent=2, ensure_ascii=False)
                
                # Atomic file replacement
                os.replace(temp_file, sample_file)

                if not sample_file.exists() or sample_file.stat().st_size == 0:
                    raise IOError(f"Sample file {sample_file} was not written properly or is empty.")

                logger.debug("Persistence successful: sample_id=%s saved to %s (%d bytes)", 
                             sample.sample_id, sample_file.name, sample_file.stat().st_size)
                return sample
            except Exception as e:
                logger.error("Persistence failed for sample %s: %s", sample.sample_id, e)
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass
                raise

    def get_sample(self, sample_id: str) -> Optional[DatasetSample]:
        """Find and load a specific sample by sample_id across all gestures."""
        with self._lock:
            for g_dir in self._samples_dir.iterdir():
                if g_dir.is_dir():
                    s_file = g_dir / f"{sample_id}.json"
                    if s_file.exists():
                        try:
                            with open(s_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            return DatasetSample(**data)
                        except Exception as e:
                            logger.error("Error reading sample file %s: %s", s_file, e)
                            return None
            return None

    def get_samples(
        self,
        gesture_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DatasetSampleSummary], int]:
        """
        Query paginated sample summaries.

        Args:
            gesture_id: Filter by gesture ID
            session_id: Filter by session ID
            limit: Maximum samples to return
            offset: Pagination offset

        Returns:
            Tuple of (sample_summaries, total_matching_count)
        """
        with self._lock:
            all_summaries: List[DatasetSampleSummary] = []

            dirs_to_scan = [self._samples_dir / gesture_id] if gesture_id else [
                d for d in self._samples_dir.iterdir() if d.is_dir()
            ]

            for g_dir in dirs_to_scan:
                if not g_dir.exists():
                    continue
                for s_file in g_dir.glob("*.json"):
                    try:
                        with open(s_file, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        # Filter by session_id if requested
                        if session_id and data.get("session_id") != session_id:
                            continue

                        all_summaries.append(
                            DatasetSampleSummary(
                                sample_id=data.get("sample_id", s_file.stem),
                                gesture_id=data.get("gesture_id", g_dir.name),
                                gesture_name=data.get("gesture_name", g_dir.name),
                                timestamp=data.get("timestamp", ""),
                                handedness=data.get("handedness", "Unknown"),
                                handedness_confidence=data.get("handedness_confidence", 0.0),
                                session_id=data.get("session_id", ""),
                                landmark_count=len(data.get("landmarks", [])),
                            )
                        )
                    except Exception as e:
                        logger.warning("Skipping unreadable sample file %s: %s", s_file, e)

            # Sort by timestamp descending
            all_summaries.sort(key=lambda s: s.timestamp, reverse=True)
            total = len(all_summaries)
            paginated = all_summaries[offset : offset + limit]

            return paginated, total

    def delete_sample(self, sample_id: str) -> bool:
        """Delete an individual sample file."""
        with self._lock:
            for g_dir in self._samples_dir.iterdir():
                if g_dir.is_dir():
                    s_file = g_dir / f"{sample_id}.json"
                    if s_file.exists():
                        try:
                            s_file.unlink()
                            logger.info("Deleted sample %s", sample_id)
                            return True
                        except Exception as e:
                            logger.error("Failed to delete sample %s: %s", sample_id, e)
                            return False
            return False

    def delete_session(self, session_id: str) -> int:
        """Delete all samples belonging to a collection session."""
        with self._lock:
            deleted_count = 0
            for s_file in self._samples_dir.rglob("*.json"):
                try:
                    with open(s_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("session_id") == session_id:
                        s_file.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.warning("Error checking session for file %s: %s", s_file, e)

            logger.info("Deleted session %s (%d samples)", session_id, deleted_count)
            return deleted_count

    def delete_gesture_samples(self, gesture_id: str) -> int:
        """Delete all sample files associated with a gesture."""
        with self._lock:
            g_dir = self._samples_dir / gesture_id
            if not g_dir.exists():
                return 0

            deleted = 0
            for s_file in g_dir.glob("*.json"):
                try:
                    s_file.unlink()
                    deleted += 1
                except Exception:
                    pass

            try:
                g_dir.rmdir()
            except Exception:
                pass

            logger.info("Deleted %d samples for gesture %s", deleted, gesture_id)
            return deleted

    def get_sample_counts_by_gesture(self) -> Dict[str, int]:
        """Return a mapping of gesture_id -> sample count."""
        with self._lock:
            counts: Dict[str, int] = {}
            if not self._samples_dir.exists():
                return counts

            for g_dir in self._samples_dir.iterdir():
                if g_dir.is_dir():
                    count = len(list(g_dir.glob("*.json")))
                    counts[g_dir.name] = count
            return counts

    def get_stats(self, registered_gestures: Optional[List[dict]] = None) -> DatasetStatsResponse:
        """Calculate complete dataset statistics."""
        with self._lock:
            counts = self.get_sample_counts_by_gesture()
            reg_list = registered_gestures or []
            total_gestures = len(reg_list) if reg_list else len(counts)

            target_per_gesture = 50
            total_samples = sum(counts.values())

            # Gestures with insufficient samples (< target)
            insufficient: List[str] = []
            for g in reg_list:
                gid = g.get("id", "")
                if counts.get(gid, 0) < target_per_gesture:
                    insufficient.append(gid)

            # Completion percentage (capped at 100%)
            if total_gestures > 0:
                target_total = total_gestures * target_per_gesture
                completion = min(100.0, round((total_samples / target_total) * 100, 1))
            else:
                completion = 0.0

            # Latest session
            latest_session_id = None
            latest_session_time = None
            all_samples, _ = self.get_samples(limit=1)
            if all_samples:
                latest_session_id = all_samples[0].session_id
                latest_session_time = all_samples[0].timestamp

            return DatasetStatsResponse(
                total_gestures=total_gestures,
                total_samples=total_samples,
                samples_per_gesture=counts,
                gesture_counts=counts,
                insufficient_sample_gestures=insufficient,
                insufficient_gestures=insufficient,
                completion_percentage=completion,
                target_samples_per_gesture=target_per_gesture,
                latest_session_id=latest_session_id,
                latest_session_time=latest_session_time,
            )

    def validate_dataset(self, registered_ids: Optional[Set[str]] = None) -> DatasetValidationReport:
        """
        Perform a thorough validation audit across all stored dataset samples.
        Checks for:
        - Corrupted JSON files
        - Missing or incomplete landmarks (must have exactly 21)
        - Invalid coordinate ranges or non-numeric values
        - Unregistered / orphaned gesture labels
        - Duplicate sample IDs
        - Invalid handedness
        """
        with self._lock:
            total_checked = 0
            valid_samples = 0
            corrupted = 0
            missing_landmarks = 0
            invalid_coords = 0
            missing_gesture_ref = 0
            seen_sample_ids: Set[str] = set()
            duplicates: Set[str] = set()
            issues: List[ValidationIssue] = []

            for s_file in self._samples_dir.rglob("*.json"):
                total_checked += 1
                try:
                    with open(s_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    corrupted += 1
                    issues.append(
                        ValidationIssue(
                            sample_id=s_file.stem,
                            gesture_id=s_file.parent.name,
                            issue_type="corrupted_file",
                            message=f"JSON parsing error: {e}",
                            severity="error",
                        )
                    )
                    continue

                sid = data.get("sample_id", "")
                gid = data.get("gesture_id", "")
                landmarks = data.get("landmarks", [])

                # Check duplicates
                if sid in seen_sample_ids:
                    duplicates.add(sid)
                    issues.append(
                        ValidationIssue(
                            sample_id=sid,
                            gesture_id=gid,
                            issue_type="duplicate_id",
                            message=f"Duplicate sample ID found: {sid}",
                            severity="warning",
                        )
                    )
                else:
                    seen_sample_ids.add(sid)

                # Check registered gesture reference
                if registered_ids is not None and gid not in registered_ids:
                    missing_gesture_ref += 1
                    issues.append(
                        ValidationIssue(
                            sample_id=sid,
                            gesture_id=gid,
                            issue_type="unregistered_gesture",
                            message=f"Gesture ID '{gid}' is not in the active gesture registry",
                            severity="warning",
                        )
                    )

                # Check landmark count
                if not isinstance(landmarks, list) or len(landmarks) != 21:
                    missing_landmarks += 1
                    issues.append(
                        ValidationIssue(
                            sample_id=sid,
                            gesture_id=gid,
                            issue_type="missing_landmarks",
                            message=f"Expected 21 landmarks, found {len(landmarks) if isinstance(landmarks, list) else 0}",
                            severity="error",
                        )
                    )
                    continue

                # Check numeric validity
                coords_valid = True
                for lm in landmarks:
                    x = lm.get("x")
                    y = lm.get("y")
                    z = lm.get("z")
                    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not isinstance(z, (int, float)):
                        coords_valid = False
                        break
                    if x < 0.0 or x > 1.0 or y < 0.0 or y > 1.0:
                        # Allow slight out-of-frame boundary if hand is partially off-camera, but flag extremes
                        if x < -0.5 or x > 1.5 or y < -0.5 or y > 1.5:
                            coords_valid = False
                            break

                if not coords_valid:
                    invalid_coords += 1
                    issues.append(
                        ValidationIssue(
                            sample_id=sid,
                            gesture_id=gid,
                            issue_type="invalid_coordinates",
                            message="One or more landmarks contain non-numeric or extreme coordinate values",
                            severity="warning",
                        )
                    )
                    continue

                # Handedness check
                if data.get("handedness") not in ("Left", "Right", "Unknown"):
                    issues.append(
                        ValidationIssue(
                            sample_id=sid,
                            gesture_id=gid,
                            issue_type="invalid_handedness",
                            message=f"Unrecognized handedness label: {data.get('handedness')}",
                            severity="info",
                        )
                    )

                valid_samples += 1

            is_valid = (corrupted == 0 and missing_landmarks == 0 and len(duplicates) == 0)

            return DatasetValidationReport(
                is_valid=is_valid,
                total_checked=total_checked,
                valid_samples=valid_samples,
                corrupted_samples=corrupted,
                missing_landmarks_count=missing_landmarks,
                invalid_coordinates_count=invalid_coords,
                missing_gesture_ref_count=missing_gesture_ref,
                duplicate_sample_ids=sorted(list(duplicates)),
                issues=issues,
            )

    def export_csv(self, gesture_id: Optional[str] = None) -> Path:
        """
        Export dataset samples to CSV.
        Flattens 21 landmarks to columns: x_0, y_0, z_0 ... x_20, y_20, z_20.
        """
        with self._lock:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"{gesture_id}_" if gesture_id else "full_dataset_"
            csv_filename = f"{prefix}{timestamp_str}.csv"
            export_path = self._exports_dir / csv_filename

            headers = [
                "sample_id",
                "gesture_id",
                "gesture_name",
                "session_id",
                "timestamp",
                "handedness",
                "handedness_confidence",
            ]
            for i in range(21):
                headers.extend([f"x_{i}", f"y_{i}", f"z_{i}"])

            samples_written = 0
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                dirs = [self._samples_dir / gesture_id] if gesture_id else [
                    d for d in self._samples_dir.iterdir() if d.is_dir()
                ]

                for g_dir in dirs:
                    if not g_dir.exists():
                        continue
                    for s_file in sorted(g_dir.glob("*.json")):
                        try:
                            with open(s_file, "r", encoding="utf-8") as sf:
                                data = json.load(sf)
                            row = [
                                data.get("sample_id", s_file.stem),
                                data.get("gesture_id", g_dir.name),
                                data.get("gesture_name", ""),
                                data.get("session_id", ""),
                                data.get("timestamp", ""),
                                data.get("handedness", "Unknown"),
                                data.get("handedness_confidence", 1.0),
                            ]
                            landmarks = {lm["index"]: lm for lm in data.get("landmarks", []) if "index" in lm}
                            for i in range(21):
                                lm = landmarks.get(i, {})
                                row.extend([
                                    lm.get("x", 0.0),
                                    lm.get("y", 0.0),
                                    lm.get("z", 0.0),
                                ])
                            writer.writerow(row)
                            samples_written += 1
                        except Exception as e:
                            logger.warning("Error exporting sample %s to CSV: %s", s_file, e)

            logger.info("Exported %d samples to CSV: %s", samples_written, export_path)
            return export_path

    def export_json(self, gesture_id: Optional[str] = None) -> Path:
        """
        Export dataset samples to structured JSON archive.
        """
        with self._lock:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"{gesture_id}_" if gesture_id else "full_dataset_"
            json_filename = f"{prefix}{timestamp_str}.json"
            export_path = self._exports_dir / json_filename

            all_samples = []
            dirs = [self._samples_dir / gesture_id] if gesture_id else [
                d for d in self._samples_dir.iterdir() if d.is_dir()
            ]

            for g_dir in dirs:
                if not g_dir.exists():
                    continue
                for s_file in sorted(g_dir.glob("*.json")):
                    try:
                        with open(s_file, "r", encoding="utf-8") as sf:
                            all_samples.append(json.load(sf))
                    except Exception as e:
                        logger.warning("Error reading sample %s for JSON export: %s", s_file, e)

            export_data = {
                "format_version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "total_samples": len(all_samples),
                "gesture_filter": gesture_id,
                "samples": all_samples,
            }

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info("Exported %d samples to JSON: %s", len(all_samples), export_path)
            return export_path
