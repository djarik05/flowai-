"""
Pydantic schemas for Phase 4 Static Gesture Classifier.

Covers:
- Dataset readiness report & class audits
- Training configuration & hyperparameters
- Epoch metrics & training job status
- Evaluation metrics & confusion matrix
- Model registry metadata
- Real-time prediction request & response
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetReadinessClassReport(BaseModel):
    """Readiness audit report for a single gesture class."""
    gesture_id: str
    gesture_name: str
    sample_count: int = 0
    valid_sample_count: int = 0
    invalid_sample_count: int = 0
    missing_landmarks_count: int = 0
    coordinate_schema: str = "3D"  # "3D" or "2D"
    handedness_distribution: Dict[str, int] = Field(default_factory=dict)
    dataset_compatibility: str = "compatible_3d"  # "compatible_3d", "2d_only", "incompatible"
    is_ready: bool = False
    warnings: List[str] = Field(default_factory=list)


class DatasetReadinessReport(BaseModel):
    """Global dataset readiness audit report before model training."""
    total_gestures: int = 0
    total_samples: int = 0
    valid_samples: int = 0
    invalid_samples: int = 0
    ready_classes_count: int = 0
    min_samples_per_class: int = 5
    classes: List[DatasetReadinessClassReport] = Field(default_factory=list)
    class_imbalance_ratio: float = 1.0
    is_training_ready: bool = False
    summary: str = ""
    warnings: List[str] = Field(default_factory=list)


class TrainingConfigRequest(BaseModel):
    """User-specified training hyperparameters and architecture."""
    model_config = {"protected_namespaces": ()}

    gesture_ids: Optional[List[str]] = Field(
        default=None,
        description="List of gesture IDs to train on. None = use all eligible classes.",
    )
    model_name: str = Field(default="GestureFlow MLP Static Classifier", max_length=100)
    hidden_layers: List[int] = Field(default=[128, 64], description="Dense layer unit counts")
    dropout_rates: List[float] = Field(default=[0.25, 0.20], description="Dropout probability per hidden layer")
    epochs: int = Field(default=50, ge=5, le=300)
    batch_size: int = Field(default=32, ge=4, le=256)
    learning_rate: float = Field(default=0.001, ge=1e-5, le=0.1)
    train_split: float = Field(default=0.70, ge=0.5, le=0.9)
    val_split: float = Field(default=0.15, ge=0.05, le=0.3)
    test_split: float = Field(default=0.15, ge=0.05, le=0.3)
    confidence_threshold: float = Field(default=0.60, ge=0.1, le=0.99)
    session_aware_split: bool = Field(
        default=True,
        description="Prevent data leakage by grouping samples from the same collection session",
    )


class TrainingMetricItem(BaseModel):
    """Performance metrics for a single training epoch."""
    epoch: int
    train_loss: float
    val_loss: float
    train_accuracy: float
    val_accuracy: float


class ClassEvaluationMetric(BaseModel):
    """Per-class test evaluation metrics."""
    precision: float
    recall: float
    f1_score: float
    support: int


class EvaluationMetrics(BaseModel):
    """Comprehensive test dataset evaluation metrics."""
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    confusion_matrix: List[List[int]]
    class_labels: List[str]
    per_class: Dict[str, ClassEvaluationMetric]
    test_samples_count: int


class ModelMetadata(BaseModel):
    """Versioned model registry entry."""
    model_config = {"protected_namespaces": ()}

    model_id: str
    model_name: str
    version: str
    created_at: str
    dataset_version: str
    classes: List[Dict[str, str]]  # [{"id": "G001", "name": "Open Palm"}]
    feature_schema: str = "landmarks_3d_wrist_relative_scale_normalized"
    feature_dim: int = 63
    preprocessing_config: Dict[str, Any]
    training_config: Dict[str, Any]
    metrics: EvaluationMetrics
    model_file: str
    is_active: bool = False


class TrainingJobStatus(BaseModel):
    """Live status of a background model training job."""
    job_id: str
    status: str = "pending"  # "pending", "training", "completed", "failed", "cancelled"
    current_epoch: int = 0
    total_epochs: int = 50
    progress_percent: float = 0.0
    latest_train_loss: Optional[float] = None
    latest_val_loss: Optional[float] = None
    latest_train_accuracy: Optional[float] = None
    latest_val_accuracy: Optional[float] = None
    metrics_history: List[TrainingMetricItem] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    created_model_id: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class LandmarkPointInput(BaseModel):
    """Coordinate for a single landmark point."""
    index: int
    x: float
    y: float
    z: Optional[float] = 0.0


class PredictionRequest(BaseModel):
    """Inference request with 21 landmarks."""
    landmarks: List[LandmarkPointInput]
    handedness: Optional[str] = "Right"
    confidence_threshold: Optional[float] = None


class PredictionResponse(BaseModel):
    """Real-time gesture recognition prediction result."""
    model_config = {"protected_namespaces": ()}

    gesture_id: Optional[str] = None
    gesture_name: str = "Unknown"
    confidence: float = 0.0
    is_recognized: bool = False
    all_probabilities: Dict[str, float] = Field(default_factory=dict)
    inference_latency_ms: float = 0.0
    model_id: Optional[str] = None
    threshold: float = 0.60


class ClassifierStatusResponse(BaseModel):
    """Status of the live classifier inference engine."""
    is_model_loaded: bool = False
    active_model_id: Optional[str] = None
    active_model_name: Optional[str] = None
    classes: List[Dict[str, str]] = Field(default_factory=list)
    confidence_threshold: float = 0.60
    inference_count: int = 0
    avg_inference_latency_ms: float = 0.0
