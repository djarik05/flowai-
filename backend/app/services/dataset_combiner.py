"""
Dataset Combiner Service for GestureFlow AI.

Combines custom webcam samples and public HaGRID samples into machine-learning ready datasets.
Features:
- Enforces coordinate compatibility (Group A: 2D, Group B: 3D)
- Supports '2d_projection' (drops z on 3D data), '2d_only', or '3d_only'
- Preserves subject-level split boundaries to prevent training/test data leakage
- Exports combined datasets in both flattened ML CSV and structured JSON
"""

import csv
import json
import logging
import math
import random
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.schemas.public_dataset import (
    DatasetCombineRequest,
    DatasetCombineResponse,
    DatasetSourcesResponse,
)
from app.services.dataset_service import DatasetService
from app.services.hagrid_constants import DATASET_ATTRIBUTION_METADATA
from app.services.hagrid_importer import HagridImporterService

logger = logging.getLogger(__name__)


class DatasetCombinerService:
    """
    Combines heterogeneous hand gesture datasets with strict coordinate
    compatibility and leakage prevention.
    """

    def __init__(
        self,
        base_dataset_dir: Optional[Path] = None,
        dataset_service: Optional[DatasetService] = None,
        hagrid_importer: Optional[HagridImporterService] = None,
    ) -> None:
        """Initialize combiner with dataset directory and services."""
        self._lock = threading.RLock()
        self._base_dir = Path(base_dataset_dir) if base_dataset_dir else settings.resolved_dataset_dir
        self._custom_samples_dir = self._base_dir / "samples"
        self._hagrid_imports_dir = self._base_dir / "public" / "hagrid" / "imports"
        self._combined_dir = self._base_dir / "combined"

        self._dataset_service = dataset_service or DatasetService(self._base_dir)
        self._hagrid_importer = hagrid_importer or HagridImporterService(self._base_dir)

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create combined datasets directory."""
        with self._lock:
            self._combined_dir.mkdir(parents=True, exist_ok=True)

    def get_sources_overview(self) -> DatasetSourcesResponse:
        """Analyze sample counts and coordinate formats across custom and public repositories."""
        with self._lock:
            custom_count = 0
            hagrid_count = 0
            coord_formats: Dict[str, int] = {}
            gesture_breakdown: Dict[str, Dict[str, int]] = {}

            # Scan custom samples
            if self._custom_samples_dir.exists():
                for g_dir in self._custom_samples_dir.iterdir():
                    if g_dir.is_dir():
                        gid = g_dir.name
                        gesture_breakdown.setdefault(gid, {"custom": 0, "hagrid": 0})
                        for sf in g_dir.glob("*.json"):
                            try:
                                with open(sf, "r", encoding="utf-8") as f:
                                    s = json.load(f)
                                custom_count += 1
                                fmt = s.get("coordinate_format", "mediapipe_normalized_3d")
                                coord_formats[fmt] = coord_formats.get(fmt, 0) + 1
                                gesture_breakdown[gid]["custom"] += 1
                            except Exception:
                                pass

            # Scan HaGRID imported samples
            if self._hagrid_imports_dir.exists():
                for g_dir in self._hagrid_imports_dir.iterdir():
                    if g_dir.is_dir():
                        gid = g_dir.name
                        gesture_breakdown.setdefault(gid, {"custom": 0, "hagrid": 0})
                        for sf in g_dir.glob("*.json"):
                            try:
                                with open(sf, "r", encoding="utf-8") as f:
                                    s = json.load(f)
                                hagrid_count += 1
                                fmt = s.get("coordinate_format", "hagrid_normalized_2d")
                                coord_formats[fmt] = coord_formats.get(fmt, 0) + 1
                                gesture_breakdown[gid]["hagrid"] += 1
                            except Exception:
                                pass

            return DatasetSourcesResponse(
                total_samples=custom_count + hagrid_count,
                custom_samples_count=custom_count,
                hagrid_samples_count=hagrid_count,
                coordinate_formats=coord_formats,
                gesture_breakdown=gesture_breakdown,
            )

    def combine_datasets(self, request: DatasetCombineRequest) -> DatasetCombineResponse:
        """
        Combine selected dataset sources applying coordinate alignment and leakage-free splits.

        Args:
            request: Configuration parameters for combination and splits

        Returns:
            DatasetCombineResponse with export paths and distribution summary
        """
        with self._lock:
            # Step 1: Collect candidates
            candidates: List[DatasetSample] = []

            if request.include_custom and self._custom_samples_dir.exists():
                for g_dir in self._custom_samples_dir.iterdir():
                    if not g_dir.is_dir():
                        continue
                    if request.selected_gestures and g_dir.name not in request.selected_gestures:
                        continue
                    for sf in g_dir.glob("*.json"):
                        try:
                            with open(sf, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            candidates.append(DatasetSample(**data))
                        except Exception as e:
                            logger.warning("Skipping invalid custom sample %s: %s", sf, e)

            if request.include_hagrid and self._hagrid_imports_dir.exists():
                for g_dir in self._hagrid_imports_dir.iterdir():
                    if not g_dir.is_dir():
                        continue
                    if request.selected_gestures and g_dir.name not in request.selected_gestures:
                        continue
                    for sf in g_dir.glob("*.json"):
                        try:
                            with open(sf, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            candidates.append(DatasetSample(**data))
                        except Exception as e:
                            logger.warning("Skipping invalid HaGRID sample %s: %s", sf, e)

            if not candidates:
                raise ValueError("No samples available to combine matching selected sources and filters.")

            # Step 2: Coordinate format compatibility check and projection
            mode = request.compatibility_mode
            compatible_samples: List[Dict[str, Any]] = []
            output_dim = 2 if mode in ("2d_projection", "2d_only") else 3
            output_fmt = "normalized_2d" if output_dim == 2 else "mediapipe_normalized_3d"

            for s in candidates:
                # 3D only mode
                if mode == "3d_only":
                    if s.landmark_dimension != 3 or any(lm.z is None for lm in s.landmarks):
                        continue  # Skip 2D samples
                    coords_dict = [{"index": lm.index, "x": lm.x, "y": lm.y, "z": lm.z} for lm in s.landmarks]
                # 2D only mode
                elif mode == "2d_only":
                    if s.landmark_dimension != 2:
                        continue  # Skip 3D samples
                    coords_dict = [{"index": lm.index, "x": lm.x, "y": lm.y} for lm in s.landmarks]
                # 2D projection mode (accepts both, projects 3D to 2D by dropping z)
                elif mode == "2d_projection":
                    coords_dict = [{"index": lm.index, "x": lm.x, "y": lm.y} for lm in s.landmarks]
                else:
                    raise ValueError(f"Unknown compatibility mode '{mode}'. Choose '2d_projection', '2d_only', or '3d_only'.")

                # Determine subject ID for leakage-free splitting
                subject_id = s.source_user_id or s.session_id or f"subj_{s.sample_id}"

                compatible_samples.append({
                    "sample_id": s.sample_id,
                    "gesture_id": s.gesture_id,
                    "gesture_name": s.gesture_name,
                    "source": s.source,
                    "subject_id": subject_id,
                    "landmarks": coords_dict,
                })

            if not compatible_samples:
                raise ValueError(
                    f"Zero samples satisfied coordinate compatibility mode '{mode}'. "
                    "Ensure your dataset sources contain samples with the selected dimension."
                )

            # Step 3: Leakage-Free Subject Split Assignment
            # Group samples by subject_id
            subjects_map: Dict[str, List[Dict[str, Any]]] = {}
            for cs in compatible_samples:
                subjects_map.setdefault(cs["subject_id"], []).append(cs)

            subjects_list = list(subjects_map.keys())
            # Deterministic reproducible shuffle
            random.Random(42).shuffle(subjects_list)

            num_subjects = len(subjects_list)
            train_cut = int(num_subjects * request.train_ratio)
            val_cut = int(num_subjects * (request.train_ratio + request.val_ratio))

            train_subjects = set(subjects_list[:train_cut])
            val_subjects = set(subjects_list[train_cut:val_cut])
            test_subjects = set(subjects_list[val_cut:])

            # Fallback if few subjects
            if not val_subjects and num_subjects >= 2:
                val_subjects.add(subjects_list[-1])
                train_subjects.discard(subjects_list[-1])

            train_samples: List[Dict[str, Any]] = []
            val_samples: List[Dict[str, Any]] = []
            test_samples: List[Dict[str, Any]] = []

            for subj, smp_list in subjects_map.items():
                if subj in train_subjects:
                    split_name = "train"
                    target_bucket = train_samples
                elif subj in val_subjects:
                    split_name = "val"
                    target_bucket = val_samples
                else:
                    split_name = "test"
                    target_bucket = test_samples

                for s in smp_list:
                    s["split"] = split_name
                    target_bucket.append(s)

            # Step 4: Save combined version and files
            combined_id = f"comb_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            target_dir = self._combined_dir / combined_id
            target_dir.mkdir(parents=True, exist_ok=True)

            all_combined = train_samples + val_samples + test_samples

            # Calculate class distributions
            class_counts: Dict[str, int] = {}
            for item in all_combined:
                gid = item["gesture_id"]
                class_counts[gid] = class_counts.get(gid, 0) + 1

            # Write structured JSON
            json_file = target_dir / "combined_dataset.json"
            combined_json_content = {
                "combined_id": combined_id,
                "name": request.name,
                "created_at": datetime.now().isoformat(),
                "total_samples": len(all_combined),
                "splits_count": {
                    "train": len(train_samples),
                    "val": len(val_samples),
                    "test": len(test_samples),
                },
                "unique_subjects": num_subjects,
                "coordinate_format": output_fmt,
                "landmark_dimension": output_dim,
                "classes": list(class_counts.keys()),
                "sample_counts_by_class": class_counts,
                "attribution": DATASET_ATTRIBUTION_METADATA if request.include_hagrid else "GestureFlow AI Custom",
                "samples": all_combined,
            }
            with open(json_file, "w", encoding="utf-8") as jf:
                json.dump(combined_json_content, jf, indent=2, ensure_ascii=False)

            # Write ML-ready Flattened CSV
            csv_file = target_dir / "combined_dataset.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as cf:
                writer = csv.writer(cf)
                # Header
                header = ["sample_id", "gesture_id", "gesture_name", "split", "source", "subject_id"]
                if output_dim == 2:
                    for i in range(21):
                        header.extend([f"x_{i}", f"y_{i}"])
                else:
                    for i in range(21):
                        header.extend([f"x_{i}", f"y_{i}", f"z_{i}"])
                writer.writerow(header)

                for item in all_combined:
                    row = [
                        item["sample_id"],
                        item["gesture_id"],
                        item["gesture_name"],
                        item["split"],
                        item["source"],
                        item["subject_id"],
                    ]
                    for lm in item["landmarks"]:
                        row.append(lm["x"])
                        row.append(lm["y"])
                        if output_dim == 3:
                            row.append(lm.get("z", 0.0))
                    writer.writerow(row)

            return DatasetCombineResponse(
                combined_id=combined_id,
                name=request.name,
                total_samples=len(all_combined),
                train_samples=len(train_samples),
                val_samples=len(val_samples),
                test_samples=len(test_samples),
                unique_subjects=num_subjects,
                coordinate_format=output_fmt,
                landmark_dimension=output_dim,
                classes_included=list(class_counts.keys()),
                sample_counts_by_class=class_counts,
                export_csv_filename=f"combined_{combined_id}.csv",
                export_json_filename=f"combined_{combined_id}.json",
                created_at=combined_json_content["created_at"],
            )

    def list_combined_datasets(self) -> List[Dict[str, Any]]:
        """List all generated combined dataset versions."""
        with self._lock:
            results: List[Dict[str, Any]] = []
            if not self._combined_dir.exists():
                return results

            for c_dir in sorted(self._combined_dir.iterdir(), reverse=True):
                if c_dir.is_dir():
                    jf = c_dir / "combined_dataset.json"
                    if jf.exists():
                        try:
                            with open(jf, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            results.append({
                                "combined_id": meta.get("combined_id", c_dir.name),
                                "name": meta.get("name", c_dir.name),
                                "total_samples": meta.get("total_samples", 0),
                                "splits_count": meta.get("splits_count", {}),
                                "coordinate_format": meta.get("coordinate_format", "2d"),
                                "classes": meta.get("classes", []),
                                "created_at": meta.get("created_at"),
                            })
                        except Exception as e:
                            logger.warning("Error reading combined dataset %s: %s", jf, e)
            return results
