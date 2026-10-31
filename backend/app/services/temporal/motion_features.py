"""
Motion feature extraction data structures for temporal gesture recognition.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class MotionFeatureVector:
    """Quantitative motion metrics extracted from a temporal trajectory window."""
    sample_count: int
    duration_ms: float
    start_pos: Tuple[float, float, float]
    end_pos: Tuple[float, float, float]
    net_dx: float
    net_dy: float
    net_dz: float
    net_distance: float
    path_length: float
    linearity: float                       # Ratio of net distance to cumulative path length [0.0, 1.0]
    avg_velocity_x: float                  # Normalized units / sec
    avg_velocity_y: float
    avg_velocity_z: float
    speed: float                           # Overall speed magnitude (units / sec)
    peak_speed: float                      # Maximum instantaneous velocity observed
    primary_direction: str                 # "left", "right", "up", "down", "forward", "backward", "none"
    reversals_x: int                       # Count of horizontal direction changes
    reversals_y: int                       # Count of vertical direction changes
    scale_ratio: float                     # Ratio of end palm scale to start palm scale
    angular_traversal: float               # Cumulative angular swept angle around centroid (radians)
    closure_distance: float                # Euclidean distance between start and end point

    def to_dict(self) -> Dict[str, float]:
        """Convert scalar features to a dictionary for telemetry or model input."""
        return {
            "duration_ms": self.duration_ms,
            "net_dx": round(self.net_dx, 4),
            "net_dy": round(self.net_dy, 4),
            "net_dz": round(self.net_dz, 4),
            "net_distance": round(self.net_distance, 4),
            "path_length": round(self.path_length, 4),
            "linearity": round(self.linearity, 3),
            "speed": round(self.speed, 3),
            "peak_speed": round(self.peak_speed, 3),
            "scale_ratio": round(self.scale_ratio, 3),
            "angular_traversal": round(self.angular_traversal, 3),
            "reversals_x": float(self.reversals_x),
            "reversals_y": float(self.reversals_y),
        }
