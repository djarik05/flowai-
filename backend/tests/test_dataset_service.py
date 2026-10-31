"""
Tests for DatasetService logic: storage, stats, validation, export.
"""

import json
from pathlib import Path
import pytest

from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.dataset_service import DatasetService


def make_dummy_sample(sample_id: str, gesture_id: str = "G001", session_id: str = "sess_1") -> DatasetSample:
    """Helper to generate a valid 21-landmark sample."""
    landmarks = [
        LandmarkCoord(
            index=i,
            x=round(0.1 + (i * 0.03), 3),
            y=round(0.2 + (i * 0.02), 3),
            z=round(-0.05 + (i * 0.005), 3),
        )
        for i in range(21)
    ]
    return DatasetSample(
        sample_id=sample_id,
        gesture_id=gesture_id,
        gesture_name=f"Gesture {gesture_id}",
        handedness="Right",
        handedness_confidence=0.98,
        landmarks=landmarks,
        session_id=session_id,
    )


@pytest.fixture
def dataset_service(tmp_path) -> DatasetService:
    """Create DatasetService with temporary directory."""
    return DatasetService(dataset_dir=tmp_path / "test_dataset")


def test_save_and_get_sample(dataset_service: DatasetService) -> None:
    """Test saving a sample and reading it back."""
    sample = make_dummy_sample("s_001", "G001")
    saved = dataset_service.save_sample(sample)
    assert saved.sample_id == "s_001"

    # Read back
    retrieved = dataset_service.get_sample("s_001")
    assert retrieved is not None
    assert retrieved.sample_id == "s_001"
    assert retrieved.gesture_id == "G001"
    assert len(retrieved.landmarks) == 21
    assert retrieved.landmarks[0].x == sample.landmarks[0].x

    # Overwrite protection
    with pytest.raises(ValueError, match="already exists"):
        dataset_service.save_sample(sample)


def test_query_and_pagination(dataset_service: DatasetService) -> None:
    """Test querying and paginating samples."""
    for i in range(5):
        dataset_service.save_sample(make_dummy_sample(f"s_g1_{i}", "G001", "sess_A"))
    for i in range(3):
        dataset_service.save_sample(make_dummy_sample(f"s_g2_{i}", "G002", "sess_B"))

    # All samples
    samples, total = dataset_service.get_samples(limit=10)
    assert total == 8
    assert len(samples) == 8

    # Filter by gesture
    g1_samples, g1_total = dataset_service.get_samples(gesture_id="G001")
    assert g1_total == 5
    assert len(g1_samples) == 5

    # Filter by session
    sess_b, sess_b_total = dataset_service.get_samples(session_id="sess_B")
    assert sess_b_total == 3

    # Pagination
    page, _ = dataset_service.get_samples(limit=3, offset=0)
    assert len(page) == 3


def test_delete_sample_and_session(dataset_service: DatasetService) -> None:
    """Test sample and session deletion."""
    dataset_service.save_sample(make_dummy_sample("s_del_1", "G001", "sess_del"))
    dataset_service.save_sample(make_dummy_sample("s_del_2", "G001", "sess_del"))

    # Delete single sample
    assert dataset_service.delete_sample("s_del_1") is True
    assert dataset_service.get_sample("s_del_1") is None
    assert dataset_service.delete_sample("s_del_1") is False

    # Delete session
    deleted = dataset_service.delete_session("sess_del")
    assert deleted == 1
    assert dataset_service.get_sample("s_del_2") is None


def test_dataset_stats(dataset_service: DatasetService) -> None:
    """Test statistics aggregation."""
    for i in range(10):
        dataset_service.save_sample(make_dummy_sample(f"s_stat_{i}", "G001"))

    reg_gestures = [{"id": "G001"}, {"id": "G002"}]
    stats = dataset_service.get_stats(registered_gestures=reg_gestures)

    assert stats.total_gestures == 2
    assert stats.total_samples == 10
    assert stats.samples_per_gesture["G001"] == 10
    assert "G001" in stats.insufficient_sample_gestures  # < 50
    assert "G002" in stats.insufficient_sample_gestures


def test_dataset_validation(dataset_service: DatasetService) -> None:
    """Test dataset integrity audit report."""
    # 1. Valid sample
    dataset_service.save_sample(make_dummy_sample("s_val_1", "G001"))

    report = dataset_service.validate_dataset(registered_ids={"G001"})
    assert report.is_valid is True
    assert report.total_checked == 1
    assert report.valid_samples == 1
    assert report.corrupted_samples == 0

    # 2. Corrupted file
    corrupt_file = dataset_service._samples_dir / "G001" / "corrupt.json"
    with open(corrupt_file, "w") as f:
        f.write("{ INVALID JSON")

    report2 = dataset_service.validate_dataset(registered_ids={"G001"})
    assert report2.is_valid is False
    assert report2.corrupted_samples == 1


def test_csv_and_json_export(dataset_service: DatasetService) -> None:
    """Test CSV and JSON export generation."""
    for i in range(3):
        dataset_service.save_sample(make_dummy_sample(f"s_exp_{i}", "G001"))

    # CSV Export
    csv_path = dataset_service.export_csv(gesture_id="G001")
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 4  # Header + 3 rows
    assert "x_0" in lines[0]
    assert "z_20" in lines[0]

    # JSON Export
    json_path = dataset_service.export_json()
    assert json_path.exists()
    assert json_path.suffix == ".json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_samples"] == 3
    assert len(data["samples"]) == 3
