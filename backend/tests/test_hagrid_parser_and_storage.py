"""
Unit and integration tests for HaGRID annotation parser, coordinate conversion, and storage.
"""

import json
import math
from pathlib import Path
import pytest
from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.gesture_service import GestureService
from app.services.hagrid_parser import HagridAnnotationParser


@pytest.fixture
def sample_hagrid_annotation_dict():
    """Generates official-schema synthetic HaGRIDv2 annotation dictionary."""
    def make_21_points(base_x=0.4, base_y=0.4):
        return [[base_x + (i * 0.01), base_y + (i * 0.01)] for i in range(21)]

    return {
        # Single hand: like
        "img_like_001": {
            "bboxes": [[0.3, 0.4, 0.2, 0.25]],
            "labels": ["like"],
            "hand_landmarks": [make_21_points(0.35, 0.45)],
            "united_bbox": None,
            "united_label": None,
            "user_id": "user_alpha_123",
            "meta": {"age": [25.0], "gender": ["female"], "race": ["Asian"]},
        },
        # Primary hand with secondary no_gesture hand
        "img_palm_and_rest_002": {
            "bboxes": [
                [0.2, 0.3, 0.15, 0.2],
                [0.7, 0.6, 0.12, 0.15],
            ],
            "labels": ["palm", "no_gesture"],
            "hand_landmarks": [
                make_21_points(0.22, 0.32),
                make_21_points(0.72, 0.62),
            ],
            "united_bbox": None,
            "united_label": None,
            "user_id": "user_beta_456",
            "meta": {"age": [30.0], "gender": ["male"], "race": ["White"]},
        },
        # Two-handed gesture: thumb_index2
        "img_two_handed_003": {
            "bboxes": [
                [0.1, 0.3, 0.25, 0.25],
                [0.6, 0.3, 0.25, 0.25],
            ],
            "labels": ["thumb_index2", "thumb_index2"],
            "hand_landmarks": [
                make_21_points(0.15, 0.35),
                make_21_points(0.65, 0.35),
            ],
            "united_bbox": [[0.1, 0.3, 0.75, 0.25]],
            "united_label": ["thumb_index2"],
            "user_id": "user_gamma_789",
            "meta": {"age": [22.0], "gender": ["female"], "race": ["Black"]},
        },
    }


def test_parser_single_and_multi_hand(sample_hagrid_annotation_dict):
    """Test parsing one-handed, secondary-hand, and two-handed gestures."""
    parser = HagridAnnotationParser()
    res = parser.parse_dict(sample_hagrid_annotation_dict, split="train")

    assert res.total_images_processed == 3
    # img1 has 1 (like), img2 has 1 (palm, no_gesture is skipped by default), img3 has 2 (thumb_index2)
    assert res.valid_samples_count >= 3

    # Check 2D coordinate preservation (no fabricated z)
    for sample in res.samples:
        assert sample.source == "hagrid"
        assert sample.coordinate_format == "hagrid_normalized_2d"
        assert sample.landmark_dimension == 2
        assert len(sample.landmarks) == 21
        for lm in sample.landmarks:
            assert lm.z is None
            assert 0.0 <= lm.x <= 1.0
            assert 0.0 <= lm.y <= 1.0


def test_parser_no_fabricated_z(sample_hagrid_annotation_dict):
    """Verify that z-depth is strictly None for HaGRID annotations."""
    parser = HagridAnnotationParser()
    res = parser.parse_dict(sample_hagrid_annotation_dict, split="val")

    like_sample = next(s for s in res.samples if s.source_image_id == "img_like_001")
    assert like_sample.gesture_name == "Thumbs Up"
    assert like_sample.gesture_id == "G003"
    assert like_sample.source_user_id == "user_alpha_123"
    assert like_sample.source_split == "val"
    assert all(lm.z is None for lm in like_sample.landmarks)


def test_parser_two_handed_metadata(sample_hagrid_annotation_dict):
    """Verify two-handed gestures preserve united_bbox and united_label."""
    parser = HagridAnnotationParser()
    res = parser.parse_dict(sample_hagrid_annotation_dict, split="test")

    two_handed_samples = [s for s in res.samples if s.source_image_id == "img_two_handed_003"]
    assert len(two_handed_samples) == 2
    for s in two_handed_samples:
        assert s.annotations is not None
        assert s.annotations.get("is_two_handed") is True
        assert s.annotations.get("united_bbox") is not None
        assert s.annotations.get("united_label") == ["thumb_index2"]


def test_parser_handles_invalid_and_corrupt_records():
    """Verify non-finite coordinates and invalid counts are flagged without crashing."""
    corrupt_data = {
        "nan_coords": {
            "bboxes": [[0.1, 0.1, 0.2, 0.2]],
            "labels": ["palm"],
            "hand_landmarks": [[[float("nan"), 0.5]] * 21],
            "user_id": "u1",
        },
        "wrong_count": {
            "bboxes": [[0.1, 0.1, 0.2, 0.2]],
            "labels": ["fist"],
            "hand_landmarks": [[[0.5, 0.5]] * 15],  # 15 instead of 21
            "user_id": "u2",
        },
        "missing_landmarks": {
            "bboxes": [[0.1, 0.1, 0.2, 0.2]],
            "labels": ["peace"],
            "hand_landmarks": [],
            "user_id": "u3",
        },
    }

    parser = HagridAnnotationParser()
    res = parser.parse_dict(corrupt_data, split="train")

    assert res.valid_samples_count == 0
    assert len(res.issues) >= 3

    issue_types = {issue.issue_type for issue in res.issues}
    assert "non_finite_coordinates" in issue_types
    assert "invalid_landmark_count" in issue_types
    assert "missing_landmarks" in issue_types


def test_parser_custom_class_mapping(sample_hagrid_annotation_dict):
    """Verify class mapping with custom target IDs and skipping."""
    custom_mappings = {
        "like": {"target_id": "CUSTOM_LIKE", "target_name": "Thumbs", "action": "map"},
        "palm": {"target_id": None, "target_name": None, "action": "skip"},
        "thumb_index2": {"target_id": "G008", "target_name": "L-Frame", "action": "map"},
    }

    parser = HagridAnnotationParser(class_mappings=custom_mappings)
    res = parser.parse_dict(sample_hagrid_annotation_dict, split="train")

    gesture_ids = {s.gesture_id for s in res.samples}
    assert "CUSTOM_LIKE" in gesture_ids
    assert "G008" in gesture_ids
    # palm was skipped
    assert "G001" not in gesture_ids
    assert "HG_PALM" not in gesture_ids
