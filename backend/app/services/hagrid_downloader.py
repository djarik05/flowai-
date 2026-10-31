"""
HaGRID Selective Download Manager for GestureFlow AI.

Manages background downloads of official HaGRIDv2 annotation and image archives.
Features:
- Streamed chunked downloads (zero complete-in-RAM buffering)
- Job cancellation & retry support
- Zip integrity verification
- Duplicate download prevention
- Disk space check & warnings
- Download manifest persistence
"""

import json
import logging
import os
import shutil
import threading
import time
import urllib.request
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.schemas.public_dataset import PublicJobStatusResponse
from app.services.hagrid_constants import (
    DATASET_ATTRIBUTION_METADATA,
    HAGRID_ANNOTATIONS_URL,
    HAGRID_CLASS_SIZES,
    HAGRID_GESTURE_URLS,
)

logger = logging.getLogger(__name__)


class HagridDownloadManager:
    """
    Manages selective downloads of HaGRID dataset archives.
    """

    def __init__(self, base_dataset_dir: Optional[Path] = None) -> None:
        """Initialize download manager with storage directory."""
        self._lock = threading.RLock()
        self._base_dir = Path(base_dataset_dir) if base_dataset_dir else settings.resolved_dataset_dir
        self._hagrid_dir = self._base_dir / "public" / "hagrid"
        self._downloads_dir = self._hagrid_dir / "downloads"
        self._extracted_dir = self._hagrid_dir / "extracted"
        self._manifests_dir = self._hagrid_dir / "manifests"
        self._manifest_file = self._manifests_dir / "download_manifest.json"

        self._ensure_directories()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._cancel_events: Dict[str, threading.Event] = {}

    def _ensure_directories(self) -> None:
        """Create required directories and initialize download manifest."""
        with self._lock:
            self._downloads_dir.mkdir(parents=True, exist_ok=True)
            self._extracted_dir.mkdir(parents=True, exist_ok=True)
            self._manifests_dir.mkdir(parents=True, exist_ok=True)
            if not self._manifest_file.exists():
                self._save_manifest({
                    "dataset": "HaGRIDv2",
                    "attribution": DATASET_ATTRIBUTION_METADATA,
                    "downloads": {},
                    "updated_at": datetime.now().isoformat(),
                })

    def _load_manifest(self) -> Dict[str, Any]:
        """Load download manifest from disk."""
        with self._lock:
            try:
                if self._manifest_file.exists():
                    with open(self._manifest_file, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception as e:
                logger.error("Error reading download manifest: %s", e)
            return {"dataset": "HaGRIDv2", "downloads": {}, "updated_at": datetime.now().isoformat()}

    def _save_manifest(self, manifest: Dict[str, Any]) -> None:
        """Save download manifest atomically."""
        with self._lock:
            manifest["updated_at"] = datetime.now().isoformat()
            tmp = self._manifest_file.with_suffix(".tmp")
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                os.replace(tmp, self._manifest_file)
            except Exception as e:
                logger.error("Error writing download manifest: %s", e)
                if tmp.exists():
                    try:
                        tmp.unlink()
                    except Exception:
                        pass

    def check_disk_space(self, required_bytes: int) -> Tuple[bool, int, str]:
        """
        Check available disk space.

        Returns:
            (has_enough_space, free_bytes, message)
        """
        try:
            total, used, free = shutil.disk_usage(self._downloads_dir)
            has_enough = free >= required_bytes
            free_gb = free / (1024**3)
            req_gb = required_bytes / (1024**3)
            if not has_enough:
                msg = f"Insufficient disk space: {req_gb:.1f} GB required, only {free_gb:.1f} GB available on disk."
            else:
                msg = f"Disk check passed: {req_gb:.1f} GB required, {free_gb:.1f} GB free."
            return has_enough, free, msg
        except Exception as e:
            return True, 0, f"Could not determine disk usage: {e}"

    def verify_zip_archive(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Verify ZIP archive integrity.

        Returns:
            (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File {file_path.name} does not exist"
        if file_path.stat().st_size == 0:
            return False, f"File {file_path.name} is empty (0 bytes)"

        if not zipfile.is_zipfile(file_path):
            return False, f"File {file_path.name} is not a valid ZIP file"

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # Test zip integrity (checks CRC on header/files)
                bad_file = zf.testzip()
                if bad_file:
                    return False, f"Corrupted file inside archive: {bad_file}"
            return True, None
        except Exception as e:
            return False, f"ZIP verification failed: {e}"

    def safe_extract_zip(
        self,
        zip_path: Path,
        destination_dir: Path,
        cancel_event: Optional[threading.Event] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[str]:
        """
        Safely extract ZIP archive preventing directory traversal (Zip Slip vulnerability).

        Args:
            zip_path: Path to zip file
            destination_dir: Target directory
            cancel_event: Cancellation event
            progress_callback: Optional progress reporter (pct, message)

        Returns:
            List of extracted relative file paths
        """
        extracted_files: List[str] = []
        destination_dir.mkdir(parents=True, exist_ok=True)
        dest_resolved = destination_dir.resolve()

        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.infolist()
            total_members = len(members)

            for idx, member in enumerate(members):
                if cancel_event and cancel_event.is_set():
                    raise InterruptedError("Extraction cancelled by user")

                # Security check: Prevent path traversal
                target_path = (destination_dir / member.filename).resolve()
                if not str(target_path).startswith(str(dest_resolved)):
                    logger.warning("Skipping malicious path traversal member in zip: %s", member.filename)
                    continue

                zf.extract(member, destination_dir)
                extracted_files.append(str(member.filename))

                if progress_callback and total_members > 0:
                    pct = round((idx + 1) / total_members * 100, 1)
                    progress_callback(pct, f"Extracting {member.filename}")

        return extracted_files

    def start_download_job(
        self,
        download_annotations: bool = True,
        target_classes: Optional[List[str]] = None,
        force_redownload: bool = False,
    ) -> str:
        """
        Initiate a selective background download job.

        Returns:
            job_id string
        """
        targets = target_classes or []
        job_id = f"dl_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        # Calculate estimated total size in bytes
        est_bytes = 0
        if download_annotations:
            est_bytes += int(2.0 * (1024**3))  # ~2 GB for annotations
        for t in targets:
            size_gb = HAGRID_CLASS_SIZES.get(t, 42.0)
            est_bytes += int(size_gb * (1024**3))

        has_space, free_bytes, space_msg = self.check_disk_space(est_bytes)
        if not has_space:
            logger.warning("Disk space warning: %s", space_msg)

        cancel_ev = threading.Event()

        with self._lock:
            self._cancel_events[job_id] = cancel_ev
            self._jobs[job_id] = {
                "job_id": job_id,
                "job_type": "download",
                "status": "pending",
                "progress_percent": 0.0,
                "message": "Initializing download queue...",
                "download_annotations": download_annotations,
                "targets": targets,
                "force_redownload": force_redownload,
                "estimated_bytes": est_bytes,
                "downloaded_bytes": 0,
                "total_bytes": est_bytes,
                "speed_mbps": 0.0,
                "current_file": None,
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "error": None,
                "disk_warning": None if has_space else space_msg,
            }

        thread = threading.Thread(
            target=self._run_download_job,
            args=(job_id, download_annotations, targets, force_redownload, cancel_ev),
            name=f"HagridDownloader-{job_id}",
            daemon=True,
        )
        thread.start()
        return job_id

    def get_job_status(self, job_id: str) -> Optional[PublicJobStatusResponse]:
        """Get status of an active or completed download job."""
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
                    "download_annotations": job.get("download_annotations", False),
                    "targets": job.get("targets", []),
                    "downloaded_bytes": job.get("downloaded_bytes", 0),
                    "total_bytes": job.get("total_bytes", 0),
                    "speed_mbps": job.get("speed_mbps", 0.0),
                    "current_file": job.get("current_file"),
                    "disk_warning": job.get("disk_warning"),
                },
                started_at=job["started_at"],
                completed_at=job.get("completed_at"),
                error=job.get("error"),
            )

    def cancel_job(self, job_id: str) -> bool:
        """Cancel an ongoing download job."""
        with self._lock:
            if job_id in self._cancel_events:
                self._cancel_events[job_id].set()
                if job_id in self._jobs:
                    self._jobs[job_id]["status"] = "cancelled"
                    self._jobs[job_id]["message"] = "Download cancelled by user"
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()
                logger.info("Cancelled download job %s", job_id)
                return True
            return False

    def _run_download_job(
        self,
        job_id: str,
        download_annotations: bool,
        targets: List[str],
        force_redownload: bool,
        cancel_event: threading.Event,
    ) -> None:
        """Background worker thread for download queue."""
        logger.info("Starting download job %s (annotations=%s, targets=%s)", job_id, download_annotations, targets)

        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "running"

        items_to_download: List[Tuple[str, str, Path]] = []
        if download_annotations:
            items_to_download.append(("annotations", HAGRID_ANNOTATIONS_URL, self._downloads_dir / "annotations.zip"))

        for target in targets:
            url = HAGRID_GESTURE_URLS.get(target)
            if url:
                dest = self._downloads_dir / f"{target}.zip"
                items_to_download.append((target, url, dest))
            else:
                logger.warning("Unknown HaGRID target class: %s", target)

        total_items = len(items_to_download)
        manifest = self._load_manifest()

        try:
            for item_idx, (name, url, dest_path) in enumerate(items_to_download):
                if cancel_event.is_set():
                    break

                with self._lock:
                    if job_id in self._jobs:
                        self._jobs[job_id]["current_file"] = dest_path.name
                        self._jobs[job_id]["message"] = f"Downloading {dest_path.name} ({item_idx + 1}/{total_items})..."

                # Check if already downloaded and valid
                if dest_path.exists() and not force_redownload:
                    is_valid, _ = self.verify_zip_archive(dest_path)
                    if is_valid:
                        logger.info("Archive %s already exists and is valid. Skipping download.", dest_path.name)
                        manifest["downloads"][name] = {
                            "filename": dest_path.name,
                            "url": url,
                            "size_bytes": dest_path.stat().st_size,
                            "verified": True,
                            "downloaded_at": datetime.now().isoformat(),
                        }
                        self._save_manifest(manifest)
                        continue

                # Stream download with chunking & progress
                self._download_file_stream(
                    url=url,
                    dest_path=dest_path,
                    job_id=job_id,
                    cancel_event=cancel_event,
                )

                if cancel_event.is_set():
                    break

                # Verify downloaded archive
                with self._lock:
                    if job_id in self._jobs:
                        self._jobs[job_id]["message"] = f"Verifying {dest_path.name} integrity..."

                is_valid, verify_err = self.verify_zip_archive(dest_path)
                if not is_valid:
                    raise IOError(f"Archive verification failed for {dest_path.name}: {verify_err}")

                manifest["downloads"][name] = {
                    "filename": dest_path.name,
                    "url": url,
                    "size_bytes": dest_path.stat().st_size,
                    "verified": True,
                    "downloaded_at": datetime.now().isoformat(),
                }
                self._save_manifest(manifest)

            with self._lock:
                if job_id in self._jobs:
                    if cancel_event.is_set():
                        self._jobs[job_id]["status"] = "cancelled"
                        self._jobs[job_id]["message"] = "Download job was cancelled."
                    else:
                        self._jobs[job_id]["status"] = "completed"
                        self._jobs[job_id]["progress_percent"] = 100.0
                        self._jobs[job_id]["message"] = "All requested archives downloaded and verified."
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()

        except Exception as e:
            logger.error("Download job %s failed: %s", job_id, e, exc_info=True)
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id]["status"] = "error"
                    self._jobs[job_id]["error"] = str(e)
                    self._jobs[job_id]["message"] = f"Download failed: {e}"
                    self._jobs[job_id]["completed_at"] = datetime.now().isoformat()

    def _download_file_stream(
        self,
        url: str,
        dest_path: Path,
        job_id: str,
        cancel_event: threading.Event,
        chunk_size: int = 128 * 1024,
    ) -> None:
        """Stream HTTP response directly to disk avoiding RAM exhaustion."""
        tmp_path = dest_path.with_suffix(".part")
        start_time = time.time()
        downloaded = 0

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GestureFlow-AI-Dataset-Manager/1.0"},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response, open(tmp_path, "wb") as out_file:
                total_size = response.headers.get("Content-Length")
                total_bytes = int(total_size) if total_size and total_size.isdigit() else 0

                last_update_time = time.time()

                while not cancel_event.is_set():
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    out_file.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_update_time >= 0.5:
                        elapsed = now - start_time
                        speed_mbps = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
                        pct = round((downloaded / total_bytes) * 100, 1) if total_bytes > 0 else 0.0

                        with self._lock:
                            if job_id in self._jobs:
                                self._jobs[job_id]["downloaded_bytes"] = downloaded
                                if total_bytes > 0:
                                    self._jobs[job_id]["total_bytes"] = total_bytes
                                    self._jobs[job_id]["progress_percent"] = pct
                                self._jobs[job_id]["speed_mbps"] = round(speed_mbps, 2)

                        last_update_time = now

            if cancel_event.is_set():
                if tmp_path.exists():
                    tmp_path.unlink()
                return

            # Atomic replace
            os.replace(tmp_path, dest_path)

        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise
