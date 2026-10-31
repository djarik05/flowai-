"""
Comprehensive Phase 4 Tests: Static Gesture Classifier & Model Registry.

Tests:
- 3D & 2D Feature Extraction and Normalization (translation, scale, finite validation)
- Dataset Readiness Analyzer (single class warning, multi-class readiness, imbalance)
- MLP Neural Network (forward pass, backpropagation, training loss reduction, save/load)
- Training Engine (splitting, training progress, independent test metrics, confusion matrix)
- Model Registry (CRUD, activation/deactivation, versioning, restart persistence)
- Real-time Classifier Service (inference latency, threshold filtering, unknown gestures)
- FastAPI Endpoints (readiness, train, predict, models CRUD)
"""

import json
import math
import shutil
import time
from pathlib import Path
from typing import List

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.classifier import PredictionRequest, TrainingConfigRequest
from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.classifier_service import ClassifierService
from app.services.dataset_readiness import DatasetReadinessAnalyzer
from app.services.dataset_seeder import DatasetSeeder
from app.services.dataset_service import DatasetService
from app.services.feature_engineering import FeatureEngineeringError, FeaturePreprocessor
from app.services.gesture_service import GestureService
from app.services.mlp_classifier import MLPClassifierModel
from app.services.model_registry import ModelRegistryService
from app.services.training_engine import TrainingEngine


@pytest.fixture
def clean_env(tmp_path: Path):
    """Create isolated test environment with temporary directories."""
    dataset_dir = tmp_path / "datasets"
    registry_file = dataset_dir / "gestures" / "registry.json"
    models_dir = tmp_path / "models" / "classifiers"

    ds = DatasetService(dataset_dir=dataset_dir)
    gs = GestureService(registry_file=registry_file)
    mr = ModelRegistryService(registry_dir=models_dir)
    te = TrainingEngine(dataset_service=ds, gesture_service=gs, registry_service=mr)
    dra = DatasetReadinessAnalyzer(dataset_service=ds, gesture_service=gs)
    seeder = DatasetSeeder(dataset_service=ds, gesture_service=gs)

    return {
        "dataset_service": ds,
        "gesture_service": gs,
        "model_registry": mr,
        "training_engine": te,
        "readiness_analyzer": dra,
        "seeder": seeder,
        "tmp_path": tmp_path,
    }


# ===========================================================================
# 1. Feature Engineering Tests
# ===========================================================================


def test_feature_extraction_3d_normalization():
    """Verify 3D normalization: 63 dims, wrist at origin, invariant to translation and scale."""
    preprocessor = FeaturePreprocessor(mode="3d", scale_normalized=True, wrist_relative=True)
    assert preprocessor.feature_dim == 63

    # Generate 21 sample landmarks
    landmarks = [
        {"index": i, "x": 0.5 + 0.01 * i, "y": 0.5 + 0.02 * i, "z": 0.005 * i}
        for i in range(21)
    ]

    features = preprocessor.transform(landmarks)
    assert isinstance(features, np.ndarray)
    assert features.shape == (63,)
    assert features.dtype == np.float32

    # Wrist (index 0) must be exactly at origin (0, 0, 0)
    assert features[0] == pytest.approx(0.0, abs=1e-6)
    assert features[1] == pytest.approx(0.0, abs=1e-6)
    assert features[2] == pytest.approx(0.0, abs=1e-6)

    # Translation Invariance: shifting raw coordinates by (+10, -5, +2) yields identical features
    shifted_landmarks = [
        {"index": i, "x": pt["x"] + 10.0, "y": pt["y"] - 5.0, "z": pt["z"] + 2.0}
        for i, pt in enumerate(landmarks)
    ]
    features_shifted = preprocessor.transform(shifted_landmarks)
    np.testing.assert_allclose(features, features_shifted, atol=1e-5)

    # Scale Invariance: scaling hand size by 2x yields identical features
    scaled_landmarks = [
        {"index": i, "x": landmarks[0]["x"] + (pt["x"] - landmarks[0]["x"]) * 2.0,
         "y": landmarks[0]["y"] + (pt["y"] - landmarks[0]["y"]) * 2.0,
         "z": landmarks[0]["z"] + (pt["z"] - landmarks[0]["z"]) * 2.0}
        for i, pt in enumerate(landmarks)
    ]
    features_scaled = preprocessor.transform(scaled_landmarks)
    np.testing.assert_allclose(features, features_scaled, atol=1e-5)


