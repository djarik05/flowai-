"""
Dataset schemas for GestureFlow AI backend.

Defines Pydantic models for sample storage, dataset collection, statistics,
validation, and export.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class LandmarkCoord(BaseModel):
    """Normalized landmark coordinate (3D for MediaPipe custom, 2D for HaGRID)."""

    index: int = Field(..., ge=0, le=20, description="Landmark index (0 to 20)")
    x: float = Field(..., description="Normalized X coordinate [0.0, 1.0]")
    y: float = Field(..., description="Normalized Y coordinate [0.0, 1.0]")
    z: Optional[float] = Field(default=None, description="Normalized relative depth coordinate (optional for 2D datasets)")

    @field_validator("x", "y")
    @classmethod
    def validate_coord_finite(cls, v: float) -> float:
        """Ensure coordinate is a valid finite float."""
        if not math.isfinite(v):
            raise ValueError("Landmark coordinate must be a finite number")
        return v

    @field_validator("z")
    @classmethod
    def validate_depth_finite(cls, v: Optional[float]) -> Optional[float]:
        """Ensure depth coordinate is a valid finite float if provided."""
        if v is not None and not math.isfinite(v):
            raise ValueError("Landmark depth z must be a finite number")
        return v


class DatasetSample(BaseModel):
    """Structured dataset sample storing complete 21-point hand landmark data."""

    sample_id: str = Field(..., description="Unique sample identifier")
    gesture_id: str = Field(..., description="Registered gesture ID")
    gesture_name: str = Field(..., description="Registered gesture display name")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Capture timestamp")
    handedness: str = Field(default="Right", description="'Left', 'Right', or 'Unknown'")
    handedness_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="MediaPipe handedness confidence")
    landmarks: List[LandmarkCoord] = Field(..., min_length=21, max_length=21, description="Exactly 21 MediaPipe landmarks")
    session_id: str = Field(..., description="Collection session ID or import session ID")
    features: Optional[Dict[str, Any]] = Field(default=None, description="Optional derived relative or normalized features")

    # Public Dataset Provenance Fields (backward-compatible)
    source: str = Field(default="custom", description="Dataset source: 'custom' (webcam) or 'hagrid'")
    source_dataset_version: Optional[str] = Field(default=None, description="Source dataset version, e.g. 'HaGRIDv2'")
    source_image_id: Optional[str] = Field(default=None, description="Source image UUID/filename")
    source_split: Optional[str] = Field(default=None, description="'train', 'val', or 'test'")
    source_user_id: Optional[str] = Field(default=None, description="Subject ID to preserve subject-level splits")
    coordinate_format: str = Field(
        default="mediapipe_normalized_3d",
        description="'mediapipe_normalized_3d' or 'hagrid_normalized_2d'"
    )
    landmark_dimension: int = Field(default=3, description="Landmark dimensionality: 2 or 3")
    annotations: Optional[Dict[str, Any]] = Field(default=None, description="Source annotations (bboxes, united_bbox, meta)")
    imported_at: Optional[str] = Field(default=None, description="ISO-8601 import timestamp")

    @field_validator("landmarks")
    @classmethod
    def validate_landmarks_integrity(cls, v: List[LandmarkCoord]) -> List[LandmarkCoord]:
        """Validate that all 21 landmarks are present with unique indices."""
        if len(v) != 21:
            raise ValueError(f"DatasetSample requires exactly 21 landmarks, got {len(v)}")
        indices = [lm.index for lm in v]
        if len(set(indices)) != 21:
            raise ValueError("Duplicate landmark indices found in sample")
        return v


class DatasetSampleSummary(BaseModel):
    """Compact summary of a dataset sample for explorer lists."""

    sample_id: str
    gesture_id: str
    gesture_name: str
    timestamp: str
    handedness: str
    handedness_confidence: float
    session_id: str
    landmark_count: int = 21
    source: str = "custom"
    coordinate_format: str = "mediapipe_normalized_3d"
    landmark_dimension: int = 3


class SampleListResponse(BaseModel):
    """Paginated list of dataset samples."""

    samples: List[DatasetSampleSummary]
    total: int
    limit: int
    offset: int
    gesture_id: Optional[str] = None


class CollectionStartRequest(BaseModel):
    """Request to initiate a live dataset collection session."""

    gesture_id: str = Field(..., description="Gesture ID to collect samples for")
    target_samples: int = Field(default=50, ge=5, le=1000, description="Number of samples to capture")
    sample_interval_ms: int = Field(default=150, ge=30, le=2000, description="Interval between captured frames in ms")
    camera_index: Optional[int] = Field(default=None, ge=0, description="Optional specific camera index")


class CollectionStatusResponse(BaseModel):
    """Real-time status of dataset collection pipeline."""

    session_id: Optional[str] = None
    gesture_id: Optional[str] = None
    gesture_name: Optional[str] = None
    status: str = Field(default="idle", description="'idle', 'starting', 'collecting', 'paused', 'stopping', 'completed', 'cancelled', 'error'")
    state: str = Field(default="idle", description="Alias for status (for frontend compatibility)")
    target_samples: int = 0
    collected_samples: int = 0
    progress_percent: float = 0.0
    progress_pct: float = 0.0  # Alias for progress_percent
    hand_detected: bool = False
    handedness: str = "Unknown"
    fps: float = 0.0
    last_error: Optional[str] = None

    @model_validator(mode="after")
    def sync_state_and_progress(self) -> "CollectionStatusResponse":
        """Synchronize state/status and progress_pct/progress_percent."""
        if self.status and not self.state:
            self.state = self.status
        elif self.state and not self.status:
            self.status = self.state
        else:
            self.state = self.status

        if self.progress_percent and not self.progress_pct:
            self.progress_pct = self.progress_percent
        elif self.progress_pct and not self.progress_percent:
            self.progress_percent = self.progress_pct
        else:
            self.progress_pct = self.progress_percent
        return self


class DatasetStatsResponse(BaseModel):
    """Aggregated dataset statistics for the dashboard."""

    total_gestures: int
    total_samples: int
    samples_per_gesture: Dict[str, int]
    gesture_counts: Dict[str, int] = Field(default_factory=dict, description="Alias for samples_per_gesture")
    insufficient_sample_gestures: List[str]
    insufficient_gestures: List[str] = Field(default_factory=list, description="Alias for insufficient_sample_gestures")
    completion_percentage: float
    target_samples_per_gesture: int = 50
    latest_session_id: Optional[str] = None
    latest_session_time: Optional[str] = None

    @model_validator(mode="after")
    def sync_aliases(self) -> "DatasetStatsResponse":
        """Ensure both backend and frontend field names are populated."""
        if self.samples_per_gesture and not self.gesture_counts:
            self.gesture_counts = self.samples_per_gesture.copy()
        elif self.gesture_counts and not self.samples_per_gesture:
            self.samples_per_gesture = self.gesture_counts.copy()

        if self.insufficient_sample_gestures and not self.insufficient_gestures:
            self.insufficient_gestures = self.insufficient_sample_gestures.copy()
        elif self.insufficient_gestures and not self.insufficient_sample_gestures:
            self.insufficient_sample_gestures = self.insufficient_gestures.copy()
        return self


class ValidationIssue(BaseModel):
    """Individual issue found during dataset integrity check."""

    sample_id: str
    gesture_id: str
    issue_type: str
    message: str
    severity: str = "warning"


class DatasetValidationReport(BaseModel):
    """Comprehensive dataset validation audit report."""

    is_valid: bool
    total_checked: int
    valid_samples: int
    corrupted_samples: int
    missing_landmarks_count: int
    invalid_coordinates_count: int
    missing_gesture_ref_count: int
    duplicate_sample_ids: List[str]
    issues: List[ValidationIssue]
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
