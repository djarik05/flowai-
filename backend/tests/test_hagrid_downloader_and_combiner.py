"""
Tests for HaGRID selective download manager, ZIP safety, and dataset combiner.
"""

import json
import zipfile
from pathlib import Path
import pytest
from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.schemas.public_dataset import DatasetCombineRequest
from app.services.dataset_combiner import DatasetCombinerService
from app.services.hagrid_downloader import HagridDownloadManager


@pytest.fixture
def temp_dataset_dir(tmp_path):
    """Temporary dataset storage sandbox."""
    d = tmp_path / "datasets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_zip_verification_valid_and_invalid(temp_dataset_dir):
    """Test ZIP archive integrity checking."""
    dl_mgr = HagridDownloadManager(base_dataset_dir=temp_dataset_dir)

    # 1. Non-existent file
    valid, err = dl_mgr.verify_zip_archive(temp_dataset_dir / "missing.zip")
    assert not valid
    assert "does not exist" in err

    # 2. Corrupt non-zip file
    corrupt_file = temp_dataset_dir / "corrupt.zip"
    corrupt_file.write_text("not a zip file", encoding="utf-8")
    valid, err = dl_mgr.verify_zip_archive(corrupt_file)
    assert not valid
    assert "not a valid ZIP" in err

    # 3. Valid zip file
    valid_file = temp_dataset_dir / "valid.zip"
    with zipfile.ZipFile(valid_file, "w") as zf:
        zf.writestr("test.json", '{"sample": 1}')
    valid, err = dl_mgr.verify_zip_archive(valid_file)
    assert valid
    assert err is None


def test_safe_zip_extraction_prevents_directory_traversal(temp_dataset_dir):
    """Verify security check blocks Zip Slip directory traversal attacks."""
    dl_mgr = HagridDownloadManager(base_dataset_dir=temp_dataset_dir)
    malicious_zip = temp_dataset_dir / "malicious.zip"
    extract_target = temp_dataset_dir / "extracted_safe"

    # Construct zip with directory traversal entry
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        zf.writestr("safe_file.txt", "safe content")
        zf.writestr("../outside.txt", "malicious payload")

    extracted = dl_mgr.safe_extract_zip(malicious_zip, extract_target)

    # safe_file.txt should be extracted, ../outside.txt should be rejected
    assert (extract_target / "safe_file.txt").exists()
    assert not (temp_dataset_dir / "outside.txt").exists()


def test_dataset_combiner_2d_projection(temp_dataset_dir):
    """Test combining custom 3D and HaGRID 2D samples via 2D projection."""
    custom_dir = temp_dataset_dir / "samples" / "G001"
    custom_dir.mkdir(parents=True, exist_ok=True)
    hagrid_dir = temp_dataset_dir / "public" / "hagrid" / "imports" / "G001"
    hagrid_dir.mkdir(parents=True, exist_ok=True)

    def make_lm(dim=3):
        return [
            {"index": i, "x": 0.5, "y": 0.5, "z": -0.05 if dim == 3 else None}
            for i in range(21)
        ]

    # Create 2 custom 3D samples from subject 'sess_user_1'
    for i in range(2):
        s = {
            "sample_id": f"custom_{i}",
            "gesture_id": "G001",
            "gesture_name": "Open Palm",
            "timestamp": "2026-10-30T10:00:00",
            "handedness": "Right",
            "handedness_confidence": 0.95,
            "landmarks": make_lm(3),
            "session_id": "sess_user_1",
            "source": "custom",
            "coordinate_format": "mediapipe_normalized_3d",
            "landmark_dimension": 3,
        }
        (custom_dir / f"custom_{i}.json").write_text(json.dumps(s), encoding="utf-8")

    # Create 2 HaGRID 2D samples from subject 'hagrid_user_2'
    for i in range(2):
        s = {
            "sample_id": f"hagrid_{i}",
            "gesture_id": "G001",
            "gesture_name": "Open Palm",
            "timestamp": "2026-10-30T10:00:00",
            "handedness": "Unknown",
            "handedness_confidence": 1.0,
            "landmarks": make_lm(2),
            "session_id": "hagrid_train",
            "source": "hagrid",
            "source_user_id": "hagrid_user_2",
            "coordinate_format": "hagrid_normalized_2d",
            "landmark_dimension": 2,
        }
        (hagrid_dir / f"hagrid_{i}.json").write_text(json.dumps(s), encoding="utf-8")

    combiner = DatasetCombinerService(base_dataset_dir=temp_dataset_dir)
    res = combiner.combine_datasets(
        DatasetCombineRequest(
            name="TestUnified_v1",
            include_custom=True,
            include_hagrid=True,
            compatibility_mode="2d_projection",
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15,
        )
    )

    assert res.total_samples == 4
    assert res.landmark_dimension == 2
    assert res.coordinate_format == "normalized_2d"
    assert res.unique_subjects == 2

    # Check that CSV and JSON export files were created
    out_dir = temp_dataset_dir / "combined" / res.combined_id
    assert (out_dir / "combined_dataset.csv").exists()
    assert (out_dir / "combined_dataset.json").exists()


def test_dataset_combiner_subject_split_preservation(temp_dataset_dir):
    """Verify that samples with the same subject ID are never split across train and test."""
    hagrid_dir = temp_dataset_dir / "public" / "hagrid" / "imports" / "G002"
    hagrid_dir.mkdir(parents=True, exist_ok=True)

    # 10 samples from subject A, 10 samples from subject B
    for subj in ("subj_alpha", "subj_beta"):
        for i in range(10):
            s = {
                "sample_id": f"{subj}_{i}",
                "gesture_id": "G002",
                "gesture_name": "Closed Fist",
                "timestamp": "2026-10-30T10:00:00",
                "handedness": "Unknown",
                "handedness_confidence": 1.0,
                "landmarks": [{"index": j, "x": 0.4, "y": 0.4, "z": None} for j in range(21)],
                "session_id": "hagrid_import",
                "source": "hagrid",
                "source_user_id": subj,
                "coordinate_format": "hagrid_normalized_2d",
                "landmark_dimension": 2,
            }
            (hagrid_dir / f"{subj}_{i}.json").write_text(json.dumps(s), encoding="utf-8")

    combiner = DatasetCombinerService(base_dataset_dir=temp_dataset_dir)
    res = combiner.combine_datasets(
        DatasetCombineRequest(
            name="LeakageFreeSplit",
            include_custom=False,
            include_hagrid=True,
            compatibility_mode="2d_only",
            train_ratio=0.5,
            val_ratio=0.5,
            test_ratio=0.0,
        )
    )

    # Read combined JSON and verify subject-level isolation
    out_dir = temp_dataset_dir / "combined" / res.combined_id
    with open(out_dir / "combined_dataset.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    splits_for_alpha = {s["split"] for s in data["samples"] if s["subject_id"] == "subj_alpha"}
    splits_for_beta = {s["split"] for s in data["samples"] if s["subject_id"] == "subj_beta"}

    # Each subject must strictly belong to exactly ONE split!
    assert len(splits_for_alpha) == 1
    assert len(splits_for_beta) == 1
