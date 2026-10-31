"""
Dataset Readiness Analyzer for GestureFlow AI Static Gesture Classifier.

Audits all registered gesture classes and persisted dataset samples to verify
readiness for training:
- Sample counts (valid vs invalid vs missing landmarks)
- Coordinate schema (3D vs 2D)
- Handedness distribution (Left, Right, Unknown)
- Duplicate sample detection
- Class imbalance detection
- Multi-class training eligibility (strictly enforces >= 2 valid classes)
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

from app.schemas.classifier import (
    DatasetReadinessClassReport,
    DatasetReadinessReport,
)
from app.services.dataset_service import DatasetService
from app.services.gesture_service import GestureService

logger = logging.getLogger(__name__)


class DatasetReadinessAnalyzer:
    """
    Audits local dataset storage for classifier training readiness.
    """

    MIN_SAMPLES_PER_CLASS = 5

    def __init__(
        self,
        dataset_service: Optional[DatasetService] = None,
        gesture_service: Optional[GestureService] = None,
    ):
        self._dataset_service = dataset_service or DatasetService()
        self._gesture_service = gesture_service or GestureService()

    def audit(self, min_samples: Optional[int] = None) -> DatasetReadinessReport:
        """
        Perform comprehensive dataset readiness audit across all registered gestures.
        """
        threshold = min_samples if min_samples is not None else self.MIN_SAMPLES_PER_CLASS
        gestures = self._gesture_service.get_all()

        class_reports: List[DatasetReadinessClassReport] = []
        total_samples = 0
        total_valid = 0
        total_invalid = 0
        ready_classes = 0
        valid_counts_for_imbalance: List[int] = []

        for g in gestures:
            rep = self._audit_gesture_class(g.id, g.name, threshold)
            class_reports.append(rep)
            total_samples += rep.sample_count
            total_valid += rep.valid_sample_count
            total_invalid += rep.invalid_sample_count

            if rep.is_ready:
                ready_classes += 1
                valid_counts_for_imbalance.append(rep.valid_sample_count)

        # Class imbalance calculation across ready classes
        imbalance_ratio = 1.0
        warnings: List[str] = []

        if len(valid_counts_for_imbalance) >= 2:
            max_c = max(valid_counts_for_imbalance)
            min_c = min(valid_counts_for_imbalance)
            imbalance_ratio = round(float(max_c / max(1, min_c)), 2)
            if imbalance_ratio >= 3.0:
                warnings.append(
                    f"Significant class imbalance detected (ratio {imbalance_ratio:.1f}:1). "
                    "Consider balancing samples across classes to avoid majority-class bias."
                )

        # Global training readiness check
        is_ready = ready_classes >= 2

        if ready_classes == 0:
            summary = "No gesture classes have sufficient valid samples for training."
            warnings.append(
                f"Dataset empty or uncollected. Collect at least {threshold} samples for at least 2 distinct gestures."
            )
        elif ready_classes == 1:
            summary = "Only 1 gesture class is eligible. Classification requires at least 2 distinct classes."
            ready_name = [c.gesture_name for c in class_reports if c.is_ready][0]
            warnings.append(
                f"Only '{ready_name}' has sufficient samples. Classifier cannot train with 1 class. "
                "Collect or import samples for a second gesture (e.g. Closed Fist, Thumbs Up)."
            )
        else:
            summary = f"Dataset is ready for training with {ready_classes} eligible gesture classes."

        return DatasetReadinessReport(
            total_gestures=len(gestures),
            total_samples=total_samples,
            valid_samples=total_valid,
            invalid_samples=total_invalid,
            ready_classes_count=ready_classes,
            min_samples_per_class=threshold,
            classes=class_reports,
            class_imbalance_ratio=imbalance_ratio,
            is_training_ready=is_ready,
            summary=summary,
            warnings=warnings,
        )

    def _audit_gesture_class(
        self, gesture_id: str, gesture_name: str, min_samples: int
    ) -> DatasetReadinessClassReport:
        """Audit all sample JSON files for a specific gesture class."""
        folder = self._dataset_service.samples_dir / gesture_id
        warnings: List[str] = []

        if not folder.exists() or not folder.is_dir():
            return DatasetReadinessClassReport(
                gesture_id=gesture_id,
                gesture_name=gesture_name,
                sample_count=0,
                valid_sample_count=0,
                invalid_sample_count=0,
                missing_landmarks_count=0,
                coordinate_schema="3D",
                handedness_distribution={},
                dataset_compatibility="compatible_3d",
                is_ready=False,
                warnings=["No samples folder exists for this gesture."],
            )

        files = list(folder.glob("*.json"))
        sample_count = len(files)

        if sample_count == 0:
            return DatasetReadinessClassReport(
                gesture_id=gesture_id,
                gesture_name=gesture_name,
                sample_count=0,
                valid_sample_count=0,
                invalid_sample_count=0,
                missing_landmarks_count=0,
                coordinate_schema="3D",
                handedness_distribution={},
                dataset_compatibility="compatible_3d",
                is_ready=False,
                warnings=["Zero samples collected."],
            )

        valid_count = 0
        invalid_count = 0
        missing_lms_count = 0
        handedness_dist: Dict[str, int] = {"Right": 0, "Left": 0, "Unknown": 0}
        seen_fingerprints: Set[str] = set()
        duplicate_count = 0
        has_2d_only = False

        for f_path in files:
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Check handedness
                hand = data.get("handedness", "Unknown")
                handedness_dist[hand] = handedness_dist.get(hand, 0) + 1

                # Check landmarks
                lms = data.get("landmarks", [])
                if not lms or len(lms) != 21:
                    invalid_count += 1
                    missing_lms_count += 1
                    continue

                # Check coordinates
                valid_coords = True
                fp_coords = []
                for pt in lms:
                    x = pt.get("x")
                    y = pt.get("y")
                    z = pt.get("z")

                    if x is None or y is None or not math.isfinite(x) or not math.isfinite(y):
                        valid_coords = False
                        break

                    if z is None or not math.isfinite(z):
                        has_2d_only = True

                    fp_coords.append(f"{round(x, 4)},{round(y, 4)}")

                if not valid_coords:
                    invalid_count += 1
                    continue

                # Duplicate detection check
                fp = ";".join(fp_coords)
                if fp in seen_fingerprints:
                    duplicate_count += 1
                else:
                    seen_fingerprints.add(fp)

                valid_count += 1

            except Exception as e:
                logger.debug("Failed to parse sample %s: %s", f_path.name, e)
                invalid_count += 1

        # Class-level warnings
        if duplicate_count > 0:
            warnings.append(f"{duplicate_count} duplicate or identical frame sample(s) detected.")

        if valid_count < min_samples:
            warnings.append(f"Insufficient samples: {valid_count}/{min_samples} required for training.")

        schema = "2D" if has_2d_only else "3D"
        compat = "2d_only" if has_2d_only else "compatible_3d"
        if has_2d_only:
            warnings.append("Samples contain 2D coordinates without depth (z) channels.")

        is_ready = valid_count >= min_samples and not has_2d_only

        return DatasetReadinessClassReport(
            gesture_id=gesture_id,
            gesture_name=gesture_name,
            sample_count=sample_count,
            valid_sample_count=valid_count,
            invalid_sample_count=invalid_count,
            missing_landmarks_count=missing_lms_count,
            coordinate_schema=schema,
            handedness_distribution=handedness_dist,
            dataset_compatibility=compat,
            is_ready=is_ready,
            warnings=warnings,
        )