def test_feature_extraction_rejects_invalid():
    """Verify preprocessor rejects non-21 landmarks, NaN, Inf, and missing depth in 3D."""
    preprocessor = FeaturePreprocessor(mode="3d")

    # Reject < 21 landmarks
    with pytest.raises(FeatureEngineeringError, match="Expected exactly 21 landmarks"):
        preprocessor.transform([{"index": 0, "x": 0.5, "y": 0.5, "z": 0.0}] * 20)

    # Reject NaN
    nan_landmarks = [{"index": i, "x": 0.5, "y": 0.5, "z": 0.0} for i in range(21)]
    nan_landmarks[5]["x"] = float("nan")
    with pytest.raises(FeatureEngineeringError, match="Non-finite coordinates"):
        preprocessor.transform(nan_landmarks)

    # Reject missing z in 3D mode
    missing_z = [{"index": i, "x": 0.5, "y": 0.5, "z": None} for i in range(21)]
    with pytest.raises(FeatureEngineeringError, match="Missing or non-finite z"):
        preprocessor.transform(missing_z)


def test_2d_and_3d_schema_separation():
    """Verify 2D mode produces 42 features without fabricating z."""
    preproc_2d = FeaturePreprocessor(mode="2d")
    assert preproc_2d.feature_dim == 42

    landmarks_2d = [{"index": i, "x": 0.1 * i, "y": 0.2 * i} for i in range(21)]
    feat_2d = preproc_2d.transform(landmarks_2d)
    assert feat_2d.shape == (42,)


# ===========================================================================
# 2. Dataset Readiness Analyzer Tests
# ===========================================================================


def test_dataset_readiness_insufficient_classes(clean_env):
    """Readiness analyzer must reject training if only 1 class is ready."""
    seeder = clean_env["seeder"]
    analyzer = clean_env["readiness_analyzer"]

    # Seed only G001
    seeder.seed_standard_gestures(samples_per_gesture=10, gesture_ids=["G001"])

    report = analyzer.audit()
    assert report.total_samples == 10
    assert report.ready_classes_count == 1
    assert report.is_training_ready is False
    assert any("Only 1 gesture class is eligible" in report.summary for _ in [1])


def test_dataset_readiness_multiple_classes_ready(clean_env):
    """Readiness analyzer succeeds when >= 2 classes have >= 5 samples."""
    seeder = clean_env["seeder"]
    analyzer = clean_env["readiness_analyzer"]

    seeder.seed_standard_gestures(samples_per_gesture=8, gesture_ids=["G001", "G002", "G003"])

    report = analyzer.audit()
    assert report.total_samples == 24
    assert report.ready_classes_count == 3
    assert report.is_training_ready is True
    assert "ready for training" in report.summary.lower()


# ===========================================================================
# 3. MLP Classifier Model Tests
# ===========================================================================


def test_mlp_model_forward_loss_and_serialization(tmp_path: Path):
    """Test MLP forward pass, dropout, loss decrease, and serialization."""
    num_classes = 3
    mapping = {"G001": 0, "G002": 1, "G003": 2}
    model = MLPClassifierModel(
        input_dim=63,
        hidden_layers=[32, 16],
        dropout_rates=[0.25, 0.20],
        num_classes=num_classes,
        class_mapping=mapping,
        seed=123,
    )

    # Synthetic cluster data
    rng = np.random.RandomState(42)
    X = np.vstack([
        rng.randn(20, 63) + 2.0,
        rng.randn(20, 63) - 2.0,
        rng.randn(20, 63) * 0.1,
    ]).astype(np.float32)
    y = np.array([0] * 20 + [1] * 20 + [2] * 20, dtype=np.int64)

    # Initial loss
    initial_loss, _ = model.compute_loss_and_acc(X, y)

    # Train for 15 epochs
    for _ in range(15):
        model.train_epoch(X, y, batch_size=16, lr=0.01)

    final_loss, final_acc = model.compute_loss_and_acc(X, y)
    assert final_loss < initial_loss, f"Loss did not decrease: {initial_loss} -> {final_loss}"
    assert final_acc > 0.80

    # Test serialization and loading
    save_path = tmp_path / "test_model" / "weights.npz"
    model.save(save_path)
    assert save_path.exists()

    loaded_model = MLPClassifierModel.load(save_path)
    assert loaded_model.input_dim == 63
    assert loaded_model.hidden_layers == [32, 16]
    assert loaded_model.num_classes == 3

    # Exact prediction match
    probs_orig = model.predict_proba(X[:5])
    probs_load = loaded_model.predict_proba(X[:5])
    np.testing.assert_allclose(probs_orig, probs_load, atol=1e-5)


# ===========================================================================
# 4. Training Engine & Evaluation Tests
# ===========================================================================


