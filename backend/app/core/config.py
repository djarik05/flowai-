"""
Configuration management for GestureFlow AI backend.

Uses Pydantic Settings for environment-based configuration with validation.
"""

from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Application
    app_name: str = Field(default="GestureFlow AI", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment: development or production")

    # API
    api_host: str = Field(default="127.0.0.1", description="API host address")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API version prefix")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: str = Field(default="logs", description="Log directory path")

    # CORS - stored as comma-separated string in env, parsed to list
    cors_allowed_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="CORS allowed origins (comma-separated)",
        alias="CORS_ALLOWED_ORIGINS",
    )
    frontend_dev_url: str = Field(default="http://localhost:5173", description="Frontend development URL")

    # Camera settings
    camera_index: int = Field(default=0, ge=0, description="Camera device index")
    camera_width: int = Field(default=640, ge=160, le=3840, description="Camera frame width")
    camera_height: int = Field(default=480, ge=120, le=2160, description="Camera frame height")
    camera_fps: int = Field(default=30, ge=1, le=120, description="Camera frame rate")
    camera_mirror: bool = Field(default=True, description="Mirror camera frames horizontally")
    camera_backend: str = Field(default="", description="OpenCV backend (e.g., 'CAP_DSHOW', 'CAP_V4L2')")
    camera_init_timeout: float = Field(default=5.0, ge=0.5, le=30.0, description="Camera initialization timeout (seconds)")

    # Hand tracking settings
    tracking_max_hands: int = Field(default=2, ge=1, le=4, description="Maximum number of hands to track")
    tracking_detection_confidence: float = Field(default=0.7, ge=0.1, le=1.0, description="Minimum detection confidence")
    tracking_tracking_confidence: float = Field(default=0.6, ge=0.1, le=1.0, description="Minimum tracking confidence")
    tracking_model_complexity: int = Field(default=1, ge=0, le=2, description="MediaPipe model complexity (0=lite, 1=full, 2=heavy)")

    # Hand landmarker model path (relative to backend directory or absolute)
    hand_landmarker_model_path: str = Field(
        default="models/hand_landmarker.task",
        description="Path to MediaPipe Hand Landmarker model asset (.task file)",
        alias="HAND_LANDMARKER_MODEL_PATH",
    )

    # Mouse control settings (Phase 6A)
    mouse_control_enabled: bool = Field(default=False, description="Enable mouse control (OFF by default for safety)")
    mouse_sensitivity: float = Field(default=1.0, ge=0.1, le=5.0, description="Cursor sensitivity multiplier")
    mouse_smoothing_alpha: float = Field(default=0.35, ge=0.01, le=0.99, description="Cursor smoothing alpha")
    mouse_active_margin_x: float = Field(default=0.15, ge=0.0, le=0.40, description="Horizontal tracking margin")
    mouse_active_margin_y: float = Field(default=0.15, ge=0.0, le=0.40, description="Vertical tracking margin")
    mouse_tracking_timeout_ms: float = Field(default=150.0, ge=50.0, le=1000.0, description="Tracking loss timeout in ms")

    # Dataset settings
    dataset_dir: str = Field(
        default="datasets",
        description="Directory for gesture datasets and samples",
        alias="DATASET_DIR",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "production", "staging"}
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("camera_backend")
    @classmethod
    def validate_camera_backend(cls, v: str) -> str:
        """Validate camera backend."""
        if v and v.upper() not in {"CAP_DSHOW", "CAP_V4L2", "CAP_MSMF", "CAP_ANY"}:
            raise ValueError(f"camera_backend must be one of: CAP_DSHOW, CAP_V4L2, CAP_MSMF, CAP_ANY or empty")
        return v.upper()

    @property
    def cors_allowed_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_allowed_origins_raw.split(",") if origin.strip()]

    @property
    def log_dir_path(self) -> Path:
        """Get log directory as Path object."""
        return Path(self.log_dir)

    @property
    def api_url(self) -> str:
        """Get full API base URL."""
        return f"http://{self.api_host}:{self.api_port}{self.api_prefix}"

    @property
    def camera_backend_flag(self) -> int:
        """Get OpenCV camera backend flag."""
        if not self.camera_backend:
            return 0  # CAP_ANY
        import cv2
        backend_map = {
            "CAP_DSHOW": cv2.CAP_DSHOW,
            "CAP_V4L2": cv2.CAP_V4L2,
            "CAP_MSMF": cv2.CAP_MSMF,
            "CAP_ANY": 0,
        }
        return backend_map.get(self.camera_backend, 0)

    @property
    def backend_dir(self) -> Path:
        """Get the backend project root directory (where this config module lives: backend/)."""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def resolved_dataset_dir(self) -> Path:
        """Resolve datasets directory."""
        d = Path(self.dataset_dir)
        if d.is_absolute():
            return d.resolve()
        return (self.backend_dir / d).resolve()

    @property
    def resolved_model_path(self) -> Path:
        """Resolve the hand landmarker model path to an absolute path.

        If the configured path is relative, it is resolved relative to the
        backend project directory so the result is stable regardless of the
        current working directory. Also handles paths specified relative to
        the repository root (e.g. 'backend/models/...').
        """
        model = Path(self.hand_landmarker_model_path)
        if model.is_absolute():
            return model.resolve()

        # Check relative to backend directory first (e.g., 'models/hand_landmarker.task')
        backend_rel = self.backend_dir / model
        if backend_rel.exists():
            return backend_rel.resolve()

        # Check relative to repository root (e.g., 'backend/models/hand_landmarker.task')
        repo_rel = self.backend_dir.parent / model
        if repo_rel.exists():
            return repo_rel.resolve()

        # Check relative to cwd
        cwd_rel = Path.cwd() / model
        if cwd_rel.exists():
            return cwd_rel.resolve()

        return backend_rel.resolve()


# Global settings instance
settings = Settings()