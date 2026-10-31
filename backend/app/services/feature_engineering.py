"""
Feature Engineering Pipeline for GestureFlow AI Static Gesture Classifier.

Transforms 21 MediaPipe hand landmarks into translation- and scale-invariant
feature vectors for training and real-time inference.

Guarantees:
- 3D mode: 21 landmarks * 3 = 63 features
- Wrist-relative translation normalization (wrist at index 0 becomes (0,0,0))
- Palm-scale normalization (invariant to hand distance from camera)
- Finite number validation (rejects NaN, Inf, non-numeric values)
- Explicit separation between 2D (42 features) and 3D (63 features) schemas
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class FeatureEngineeringError(ValueError):
    """Raised when landmark data is invalid, corrupt, or incompatible."""
    pass


class FeaturePreprocessor:
    """
    Reusable landmark feature preprocessor for training and real-time inference.
    """

    FEATURE_DIM_3D = 63
    FEATURE_DIM_2D = 42

    def __init__(
        self,
        mode: str = "3d",
        scale_normalized: bool = True,
        wrist_relative: bool = True,
    ):
        """
        Initialize feature preprocessor.

        Args:
            mode: "3d" (63 features) or "2d" (42 features).
            scale_normalized: Divide relative coordinates by reference palm distance.
            wrist_relative: Center coordinates relative to wrist landmark (index 0).
        """
        if mode not in ("3d", "2d"):
            raise ValueError(f"Invalid mode '{mode}'. Must be '3d' or '2d'.")
        self.mode = mode
        self.scale_normalized = scale_normalized
        self.wrist_relative = wrist_relative

    @property
    def feature_dim(self) -> int:
        return self.FEATURE_DIM_3D if self.mode == "3d" else self.FEATURE_DIM_2D

    def get_config(self) -> Dict[str, Any]:
        """Return preprocessor configuration for model serialization."""
        return {
            "mode": self.mode,
            "feature_dim": self.feature_dim,
            "scale_normalized": self.scale_normalized,
            "wrist_relative": self.wrist_relative,
            "reference_bone": "wrist_to_middle_mcp (0 to 9)",
        }

    @staticmethod
    def _extract_coord(pt: Any) -> Tuple[float, float, Optional[float]]:
        """Extract x, y, and optional z from dict, LandmarkCoord, list/tuple, or object."""
        if isinstance(pt, (list, tuple)):
            x = float(pt[0]) if len(pt) > 0 else float("nan")
            y = float(pt[1]) if len(pt) > 1 else float("nan")
            z = float(pt[2]) if len(pt) > 2 and pt[2] is not None else None
            return x, y, z

        if isinstance(pt, dict):
            x = float(pt.get("x", float("nan")))
            y = float(pt.get("y", float("nan")))
            z = pt.get("z")
            z = float(z) if z is not None else None
            return x, y, z

        x = float(getattr(pt, "x", float("nan")))
        y = float(getattr(pt, "y", float("nan")))
        z = getattr(pt, "z", None)
        z = float(z) if z is not None else None
        return x, y, z

    def transform(self, landmarks: List[Any]) -> np.ndarray:
        """
        Transform 21 hand landmarks into a normalized 1D feature vector.

        Args:
            landmarks: List of 21 landmark objects or dicts with x, y, (and z for 3D).

        Returns:
            1D np.ndarray of shape (63,) for 3D, or (42,) for 2D.

        Raises:
            FeatureEngineeringError: If landmark count != 21, NaN/Inf detected,
                                    or missing z in 3D mode.
        """
        if not landmarks or len(landmarks) != 21:
            raise FeatureEngineeringError(
                f"Expected exactly 21 landmarks, received {len(landmarks) if landmarks else 0}"
            )

        coords_3d: List[Tuple[float, float, float]] = []
        coords_2d: List[Tuple[float, float]] = []

        for idx, pt in enumerate(landmarks):
            x, y, z = self._extract_coord(pt)

            if not (math.isfinite(x) and math.isfinite(y)):
                raise FeatureEngineeringError(
                    f"Non-finite coordinates detected at landmark {idx}: x={x}, y={y}"
                )

            if self.mode == "3d":
                if z is None or not math.isfinite(z):
                    raise FeatureEngineeringError(
                        f"Missing or non-finite z coordinate at landmark {idx} for 3D schema: z={z}"
                    )
                coords_3d.append((x, y, z))
            else:
                coords_2d.append((x, y))

        if self.mode == "3d":
            return self._normalize_3d(coords_3d)
        else:
            return self._normalize_2d(coords_2d)

    def _normalize_3d(self, coords: List[Tuple[float, float, float]]) -> np.ndarray:
        """Apply wrist-relative translation and scale normalization in 3D."""
        w_x, w_y, w_z = coords[0] if self.wrist_relative else (0.0, 0.0, 0.0)

        # 1. Translation: translate all points relative to wrist
        rel = [(x - w_x, y - w_y, z - w_z) for (x, y, z) in coords]

        # 2. Scale: reference distance between wrist (0) and Middle MCP (9)
        scale = 1.0
        if self.scale_normalized:
            m_x, m_y, m_z = rel[9]
            dist = math.sqrt(m_x * m_x + m_y * m_y + m_z * m_z)
            if dist > 1e-4:
                scale = dist
            else:
                # Fallback: maximum Euclidean distance to wrist
                max_d = max(math.sqrt(x * x + y * y + z * z) for (x, y, z) in rel)
                scale = max_d if max_d > 1e-4 else 1.0

        # 3. Flatten into 63-element feature vector
        features = np.zeros(self.FEATURE_DIM_3D, dtype=np.float32)
        for i, (x, y, z) in enumerate(rel):
            features[i * 3] = x / scale
            features[i * 3 + 1] = y / scale
            features[i * 3 + 2] = z / scale

        return features

    def _normalize_2d(self, coords: List[Tuple[float, float]]) -> np.ndarray:
        """Apply wrist-relative translation and scale normalization in 2D."""
        w_x, w_y = coords[0] if self.wrist_relative else (0.0, 0.0)

        rel = [(x - w_x, y - w_y) for (x, y) in coords]

        scale = 1.0
        if self.scale_normalized:
            m_x, m_y = rel[9]
            dist = math.sqrt(m_x * m_x + m_y * m_y)
            if dist > 1e-4:
                scale = dist
            else:
                max_d = max(math.sqrt(x * x + y * y) for (x, y) in rel)
                scale = max_d if max_d > 1e-4 else 1.0

        features = np.zeros(self.FEATURE_DIM_2D, dtype=np.float32)
        for i, (x, y) in enumerate(rel):
            features[i * 2] = x / scale
            features[i * 2 + 1] = y / scale

        return features

    def transform_batch(
        self, samples_landmarks: List[List[Any]]
    ) -> Tuple[np.ndarray, List[int]]:
        """
        Process a batch of sample landmark sets.
        Returns (feature_matrix, valid_indices).
        """
        valid_features = []
        valid_indices = []

        for idx, lms in enumerate(samples_landmarks):
            try:
                feat = self.transform(lms)
                valid_features.append(feat)
                valid_indices.append(idx)
            except FeatureEngineeringError:
                continue

        if not valid_features:
            return np.empty((0, self.feature_dim), dtype=np.float32), []

        return np.array(valid_features, dtype=np.float32), valid_indices
