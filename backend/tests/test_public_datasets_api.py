"""
API integration tests for HaGRID public dataset endpoints and dataset combiner.
"""

import json
import time
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def local_annotation_fixture(tmp_path):
    """Creates a small local HaGRID annotation fixture file."""
    fixture_file = tmp_path / "test_hagrid_train.json"

    def make_21(x=0.5, y=0.5):
        return [[x + (i * 0.005), y + (i * 0.005)] for i in range(21)]

    data = {
        "fixture_uuid_001": {
            "bboxes": [[0.2, 0.2, 0.3, 0.3]],
            "labels": ["palm"],
            "hand_landmarks": [make_21(0.25, 0.25)],
            "united_bbox": None,
            "united_label": None,
            "user_id": "test_user_alpha",
            "meta": {"age": [25.0], "gender": ["female"], "race": ["White"]},
        },
        "fixture_uuid_002": {
            "bboxes": [[0.4, 0.4, 0.2, 0.2]],
            "labels": ["like"],
            "hand_landmarks": [make_21(0.45, 0.45)],
            "united_bbox": None,
            "united_label": None,
            "user_id": "test_user_beta",
            "meta": {"age": [32.0], "gender": ["male"], "race": ["Asian"]},
        },
    }
    fixture_file.write_text(json.dumps(data), encoding="utf-8")
    return fixture_file


def test_list_public_datasets(client):
    """Test GET /api/v1/public-datasets."""
    res = client.get("/api/v1/public-datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 1
    hagrid = next(d for d in datasets if d["id"] == "hagrid")
    assert hagrid["name"] == "HaGRIDv2"
    assert hagrid["classes_count"] == 34
    assert hagrid["license"] == "CC BY-SA 4.0"


def test_get_hagrid_info_and_classes(client):
    """Test GET /api/v1/public-datasets/hagrid and /classes."""
    res_info = client.get("/api/v1/public-datasets/hagrid")
    assert res_info.status_code == 200
    info = res_info.json()
    assert info["name"] == "HaGRIDv2"
    assert len(info["classes"]) == 34
    assert "https://github.com/hukenovs/hagrid" in info["repository_url"]

    res_classes = client.get("/api/v1/public-datasets/hagrid/classes")
    assert res_classes.status_code == 200
    classes = res_classes.json()
    assert len(classes) == 34
    names = {c["name"] for c in classes}
    assert "palm" in names
    assert "fist" in names
    assert "no_gesture" in names


def test_hagrid_mappings_get_and_put(client):
    """Test GET and PUT /api/v1/public-datasets/hagrid/mappings."""
    res_get = client.get("/api/v1/public-datasets/hagrid/mappings")
    assert res_get.status_code == 200
    data = res_get.json()
    assert "mappings" in data
    assert "palm" in data["mappings"]

    # Update mapping
    updated_mappings = data["mappings"]
    updated_mappings["palm"]["action"] = "map"
    updated_mappings["palm"]["target_gesture_id"] = "G001"

    res_put = client.put("/api/v1/public-datasets/hagrid/mappings", json=updated_mappings)
    assert res_put.status_code == 200
    assert res_put.json()["status"] == "success"


def test_import_local_annotation_fixture(client, local_annotation_fixture):
    """Integration test importing a small local annotation fixture."""
    req = {
        "source_type": "local_path",
        "local_annotation_path": str(local_annotation_fixture),
        "splits": ["train"],
        "selected_classes": ["palm", "like"],
        "max_samples_per_class": 10,
    }

    res_start = client.post("/api/v1/public-datasets/hagrid/import", json=req)
    assert res_start.status_code == 200
    job = res_start.json()
    job_id = job["job_id"]
    assert job["job_type"] == "import"

    # Wait briefly for background import thread to complete
    for _ in range(20):
        time.sleep(0.1)
        res_status = client.get(f"/api/v1/public-datasets/import/{job_id}")
        assert res_status.status_code == 200
        curr = res_status.json()
        if curr["status"] in ("completed", "error"):
            break

    final_status = client.get(f"/api/v1/public-datasets/import/{job_id}").json()
    assert final_status["status"] == "completed"
    assert final_status["details"]["samples_imported"] >= 2


def test_dataset_sources_and_combine_api(client, local_annotation_fixture):
    """Test GET /api/v1/dataset/sources and POST /api/v1/dataset/combine."""
    # First query sources
    res_sources = client.get("/api/v1/dataset/sources")
    assert res_sources.status_code == 200
    sources_data = res_sources.json()
    assert "custom_samples_count" in sources_data
    assert "hagrid_samples_count" in sources_data

    # Test combine
    req = {
        "name": "IntegrationCombinedTest",
        "include_custom": True,
        "include_hagrid": True,
        "compatibility_mode": "2d_projection",
        "train_ratio": 0.7,
        "val_ratio": 0.15,
        "test_ratio": 0.15,
        "preserve_subject_splits": True,
    }
    res_combine = client.post("/api/v1/dataset/combine", json=req)
    assert res_combine.status_code in (200, 400)
    if res_combine.status_code == 200:
        cdata = res_combine.json()
        assert "combined_id" in cdata
        assert cdata["landmark_dimension"] == 2
