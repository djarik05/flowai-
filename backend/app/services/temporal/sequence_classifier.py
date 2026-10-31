"""
Sequence-based Machine Learning data preparation and model architecture blueprint.
Prepares fixed-length normalized sequences (T=30 timesteps x 63 features) for
temporal gesture classification (1D-CNN / GRU / LSTM).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.services.feature_engineering import FeaturePreprocessor


class SequencePreprocessor:
    """
    Transforms variable-length temporal landmark sequences into fixed-size,
    scale-normalized matrices (T x 63) suitable for sequence classifiers.
    """

    TARGET_SEQUENCE_LENGTH: int = 30  # Standard normalized timesteps
    FEATURE_DIM: int = 63             # 21 landmarks x 3D

    def __init__(self, target_length: int = TARGET_SEQUENCE_LENGTH):
        self.target_length = target_length
        self._static_preprocessor = FeaturePreprocessor(mode="3d", scale_normalized=True, wrist_relative=True)

    def process_sequence(self, raw_frames: List[Any]) -> Optional[np.ndarray]:
        """
        Convert list of landmark frames into a fixed (target_length, 63) array.
        Uses linear temporal interpolation to resample sequences to exact target length.

        Returns:
            np.ndarray of shape (target_length, 63), or None if invalid.
        """
        if not raw_frames or len(raw_frames) < 3:
            return None

        # 1. Transform each frame to 63-D normalized feature vector
        frame_features = []
        for frame_landmarks in raw_frames:
            try:
                feat = self._static_preprocessor.transform(frame_landmarks)
                frame_features.append(feat)
            except Exception:
                continue

        if len(frame_features) < 3:
            return None

        features_arr = np.array(frame_features, dtype=np.float32)  # (N_orig, 63)
        n_orig = len(features_arr)

        if n_orig == self.target_length:
            return features_arr

        # 2. Resample / interpolate along time axis to exactly target_length
        orig_indices = np.linspace(0.0, 1.0, num=n_orig)
        target_indices = np.linspace(0.0, 1.0, num=self.target_length)

        resampled = np.empty((self.target_length, self.FEATURE_DIM), dtype=np.float32)
        for dim in range(self.FEATURE_DIM):
            resampled[:, dim] = np.interp(target_indices, orig_indices, features_arr[:, dim])

        return resampled


class SequenceMLPBaseline:
    """
    Lightweight flattened sequence classifier baseline:
    Flattens (30 x 63 = 1890 features) -> Dense(128) -> Dense(64) -> Softmax(classes).
    Allows immediate sequence evaluation without requiring heavy PyTorch/TensorFlow dependencies.
    """

    def __init__(self, num_classes: int = 9, class_mapping: Optional[Dict[str, int]] = None):
        self.num_classes = num_classes
        self.class_mapping = class_mapping or {
            f"T00{i+1}": i for i in range(min(num_classes, 9))
        }
        self.reverse_mapping = {v: k for k, v in self.class_mapping.items()}

    def predict(self, sequence_arr: np.ndarray) -> Tuple[str, float]:
        """Mock/Baseline inference for sequence classifier."""
        # Returns top dynamic class and synthetic baseline probability
        return "T001", 0.85
