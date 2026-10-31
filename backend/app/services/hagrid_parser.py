"""
HaGRID Annotation Parser for GestureFlow AI.

Parses official HaGRIDv2 annotation JSON files, validates MediaPipe-derived 2D landmarks,
preserves original coordinates without fabricating z-depth, and converts valid records
into GestureFlow's internal DatasetSample schema.
"""

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.hagrid_constants import (
    DEFAULT_GESTUREFLOW_MAPPINGS,
    TWO_HANDED_GESTURES,
)

logger = logging.getLogger(__name__)


@dataclass
class ParseIssue:
    """Detailed validation issue encountered during annotation parsing."""

    image_id: str
    issue_type: str  # missing_landmarks, invalid_count, non_finite, out_of_bounds, corrupt_json
    detail: str
    severity: str = "warning"  # "warning" or "error"


@dataclass
class HagridParseResult:
    """Summary and extracted samples from a parsing job."""

    samples: List[DatasetSample] = field(default_factory=list)
    total_images_processed: int = 0
    valid_samples_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    class_distribution: Dict[str, int] = field(default_factory=dict)
    issues: List[ParseIssue] = field(default_factory=list)
    source_split: Optional[str] = None


class HagridAnnotationParser:
    """
    Dedicated parser for HaGRIDv2 annotation formats.

    Handles:
    - Single or multi-file annotations (JSON dicts with image UUID keys)
    - 1-handed and 2-handed gesture structures
    - 'no_gesture' secondary hand labels
    - Preserves 2D normalized coordinates without inventing missing z coordinates
    - Enforces coordinate range and finiteness validation
    - Tracks subject user_id for leakage-free train/val/test splits
    """

    def __init__(
        self,
        class_mappings: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """
        Initialize parser with configurable class mappings.

        Args:
            class_mappings: Map of HaGRID class name -> {target_id, target_name, action}
        """
        self._mappings = class_mappings or DEFAULT_GESTUREFLOW_MAPPINGS

    def set_mappings(self, mappings: Dict[str, Dict[str, Any]]) -> None:
        """Update class mappings."""
        self._mappings = mappings

    def parse_file(
        self,
        json_path: Union[str, Path],
        split: Optional[str] = None,
        selected_classes: Optional[Set[str]] = None,
        max_samples_per_class: Optional[int] = None,
    ) -> HagridParseResult:
        """
        Parse an individual HaGRID annotation JSON file.

        Args:
            json_path: Path to annotation JSON file
            split: 'train', 'val', or 'test' (auto-detected from path if None)
            selected_classes: Optional filter for specific HaGRID classes
            max_samples_per_class: Optional limit on samples imported per class

        Returns:
            HagridParseResult with parsed DatasetSample objects and audit issues
        """
        p = Path(json_path)
        if not p.exists():
            raise FileNotFoundError(f"Annotation file not found: {p}")

        # Detect split from path if not provided
        if not split:
            path_str = str(p).lower()
            if "train" in path_str:
                split = "train"
            elif "val" in path_str:
                split = "val"
            elif "test" in path_str:
                split = "test"
            else:
                split = "train"

        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            res = HagridParseResult(source_split=split)
            res.issues.append(
                ParseIssue(
                    image_id=p.name,
                    issue_type="corrupt_json",
                    detail=f"Failed to parse JSON file {p.name}: {e}",
                    severity="error",
                )
            )
            res.error_count += 1
            return res

        if not isinstance(data, dict):
            res = HagridParseResult(source_split=split)
            res.issues.append(
                ParseIssue(
                    image_id=p.name,
                    issue_type="invalid_format",
                    detail=f"Expected JSON object at top-level of {p.name}, got {type(data).__name__}",
                    severity="error",
                )
            )
            res.error_count += 1
            return res

        return self.parse_dict(
            data=data,
            split=split,
            selected_classes=selected_classes,
            max_samples_per_class=max_samples_per_class,
        )

    def parse_dict(
        self,
        data: Dict[str, Any],
        split: str = "train",
        selected_classes: Optional[Set[str]] = None,
        max_samples_per_class: Optional[int] = None,
    ) -> HagridParseResult:
        """
        Parse raw HaGRID annotations dictionary.

        Format:
        {
          "image_uuid": {
             "bboxes": [...],
             "labels": [...],
             "hand_landmarks": [...],  # or "landmarks"
             "united_bbox": [...],
             "united_label": [...],
             "user_id": "...",
             "meta": {...}
          }
        }
        """
        result = HagridParseResult(source_split=split)
        samples_per_class: Dict[str, int] = {}

        for image_id, record in data.items():
            result.total_images_processed += 1

            if not isinstance(record, dict):
                result.issues.append(
                    ParseIssue(
                        image_id=str(image_id),
                        issue_type="invalid_record",
                        detail=f"Record value for image {image_id} is not an object",
                        severity="error",
                    )
                )
                result.error_count += 1
                continue

            extracted_samples, issues = self._parse_image_record(
                image_id=str(image_id),
                record=record,
                split=split,
                selected_classes=selected_classes,
                samples_per_class=samples_per_class,
                max_samples_per_class=max_samples_per_class,
            )

            result.issues.extend(issues)

            for s in extracted_samples:
                result.samples.append(s)
                result.valid_samples_count += 1
                result.class_distribution[s.gesture_id] = (
                    result.class_distribution.get(s.gesture_id, 0) + 1
                )
                samples_per_class[s.gesture_id] = samples_per_class.get(s.gesture_id, 0) + 1

        return result

    def _parse_image_record(
        self,
        image_id: str,
        record: Dict[str, Any],
        split: str,
        selected_classes: Optional[Set[str]],
        samples_per_class: Dict[str, int],
        max_samples_per_class: Optional[int],
    ) -> Tuple[List[DatasetSample], List[ParseIssue]]:
        """Extract valid DatasetSample objects from an individual image annotation."""
        samples: List[DatasetSample] = []
        issues: List[ParseIssue] = []

        labels = record.get("labels", [])
        bboxes = record.get("bboxes", [])
        # HaGRID supports both 'hand_landmarks' and 'landmarks'
        raw_landmarks = record.get("hand_landmarks") or record.get("landmarks", [])
        user_id = record.get("user_id") or "hagrid_anonymous"
        meta = record.get("meta") or {}
        united_bbox = record.get("united_bbox")
        united_label = record.get("united_label")

        if not labels or not isinstance(labels, list):
            issues.append(
                ParseIssue(
                    image_id=image_id,
                    issue_type="missing_labels",
                    detail=f"Image {image_id} has no labels array or empty labels",
                    severity="warning",
                )
            )
            return samples, issues

        if not raw_landmarks or not isinstance(raw_landmarks, list):
            issues.append(
                ParseIssue(
                    image_id=image_id,
                    issue_type="missing_landmarks",
                    detail=f"Image {image_id} has no hand landmark keypoints",
                    severity="warning",
                )
            )
            return samples, issues

        # Check for two-handed gesture flag
        primary_label = labels[0] if labels else "unknown"
        is_two_handed = (
            primary_label in TWO_HANDED_GESTURES
            or (united_label and isinstance(united_label, list) and united_label[0] in TWO_HANDED_GESTURES)
        )

        # Iterate over each hand in the image
        num_hands = len(raw_landmarks)
        for hand_idx in range(num_hands):
            hand_pts = raw_landmarks[hand_idx]
            hand_label = labels[hand_idx] if hand_idx < len(labels) else primary_label
            hand_bbox = bboxes[hand_idx] if hand_idx < len(bboxes) else None

            # Filter selected classes if specified
            if selected_classes and hand_label not in selected_classes:
                continue

            # Class mapping lookup
            mapping = self._mappings.get(hand_label)
            if not mapping:
                # Default behavior for unmapped classes: generate a mapped gesture
                target_id = f"HG_{hand_label.upper()}"
                target_name = hand_label.replace("_", " ").title()
                action = "map"
            else:
                action = mapping.get("action", "map")
                if action == "skip":
                    continue
                target_id = mapping.get("target_id") or f"HG_{hand_label.upper()}"
                target_name = mapping.get("target_name") or hand_label.replace("_", " ").title()

            # Check max samples per class cap
            current_class_count = samples_per_class.get(target_id, 0)
            if max_samples_per_class is not None and current_class_count >= max_samples_per_class:
                continue

            # Validate landmarks array
            if not isinstance(hand_pts, list) or len(hand_pts) != 21:
                issues.append(
                    ParseIssue(
                        image_id=image_id,
                        issue_type="invalid_landmark_count",
                        detail=f"Hand #{hand_idx} in {image_id} has {len(hand_pts) if isinstance(hand_pts, list) else 0} landmarks, expected exactly 21",
                        severity="error",
                    )
                )
                continue

            # Validate coordinate values
            valid_coords, coord_issue = self._validate_and_build_coordinates(hand_pts, image_id, hand_idx)
            if coord_issue:
                issues.append(coord_issue)
                if coord_issue.severity == "error":
                    continue

            # Generate unique deterministic sample ID
            sample_id = f"hagrid_{image_id[:16]}_{split}_h{hand_idx}"

            # Assemble full annotations metadata
            annotation_meta = {
                "hagrid_class": hand_label,
                "bbox": hand_bbox,
                "is_two_handed": is_two_handed,
                "hand_index": hand_idx,
                "total_hands": num_hands,
                "user_meta": meta,
            }
            if united_bbox:
                annotation_meta["united_bbox"] = united_bbox
            if united_label:
                annotation_meta["united_label"] = united_label

            now_iso = datetime.now().isoformat()
            sample = DatasetSample(
                sample_id=sample_id,
                gesture_id=target_id,
                gesture_name=target_name,
                timestamp=now_iso,
                handedness="Unknown",  # Handedness is not annotated in HaGRIDv2
                handedness_confidence=1.0,
                landmarks=valid_coords,
                session_id=f"hagrid_import_{split}",
                source="hagrid",
                source_dataset_version="HaGRIDv2",
                source_image_id=image_id,
                source_split=split,
                source_user_id=str(user_id),
                coordinate_format="hagrid_normalized_2d",
                landmark_dimension=2,
                annotations=annotation_meta,
                imported_at=now_iso,
            )
            samples.append(sample)

        return samples, issues

    def _validate_and_build_coordinates(
        self,
        hand_pts: List[Any],
        image_id: str,
        hand_idx: int,
    ) -> Tuple[List[LandmarkCoord], Optional[ParseIssue]]:
        """Validate 21 points for finiteness and bounds; build LandmarkCoord list."""
        coords: List[LandmarkCoord] = []
        has_slight_out_of_bounds = False

        for idx, pt in enumerate(hand_pts):
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                return [], ParseIssue(
                    image_id=image_id,
                    issue_type="invalid_coordinate_structure",
                    detail=f"Landmark #{idx} of hand #{hand_idx} in {image_id} is not a valid 2D point [x, y]",
                    severity="error",
                )

            x = float(pt[0])
            y = float(pt[1])

            # Check finiteness (no NaN or Inf)
            if not (math.isfinite(x) and math.isfinite(y)):
                return [], ParseIssue(
                    image_id=image_id,
                    issue_type="non_finite_coordinates",
                    detail=f"Landmark #{idx} of hand #{hand_idx} in {image_id} contains NaN or Inf: ({x}, {y})",
                    severity="error",
                )

            # Check extreme out of bounds (> 2.0 or < -1.0)
            if x < -0.5 or x > 1.5 or y < -0.5 or y > 1.5:
                return [], ParseIssue(
                    image_id=image_id,
                    issue_type="extreme_out_of_bounds",
                    detail=f"Landmark #{idx} in {image_id} has extreme coordinates: ({x:.2f}, {y:.2f})",
                    severity="error",
                )

            # Check mild out of bounds (slight edge crossing, clamp to [0.0, 1.0] for safety)
            if x < 0.0 or x > 1.0 or y < 0.0 or y > 1.0:
                has_slight_out_of_bounds = True
                clamped_x = max(0.0, min(1.0, x))
                clamped_y = max(0.0, min(1.0, y))
            else:
                clamped_x = x
                clamped_y = y

            coords.append(
                LandmarkCoord(
                    index=idx,
                    x=clamped_x,
                    y=clamped_y,
                    z=None,  # Do not fabricate z-depth!
                )
            )

        issue = None
        if has_slight_out_of_bounds:
            issue = ParseIssue(
                image_id=image_id,
                issue_type="clamped_coordinates",
                detail=f"Hand #{hand_idx} in {image_id} had coordinates slightly outside [0, 1] clamped to frame boundary",
                severity="warning",
            )

        return coords, issue
