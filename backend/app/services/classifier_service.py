"""
Real-Time Gesture Classifier Inference Service for GestureFlow AI.

Integrates with the MediaPipe Hand Tracking pipeline:
- Loads active model ONCE in memory (zero per-frame reload overhead)
- Extracts 63-dim normalized features
- Runs fast (<0.1ms) vectorized MLP forward pass
- Computes confidence scores & threshold filtering
- Handles uncertain gestures and no-hand states
- Measures exact inference latency
"""

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from app.schemas.classifier import ClassifierStatusResponse, ModelMetadata, PredictionResponse
from app.services.feature_engineering import FeatureEngineeringError, FeaturePreprocessor
from app.services.mlp_classifier import MLPClassifierModel
from app.services.model_registry import ModelRegistryService

logger = logging.getLogger(__name__)


class ClassifierService:
    """Manages active classifier model in memory and performs real-time inference."""

    def __init__(self, registry_service: Optional[ModelRegistryService] = None):
        self._registry_service = registry_service or ModelRegistryService()
        self._preprocessor = FeaturePreprocessor(mode="3d", scale_normalized=True, wrist_relative=True)
        self._active_model: Optional[MLPClassifierModel] = None
        self._active_metadata_id: Optional[str] = None
        self._active_metadata_name: Optional[str] = None
        self._active_classes: List[Dict[str, str]] = []
        self._confidence_threshold: float = 0.60
        self._inference_count: int = 0
        self._total_inference_time_ms: float = 0.0
        self._lock = threading.RLock()

        # Load active model from registry if available
        self.load_active_model()

    @property
    def is_model_loaded(self) -> bool:
        with self._lock:
            return self._active_model is not None

    @property
    def active_metadata(self) -> Optional[ModelMetadata]:
        with self._lock:
            if not self._active_metadata_id:
                return None
            return self._registry_service.get_model(self._active_metadata_id)

    @property
    def confidence_threshold(self) -> float:
        with self._lock:
            return self._confidence_threshold

    def set_confidence_threshold(self, threshold: float) -> None:
        with self._lock:
            self._confidence_threshold = max(0.1, min(0.99, float(threshold)))

    def load_active_model(self, force: bool = False) -> bool:
        """
        Load active model from registry into memory once.
        Skips reload if already active and not forced.
        """
        with self._lock:
            meta = self._registry_service.get_active_model()
            if not meta:
                self._active_model = None
                self._active_metadata_id = None
                self._active_metadata_name = None
                self._active_classes = []
                return False

            if not force and self._active_metadata_id == meta.model_id and self._active_model is not None:
                # Already loaded in memory
                return True

            weights_path = Path(meta.model_file)
            if not weights_path.exists():
                logger.error("Model weights file missing: %s", weights_path)
                return False

            try:
                model = MLPClassifierModel.load(weights_path)
                self._active_model = model
                self._active_metadata_id = meta.model_id
                self._active_metadata_name = meta.model_name
                self._active_classes = meta.classes
                logger.info(
                    "Loaded active static gesture classifier into memory: %s (%s)",
                    meta.model_name,
                    meta.model_id,
                )
                return True
            except Exception as e:
                logger.error("Failed to load model weights: %s", e, exc_info=True)
                return False

    def predict_landmarks(
        self,
        landmarks: Optional[List[Any]],
        handedness: str = "Right",
        custom_threshold: Optional[float] = None,
    ) -> PredictionResponse:
        """
        Classify a single set of 21 hand landmarks in real time.
        """
        threshold = custom_threshold if custom_threshold is not None else self._confidence_threshold

        with self._lock:
            if not self._active_model:
                # Attempt lazy reload
                self.load_active_model()

            if not self._active_model:
                return PredictionResponse(
                    gesture_id=None,
                    gesture_name="No Model Active",
                    confidence=0.0,
                    is_recognized=False,
                    threshold=threshold,
                )

            if not landmarks or len(landmarks) != 21:
                return PredictionResponse(
                    gesture_id=None,
                    gesture_name="No Hand",
                    confidence=0.0,
                    is_recognized=False,
                    threshold=threshold,
                )

            t_start = time.perf_counter()
            try:
                # Extract 63-dim normalized feature vector
                feat = self._preprocessor.transform(landmarks)
                # Compute forward pass probabilities
                probs = self._active_model.predict_proba(feat)[0]
                t_end = time.perf_counter()
                latency_ms = round((t_end - t_start) * 1000.0, 3)

                best_idx = int(np.argmax(probs))
                best_prob = round(float(probs[best_idx]), 4)

                all_probs: Dict[str, float] = {}
                name_lookup = {c["id"]: c["name"] for c in self._active_classes}

                for gid, c_idx in self._active_model.class_mapping.items():
                    c_name = name_lookup.get(gid, gid)
                    all_probs[c_name] = round(float(probs[c_idx]), 4)

                pred_gid = self._active_model.reverse_class_mapping.get(best_idx)
                pred_name = name_lookup.get(pred_gid, pred_gid or "Unknown")

                # Update stats
                self._inference_count += 1
                self._total_inference_time_ms += latency_ms

                # Confidence threshold check
                is_recognized = best_prob >= threshold

                return PredictionResponse(
                    gesture_id=pred_gid if is_recognized else None,
                    gesture_name=pred_name if is_recognized else f"Uncertain ({pred_name})",
                    confidence=best_prob,
                    is_recognized=is_recognized,
                    all_probabilities=all_probs,
                    inference_latency_ms=latency_ms,
                    model_id=self._active_metadata_id,
                    threshold=threshold,
                )

            except FeatureEngineeringError as fe:
                return PredictionResponse(
                    gesture_id=None,
                    gesture_name=f"Invalid Landmarks ({fe})",
                    confidence=0.0,
                    is_recognized=False,
                    threshold=threshold,
                )
            except Exception as e:
                logger.debug("Inference error: %s", e)
                return PredictionResponse(
                    gesture_id=None,
                    gesture_name=f"Inference Error: {e}",
                    confidence=0.0,
                    is_recognized=False,
                    threshold=threshold,
                )

    def get_status(self) -> ClassifierStatusResponse:
        """Get live classifier status and latency telemetry."""
        with self._lock:
            avg_lat = 0.0
            if self._inference_count > 0:
                avg_lat = round(self._total_inference_time_ms / self._inference_count, 3)

            return ClassifierStatusResponse(
                is_model_loaded=self._active_model is not None,
                active_model_id=self._active_metadata_id,
                active_model_name=self._active_metadata_name,
                classes=self._active_classes,
                confidence_threshold=self._confidence_threshold,
                inference_count=self._inference_count,
                avg_inference_latency_ms=avg_lat,
            )


# Global singleton instance
_classifier_service: Optional[ClassifierService] = None
_service_lock = threading.Lock()


def get_classifier_service() -> ClassifierService:
    global _classifier_service
    with _service_lock:
        if _classifier_service is None:
            _classifier_service = ClassifierService()
        return _classifier_service
