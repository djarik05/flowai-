"""
HaGRID Dataset Importer Service for GestureFlow AI.

Coordinates:
- Extraction of downloaded or local annotation archives
- Invocation of HagridAnnotationParser with class mappings
- Dynamic registration of newly created gestures
- Atomic sample persistence in public dataset storage (backend/datasets/public/hagrid/imports/)
- Import manifest generation and validation tracking
"""

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.schemas.dataset import DatasetSample
from app.schemas.public_dataset import (
    HagridClassMapping,
    PublicJobStatusResponse,
)
from app.services.gesture_service import GestureService
from app.services.hagrid_constants import (
    DATASET_ATTRIBUTION_METADATA,
    DEFAULT_GESTUREFLOW_MAPPINGS,
)
from app.services.hagrid_downloader import HagridDownloadManager
from app.services.hagrid_parser import HagridAnnotationParser, HagridParseResult

logger = logging.getLogger(__name__)


class HagridImporterService:
    """
    Manages end-to-end ingestion of HaGRID dataset annotations into GestureFlow AI.
    """

    def __init__(
        self,
        base_dataset_dir: Optional[Path] = None,
        gesture_service: Optional[GestureService] = None,
        download_manager: Optional[HagridDownloadManager] = None,
    ) -> None:
        """Initialize HaGRID importer with storage directory and dependent services."""
        self._lock = threading.RLock()
        self._base_dir = Path(base_dataset_dir) if base_dataset_dir else settings.resolved_dataset_dir
        self._hagrid_dir = self._base_dir / "public" / "hagrid"
        self._imports_dir = self._hagrid_dir / "imports"
        self._extracted_dir = self._hagrid_dir / "extracted"
        self._annotations_dir = self._hagrid_dir / "annotations"
        self._manifests_dir = self._hagrid_dir / "manifests"
        self._mappings_file = self._hagrid_dir / "mappings.json"

        self._gesture_service = gesture_service or GestureService()
        self._download_manager = download_manager or HagridDownloadManager(self._base_dir)

        self._ensure_directories()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._cancel_events: Dict[str, threading.Event] = {}

    def _ensure_directories(self) -> None:
        """Create storage hierarchy and default mappings."""
        with self._lock:
            self._imports_dir.mkdir(parents=True, exist_ok=True)
            self._extracted_dir.mkdir(parents=True, exist_ok=True)
            self._annotations_dir.mkdir(parents=True, exist_ok=True)
            self._manifests_dir.mkdir(parents=True, exist_ok=True)

            if not self._mappings_file.exists():
                self._save_mappings(DEFAULT_GESTUREFLOW_MAPPINGS)

    def load_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load class mappings configuration."""
        with self._lock:
            try:
                if self._mappings_file.exists():
                    with open(self._mappings_file, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception as e:
                logger.error("Error reading mappings file: %s", e)
            return DEFAULT_GESTUREFLOW_MAPPINGS.copy()

    def _save_mappings(self, mappings: Dict[str, Dict[str, Any]]) -> None:
        """Persist class mappings configuration atomically."""
        with self._lock:
            tmp = self._mappings_file.with_suffix(".tmp")
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(mappings, f, indent=2, ensure_ascii=False)
                os.replace(tmp, self._mappings_file)
            except Exception as e:
                logger.error("Error saving mappings file: %s", e)
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except Exception:
                        pass

    def update_mapping(self, hagrid_class: str, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update single class mapping."""
        with self._lock:
            mappings = self.load_mappings()
            mappings[hagrid_class] = mapping_data
            self._save_mappings(mappings)
            return mappings[hagrid_class]

    def set_all_mappings(self, new_mappings: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Replace all mappings."""
        with self._lock:
            self._save_mappings(new_mappings)
            return new_mappings

    def get_imported_sample_counts(self) -> Dict[str, int]:
        """Count imported samples per gesture class."""
        with self._lock:
            counts: Dict[str, int] = {}
            for g_dir in self._imports_dir.iterdir():
                if g_dir.is_dir():
                    counts[g_dir.name] = len(list(g_dir.glob("*.json")))
            return counts

    def get_imported_samples(
        self,
        gesture_id: Optional[str] = None,
        split: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DatasetSample], int]:
        """Query imported HaGRID samples."""
        with self._lock:
            all_samples: List[DatasetSample] = []
            dirs_to_check = [self._imports_dir / gesture_id] if gesture_id else [
                d for d in self._imports_dir.iterdir() if d.is_dir()
            ]

            for g_dir in dirs_to_check:
                if not g_dir.exists():
                    continue
                for sf in g_dir.glob("*.json"):
                    try:
                        with open(sf, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if split and data.get("source_split") != split:
                            continue
                        all_samples.append(DatasetSample(**data))
                    except Exception as e:
                        logger.warning("Error reading sample %s: %s", sf, e)

            total = len(all_samples)
            paginated = all_samples[offset : offset + limit]
            return paginated, total

    def start_import_job(
        self,
        source_type: str = "downloaded",
        local_annotation_path: Optional[str] = None,
        splits: Optional[List[str]] = None,
        selected_classes: Optional[List[str]] = None,
        max_samples_per_class: Optional[int] = None,
    ) -> str:
        """
        Start an asynchronous HaGRID annotation import job.

        Returns:
            job_id string
        """
        job_id = f"imp_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        cancel_ev = threading.Event()

        with self._lock:
            self._cancel_events[job_id] = cancel_ev
            self._jobs[job_id] = {
                "job_id": job_id,
                "job_type": "import",
                "status": "pending",
                "progress_percent": 0.0,
                "message": "Initializing import pipeline...",
                "source_type": source_type,
                "splits": splits or ["train", "val", "test"],
                "selected_classes": selected_classes,
                "max_samples_per_class": max_samples_per_class,
                "samples_imported": 0,
                "class_distribution": {},
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "error": None,
            }

        thread = threading.Thread(
            target=self._run_import_job,
            args=(
                job_id,
                source_type,
                local_annotation_path,
                splits or ["train", "val", "test"],
                selected_classes,
                max_samples_per_class,
                cancel_ev,
            ),
            name=f"HagridImporter-{job_id}",
            daemon=True,
        )
        thread.start()
        return job_id

    def get_job_status(self, job_id: str) -> Optional[PublicJobStatusResponse]:
        """Get telemetry and status of an import job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            return PublicJobStatusResponse(
                job_id=job["job_id"],
                job_type=job["job_type"],
                status=job["status"],
                progress_percent=job["progress_percent"],
                message=job["message"],
                details={
                    "samples_imported": job.get("samples_imported", 0),
                    "class_distribution": job.get("class_distribution", {}),
                    "source_type": job.get("source_type"),
                    "splits": job.get("splits", []),
                },
                started_at=job["started_at"],
                completed_at=job.get("completed_at"),
                error=job.get("error"),
            )

    def cancel_job(self, job_id: str) -> bool:
        """Cancel an ongoing import job."""
        with self._lock:
            if job_id in self._cancel_events:
                self._cancel_events[job_id].set()
                if job_id in self._jobs:
                    self._jobs[job_id]["status"] = "cancelled"
                    self._jobs[job_id]["message"] = "Import cancelled by user"
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
                return True
            return False

    def _run_import_job(
        self,
        job_id: str,
        source_type: str,
        local_annotation_path: Optional[str],
        splits: List[str],
        selected_classes: Optional[List[str]],
        max_samples_per_class: Optional[int],
        cancel_event: threading.Event,
    ) -> None:
        """Background import worker thread."""
        logger.info("Executing import job %s (source=%s, splits=%s)", job_id, source_type, splits)

        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "running"
                self._jobs[job_id]["message"] = "Locating annotation files..."

        try:
            # Step 1: Find or extract annotation files
            annotation_files: List[Tuple[Path, str]] = self._locate_annotation_files(
                source_type=source_type,
                local_path=local_annotation_path,
                splits=splits,
                cancel_event=cancel_event,
            )

            if not annotation_files:
                raise FileNotFoundError(
                    "No annotation files found. Please download annotations.zip or provide a valid local path to annotation JSON files."
                )

            # Step 2: Prepare parser with current class mappings
            mappings = self.load_mappings()
            self._handle_create_new_gestures(mappings, selected_classes)
            parser = HagridAnnotationParser(class_mappings=mappings)

            total_imported = 0
            overall_distribution: Dict[str, int] = {}
            total_files = len(annotation_files)

            sel_set = set(selected_classes) if selected_classes else None

            # Step 3: Parse and persist samples from each file
            for file_idx, (json_file, split) in enumerate(annotation_files):
                if cancel_event.is_set():
                    break

                with self._lock:
                    if job_id in self._jobs:
                        self._jobs[job_id]["message"] = (
                            f"Parsing {json_file.name} [{split}] ({file_idx + 1}/{total_files})..."
                        )

                parse_res = parser.parse_file(
                    json_path=json_file,
                    split=split,
                    selected_classes=sel_set,
                    max_samples_per_class=max_samples_per_class,
                )

                # Persist valid samples atomically
                for sample in parse_res.samples:
                    if cancel_event.is_set():
                        break
                    self._persist_sample(sample)
                    total_imported += 1
                    overall_distribution[sample.gesture_id] = (
                        overall_distribution.get(sample.gesture_id, 0) + 1
                    )

                pct = round(((file_idx + 1) / total_files) * 100, 1)
                with self._lock:
                    if job_id in self._jobs:
                        self._jobs[job_id]["progress_percent"] = pct
                        self._jobs[job_id]["samples_imported"] = total_imported
                        self._jobs[job_id]["class_distribution"] = overall_distribution

            # Step 4: Write import manifest
            manifest_file = self._manifests_dir / f"import_manifest_{job_id}.json"
            manifest_data = {
                "import_id": job_id,
                "dataset": "HaGRIDv2",
                "imported_at": datetime.now().isoformat(),
                "total_samples": total_imported,
                "class_distribution": overall_distribution,
                "splits": splits,
                "coordinate_format": "hagrid_normalized_2d",
                "landmark_dimension": 2,
                "attribution": DATASET_ATTRIBUTION_METADATA,
            }
            with open(manifest_file, "w", encoding="utf-8") as mf:
                json.dump(manifest_data, mf, indent=2, ensure_ascii=False)

            with self._lock:
                if job_id in self._jobs:
                    if cancel_event.is_set():
                        self._jobs[job_id]["status"] = "cancelled"
                        self._jobs[job_id]["message"] = f"Import cancelled. Saved {total_imported} samples."
                    else:
                        self._jobs[job_id]["status"] = "completed"
                        self._jobs[job_id]["progress_percent"] = 100.0
                        self._jobs[job_id]["message"] = (
                            f"Successfully imported {total_imported} HaGRID samples across {len(overall_distribution)} classes."
                        )
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()

        except Exception as e:
            logger.error("Import job %s error: %s", job_id, e, exc_info=True)
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id]["status"] = "error"
                    self._jobs[job_id]["error"] = str(e)
                    self._jobs[job_id]["message"] = f"Import failed: {e}"
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()

    def _locate_annotation_files(
        self,
        source_type: str,
        local_path: Optional[str],
        splits: List[str],
        cancel_event: threading.Event,
    ) -> List[Tuple[Path, str]]:
        """Identify JSON files to parse based on source mode."""
        found_files: List[Tuple[Path, str]] = []

        if source_type == "local_path" and local_path:
            lp = Path(local_path)
            if lp.is_file() and lp.suffix.lower() == ".json":
                split = "train"
                for s in ("val", "test", "train"):
                    if s in lp.name.lower():
                        split = s
                        break
                found_files.append((lp, split))
            elif lp.is_dir():
                for sf in lp.rglob("*.json"):
                    split = "train"
                    for s in ("val", "test", "train"):
                        if s in str(sf).lower():
                            split = s
                            break
                    if split in splits:
                        found_files.append((sf, split))
            return found_files

        # Otherwise check downloaded annotations in public/hagrid/
        ann_zip = self._hagrid_dir / "downloads" / "annotations.zip"
        if ann_zip.exists():
            # Check if already extracted
            target_extracted = self._annotations_dir
            if not any(target_extracted.rglob("*.json")):
                logger.info("Extracting %s to %s...", ann_zip.name, target_extracted)
                self._download_manager.safe_extract_zip(
                    zip_path=ann_zip,
                    destination_dir=target_extracted,
                    cancel_event=cancel_event,
                )

        # Search for JSON files in extracted directory
        for target_dir in (self._annotations_dir, self._extracted_dir):
            if target_dir.exists():
                for jf in target_dir.rglob("*.json"):
                    path_str = str(jf).lower()
                    split = "train"
                    if "val" in path_str:
                        split = "val"
                    elif "test" in path_str:
                        split = "test"
                    if split in splits:
                        found_files.append((jf, split))

        return found_files

    def _handle_create_new_gestures(
        self,
        mappings: Dict[str, Dict[str, Any]],
        selected_classes: Optional[List[str]],
    ) -> None:
        """Register newly created GestureFlow gestures for mappings configured as 'create_new'."""
        for hagrid_class, cfg in mappings.items():
            if selected_classes and hagrid_class not in selected_classes:
                continue

            if cfg.get("action") == "create_new":
                name = cfg.get("target_name") or hagrid_class.replace("_", " ").title()
                desc = f"Imported gesture class from HaGRID ({hagrid_class})"
                # Check if gesture already exists by name
                existing = [g for g in self._gesture_service.get_all() if g.name.lower() == name.lower()]
                if existing:
                    cfg["target_id"] = existing[0].id
                    cfg["action"] = "map"
                else:
                    new_g = self._gesture_service.create({
                        "name": name,
                        "description": desc,
                        "type": "static",
                        "action": "no_action",
                        "confidence_threshold": cfg.get("confidence_threshold", 0.8),
                    })
                    cfg["target_id"] = new_g.id
                    cfg["action"] = "map"

    def _persist_sample(self, sample: DatasetSample) -> None:
        """Save an imported DatasetSample atomically under public/hagrid/imports/{gesture_id}/."""
        g_dir = self._imports_dir / sample.gesture_id
        g_dir.mkdir(parents=True, exist_ok=True)

        target_file = g_dir / f"{sample.sample_id}.json"
        tmp_file = target_file.with_suffix(".tmp")

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(sample.model_dump(), f, indent=2, ensure_ascii=False)

        os.replace(tmp_file, target_file)