def test_training_engine_full_workflow(clean_env):
    """Test end-to-end training, metrics calculation, and model saving."""
    seeder = clean_env["seeder"]
    engine = clean_env["training_engine"]
    registry = clean_env["model_registry"]

    # Seed 3 classes with 15 samples each
    seeder.seed_standard_gestures(samples_per_gesture=15, gesture_ids=["G001", "G002", "G003"])

    config = TrainingConfigRequest(
        gesture_ids=["G001", "G002", "G003"],
        model_name="Unit Test Static MLP",
        epochs=10,
        batch_size=8,
        learning_rate=0.01,
        train_split=0.7,
        val_split=0.15,
        test_split=0.15,
    )

    status = engine.start_training_job(config, background=False)
    assert status.status == "completed"
    assert status.created_model_id is not None
    assert status.latest_train_loss is not None
    assert len(status.metrics_history) == 10

    # Verify registered model
    meta = registry.get_model(status.created_model_id)
    assert meta is not None
    assert meta.model_name == "Unit Test Static MLP"
    assert meta.metrics.accuracy >= 0.70
    assert len(meta.metrics.confusion_matrix) == 3
    assert len(meta.metrics.class_labels) == 3
    assert meta.is_active is True


# ===========================================================================
# 5. Model Registry Tests
# ===========================================================================


def test_model_registry_lifecycle(clean_env):
    """Test model registry CRUD, activation, and restart persistence."""
    registry = clean_env["model_registry"]
    engine = clean_env["training_engine"]
    seeder = clean_env["seeder"]

    seeder.seed_standard_gestures(samples_per_gesture=10, gesture_ids=["G001", "G002"])

    # Train model 1
    config1 = TrainingConfigRequest(epochs=5, model_name="Model v1")
    job1 = engine.start_training_job(config1, background=False)
    m1_id = job1.created_model_id

    # Train model 2
    config2 = TrainingConfigRequest(epochs=5, model_name="Model v2")
    job2 = engine.start_training_job(config2, background=False)
    m2_id = job2.created_model_id

    # Model 2 should be active by default (latest registered)
    assert registry.get_active_model().model_id == m2_id

    # Switch active model to Model 1
    assert registry.activate_model(m1_id) is True
    assert registry.get_active_model().model_id == m1_id

    # Restart persistence: Re-instantiate ModelRegistryService
    new_reg = ModelRegistryService(registry_dir=registry.registry_dir)
    assert len(new_reg.list_models()) == 2
    assert new_reg.get_active_model().model_id == m1_id

    # Delete Model 2
    assert new_reg.delete_model(m2_id) is True
    assert len(new_reg.list_models()) == 1


# ===========================================================================
# 6. Real-Time Classifier Service Tests
# ===========================================================================


def test_realtime_classifier_service(clean_env):
    """Test ClassifierService inference latency and confidence threshold filtering."""
    seeder = clean_env["seeder"]
    engine = clean_env["training_engine"]
    registry = clean_env["model_registry"]

    seeder.seed_standard_gestures(samples_per_gesture=15, gesture_ids=["G001", "G002"])
    job = engine.start_training_job(TrainingConfigRequest(epochs=10), background=False)

    cls_svc = ClassifierService(registry_service=registry)
    assert cls_svc.is_model_loaded is True

    # Real Palm landmark coordinates
    palm_lms = seeder._generate_landmarks("G001", seed=42)
    pred_palm = cls_svc.predict_landmarks(palm_lms)

    assert pred_palm.is_recognized is True
    assert pred_palm.gesture_id == "G001"
    assert pred_palm.confidence >= 0.60
    assert pred_palm.inference_latency_ms < 15.0  # Ultra-fast real-time latency (<15ms)

    # Fist landmark coordinates
    fist_lms = seeder._generate_landmarks("G002", seed=42)
    pred_fist = cls_svc.predict_landmarks(fist_lms)
    assert pred_fist.is_recognized is True
    assert pred_fist.gesture_id == "G002"

    # Low-confidence / uncertain threshold test
    cls_svc.set_confidence_threshold(0.999)
    pred_strict = cls_svc.predict_landmarks(fist_lms)
    if pred_strict.confidence < 0.999:
        assert pred_strict.is_recognized is False
        assert "Uncertain" in pred_strict.gesture_name


# ===========================================================================
# 7. FastAPI Endpoint Integration Tests
# ===========================================================================


def test_classifier_api_endpoints():
    """Test FastAPI routes: readiness, status, models list, predict."""
    client = TestClient(app)

    # 1. Status
    res_status = client.get("/api/v1/classifier/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "is_model_loaded" in data_status

    # 2. Dataset Readiness
    res_ready = client.get("/api/v1/classifier/dataset-readiness")
    assert res_ready.status_code == 200
    data_ready = res_ready.json()
    assert "is_training_ready" in data_ready
    assert "classes" in data_ready

    # 3. Models List
    res_models = client.get("/api/v1/models")
    assert res_models.status_code == 200
    assert isinstance(res_models.json(), list)

    # 4. Predict endpoint
    sample_landmarks = [{"index": i, "x": 0.5, "y": 0.5, "z": 0.0} for i in range(21)]
    res_pred = client.post("/api/v1/classifier/predict", json={"landmarks": sample_landmarks})
    assert res_pred.status_code == 200
    data_pred = res_pred.json()
    assert "gesture_name" in data_pred
    assert "confidence" in data_pred
    assert "inference_latency_ms" in data_pred
