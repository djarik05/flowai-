"""
Public dataset schemas for HaGRIDv2 integration in GestureFlow AI.

Defines models for HaGRID dataset catalog, class mappings, download manager,
annotation parsing, and dataset combiner.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HagridClassInfo(BaseModel):
    """Information about an individual HaGRID gesture class."""

    name: str = Field(..., description="Class name in HaGRID, e.g. 'palm', 'like', 'fist'")
    size_gb: float = Field(..., description="Approximate archive size in GB")
    sample_count_approx: int = Field(default=32000, description="Approximate number of samples")
    description: str = Field(default="", description="Description of gesture pose")
    is_two_handed: bool = Field(default=False, description="Whether this is a two-handed gesture")
    download_url: str = Field(..., description="Official download URL from SberCloud")
    suggested_gesture_id: Optional[str] = Field(default=None, description="Suggested GestureFlow ID")
    suggested_gesture_name: Optional[str] = Field(default=None, description="Suggested GestureFlow name")


class HagridDatasetInfo(BaseModel):
    """Metadata and attribution for the HaGRIDv2 public dataset."""

    name: str = "HaGRIDv2"
    full_name: str = "HAnd Gesture Recognition Image Dataset v2"
    version: str = "v2"
    total_classes: int = 34
    total_samples: int = 1086158
    total_size_tb: float = 1.5
    license: str = "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
    license_url: str = "https://creativecommons.org/licenses/by-sa/4.0/"
    repository_url: str = "https://github.com/hukenovs/hagrid"
    paper_title: str = "HaGRIDv2: 1M Images for Static and Dynamic Hand Gesture Recognition"
    paper_url: str = "https://arxiv.org/abs/2412.01508"
    authors: List[str] = [
        "Alexander Kapitanov",
        "Andrey Makhlyarchuk",
        "Karina Kvanchiani",
        "Aleksandr Nagaev",
        "Roman Kraynov",
        "Anton Nuzhdin",
    ]
    citation: str = (
        "@misc{nuzhdin2024hagridv21mimagesstatic,\n"
        "  title={HaGRIDv2: 1M Images for Static and Dynamic Hand Gesture Recognition},\n"
        "  author={Anton Nuzhdin and Alexander Nagaev and Alexander Sautin and Alexander Kapitanov and Karina Kvanchiani},\n"
        "  year={2024},\n"
        "  eprint={2412.01508},\n"
        "  archivePrefix={arXiv},\n"
        "  primaryClass={cs.CV}\n"
        "}"
    )
    annotations_download_url: str = (
        "https://rndml-team-cv.obs.ru-moscow-1.hc.sbercloud.ru/datasets/hagrid_v2/annotations_with_landmarks/annotations.zip"
    )
    classes: List[HagridClassInfo] = []
    downloaded_classes: List[str] = []
    annotations_downloaded: bool = False
    imported_sample_counts: Dict[str, int] = {}


class HagridClassMapping(BaseModel):
    """Mapping between a HaGRID class and a GestureFlow gesture."""

    hagrid_class: str
    target_gesture_id: Optional[str] = None
    target_gesture_name: Optional[str] = None
    action: str = Field(default="map", description="'map', 'skip', or 'create_new'")
    confidence_threshold: float = Field(default=0.8, ge=0.5, le=0.99)


class HagridClassMappingsResponse(BaseModel):
    """Full mapping configuration for all HaGRID classes."""

    mappings: Dict[str, HagridClassMapping]
    available_gestures: List[Dict[str, Any]]


class HagridDownloadRequest(BaseModel):
    """Selective download request for HaGRID data."""

    download_annotations: bool = Field(default=True, description="Download annotations.zip")
    target_classes: List[str] = Field(default_factory=list, description="List of gesture classes to download")
    force_redownload: bool = Field(default=False, description="Re-download even if archive exists")


class HagridImportRequest(BaseModel):
    """Import request to parse annotations and ingest into GestureFlow schema."""

    source_type: str = Field(default="downloaded", description="'downloaded' or 'local_path'")
    local_annotation_path: Optional[str] = Field(default=None, description="Path to local annotation JSON or folder")
    local_images_dir: Optional[str] = Field(default=None, description="Path to local images directory")
    splits: List[str] = Field(default_factory=lambda: ["train", "val", "test"], description="Splits to import")
    selected_classes: Optional[List[str]] = Field(default=None, description="Subset of classes to import")
    max_samples_per_class: Optional[int] = Field(default=None, ge=1, le=100000, description="Optional cap per class")


class PublicJobStatusResponse(BaseModel):
    """Telemetry for background download or import jobs."""

    job_id: str
    job_type: str = Field(..., description="'download' or 'import'")
    status: str = Field(default="pending", description="'pending', 'running', 'completed', 'cancelled', 'error'")
    progress_percent: float = 0.0
    message: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class DatasetCombineRequest(BaseModel):
    """Request to combine custom and public datasets with compatibility checks."""

    name: str = Field(..., min_length=1, description="Name of the combined dataset version")
    include_custom: bool = Field(default=True, description="Include custom webcam samples")
    include_hagrid: bool = Field(default=True, description="Include imported HaGRID samples")
    selected_gestures: Optional[List[str]] = Field(default=None, description="Gesture IDs to include (None = all)")
    compatibility_mode: str = Field(
        default="2d_projection",
        description="'2d_projection' (drops z on 3D to match 2D), '2d_only' (only 2D samples), or '3d_only' (only 3D samples)",
    )
    train_ratio: float = Field(default=0.70, ge=0.1, le=1.0, description="Training split proportion")
    val_ratio: float = Field(default=0.15, ge=0.0, le=0.5, description="Validation split proportion")
    test_ratio: float = Field(default=0.15, ge=0.0, le=0.5, description="Test split proportion")
    preserve_subject_splits: bool = Field(default=True, description="Prevent data leakage by grouping by subject ID")


class DatasetCombineResponse(BaseModel):
    """Result of dataset combination."""

    combined_id: str
    name: str
    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    unique_subjects: int
    coordinate_format: str
    landmark_dimension: int
    classes_included: List[str]
    sample_counts_by_class: Dict[str, int]
    export_csv_filename: str
    export_json_filename: str
    created_at: str


class DatasetSourcesResponse(BaseModel):
    """Overview of available dataset sources and sample counts."""

    total_samples: int
    custom_samples_count: int
    hagrid_samples_count: int
    coordinate_formats: Dict[str, int]
    gesture_breakdown: Dict[str, Dict[str, int]]
