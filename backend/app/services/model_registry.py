"""
Model Registry Service for GestureFlow AI.

Manages trained static gesture classifier artifacts:
- Versioned storage with immutable checkpoints
- Registry metadata index (registry.json)
- Activation / deactivation state for real-time inference
- Model comparison and lifecycle management
"""

import json
import logging
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas.classifier import EvaluationMetrics, ModelMetadata

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """Manages versioned static gesture classification models."""

    def __init__(self, registry_dir: Optional[Path] = None):
        backend_dir = Path(__file__).resolve().parent.parent.parent
        self.registry_dir = registry_dir or (backend_dir / "models" / "classifiers")
        self.registry_file = self.registry_dir / "registry.json"
        self._lock = threading.RLock()
        self._ensure_registry()

    def _ensure_registry(self) -> None:
        """Create directory and initialize registry index if needed."""
        with self._lock:
            self.registry_dir.mkdir(parents=True, exist_ok=True)
            if not self.registry_file.exists():
                with open(self.registry_file, "w", encoding="utf-8") as f:
                    json.dump({"active_model_id": None, "models": []}, f, indent=2)

    def _load_registry_data(self) -> Dict[str, Any]:
        """Read registry index from disk."""
        with self._lock:
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load registry index: %s", e)
                return {"active_model_id": None, "models": []}

    def _save_registry_data(self, data: Dict[str, Any]) -> None:
        """Atomically persist registry index to disk."""
        with self._lock:
            tmp = self.registry_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.registry_file)

    def list_models(self) -> List[ModelMetadata]:
        """Return all registered models sorted by creation date."""
        with self._lock:
            data = self._load_registry_data()
            active_id = data.get("active_model_id")
            models: List[ModelMetadata] = []

            for item in data.get("models", []):
                try:
                    m = ModelMetadata(**item)
                    m.is_active = (m.model_id == active_id)
                    models.append(m)
                except Exception as e:
                    logger.warning("Skipping invalid model entry: %s", e)

            # Sort latest first
            models.sort(key=lambda m: m.created_at, reverse=True)
            return models

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Retrieve metadata for a specific model."""
        with self._lock:
            data = self._load_registry_data()
            active_id = data.get("active_model_id")

            for item in data.get("models", []):
                if item.get("model_id") == model_id:
                    m = ModelMetadata(**item)
                    m.is_active = (m.model_id == active_id)
                    return m
            return None

    def get_active_model(self) -> Optional[ModelMetadata]:
        """Get the currently activated model for live inference."""
        with self._lock:
            data = self._load_registry_data()
            active_id = data.get("active_model_id")
            if not active_id:
                return None
            return self.get_model(active_id)

    def register_model(
        self,
        metadata: ModelMetadata,
        activate: bool = True,
    ) -> ModelMetadata:
        """Register a freshly trained model artifact."""
        with self._lock:
            data = self._load_registry_data()
            # If model_id already exists, prevent accidental overwrite
            existing = [m for m in data.get("models", []) if m.get("model_id") == metadata.model_id]
            if existing:
                raise ValueError(f"Model ID '{metadata.model_id}' is already registered.")

            if activate or data.get("active_model_id") is None:
                data["active_model_id"] = metadata.model_id
                metadata.is_active = True
            else:
                metadata.is_active = False

            data["models"].append(metadata.model_dump())
            self._save_registry_data(data)
            logger.info("Registered model %s (active=%s)", metadata.model_id, metadata.is_active)
            return metadata

    def activate_model(self, model_id: str) -> bool:
        """Activate a registered model for real-time inference."""
        with self._lock:
            data = self._load_registry_data()
            found = any(m.get("model_id") == model_id for m in data.get("models", []))
            if not found:
                logger.warning("Cannot activate unknown model: %s", model_id)
                return False

            data["active_model_id"] = model_id
            self._save_registry_data(data)
            logger.info("Activated model: %s", model_id)
            return True

    def deactivate_model(self, model_id: Optional[str] = None) -> bool:
        """Deactivate currently active model."""
        with self._lock:
            data = self._load_registry_data()
            curr = data.get("active_model_id")
            if model_id is not None and curr != model_id:
                return False

            data["active_model_id"] = None
            self._save_registry_data(data)
            logger.info("Deactivated active model: %s", curr)
            return True

    def delete_model(self, model_id: str) -> bool:
        """Delete a model artifact and remove from registry."""
        with self._lock:
            data = self._load_registry_data()
            models = data.get("models", [])
            target = next((m for m in models if m.get("model_id") == model_id), None)
            if not target:
                return False

            # If deleting the active model, deactivate it
            if data.get("active_model_id") == model_id:
                data["active_model_id"] = None

            # Remove directory
            model_dir = self.registry_dir / model_id
            if model_dir.exists() and model_dir.is_dir():
                try:
                    shutil.rmtree(model_dir)
                except Exception as e:
                    logger.warning("Could not delete directory %s: %s", model_dir, e)

            data["models"] = [m for m in models if m.get("model_id") != model_id]
            self._save_registry_data(data)
            logger.info("Deleted model: %s", model_id)
            return True

    def compare_models(self, id_a: str, id_b: str) -> Dict[str, Any]:
        """Compare evaluation metrics and configurations of two models."""
        model_a = self.get_model(id_a)
        model_b = self.get_model(id_b)

        if not model_a or not model_b:
            raise ValueError("One or both model IDs were not found in registry.")

        return {
            "model_a": model_a.model_dump(),
            "model_b": model_b.model_dump(),
            "comparison": {
                "accuracy_diff": round(model_a.metrics.accuracy - model_b.metrics.accuracy, 4),
                "f1_diff": round(model_a.metrics.f1_macro - model_b.metrics.f1_macro, 4),
                "classes_a_count": len(model_a.classes),
                "classes_b_count": len(model_b.classes),
            },
        }
