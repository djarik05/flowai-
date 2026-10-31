"""
Vectorized spatial trajectory analysis and movement tracking for hand landmarks.
"""

import math
from typing import List, Optional, Tuple
import numpy as np

from app.services.temporal.motion_features import MotionFeatureVector
from app.services.temporal.temporal_buffer import TemporalFrameBuffer, TemporalObservation


class MovementTracker:
    """
    Computes spatial kinematics, velocities, linearity, reversals, and angular sweeps
    from a TemporalFrameBuffer observation window.
    """

    def __init__(self, target_point: str = "centroid"):
        """
        Args:
            target_point: Reference landmark to track ('centroid', 'wrist', 'palm_center').
        """
        self.target_point = target_point

    def extract_features(
        self,
        buffer: TemporalFrameBuffer,
        duration_s: Optional[float] = None,
    ) -> Optional[MotionFeatureVector]:
        """
        Extract quantitative motion features from recent buffer observations.

        Returns:
            MotionFeatureVector if buffer has >= 3 observations, else None.
        """
        observations = buffer.get_observations(duration_s=duration_s)
        if len(observations) < 3:
            return None

        times, pts = buffer.get_trajectory_points(target=self.target_point, duration_s=duration_s)
        n = len(times)
        if n < 3:
            return None

        # Duration in seconds and ms
        dt_total = float(times[-1] - times[0])
        if dt_total <= 1e-4:
            return None
        duration_ms = dt_total * 1000.0

        start_pos = (float(pts[0, 0]), float(pts[0, 1]), float(pts[0, 2]))
        end_pos = (float(pts[-1, 0]), float(pts[-1, 1]), float(pts[-1, 2]))

        # Net displacements
        dx = float(pts[-1, 0] - pts[0, 0])
        dy = float(pts[-1, 1] - pts[0, 1])
        dz = float(pts[-1, 2] - pts[0, 2])
        net_dist = math.sqrt(dx * dx + dy * dy + dz * dz)

        # Segment-by-segment incremental displacements
        diffs = np.diff(pts, axis=0)  # (N-1, 3)
        seg_dists = np.linalg.norm(diffs, axis=1)  # (N-1,)
        path_length = float(np.sum(seg_dists))

        # Linearity: net distance / cumulative path length
        linearity = net_dist / max(path_length, 1e-5)
        linearity = float(np.clip(linearity, 0.0, 1.0))

        # Velocities
        time_diffs = np.diff(times)
        time_diffs = np.where(time_diffs <= 1e-5, 1e-5, time_diffs)

        seg_velocities = seg_dists / time_diffs  # (N-1,)
        peak_speed = float(np.max(seg_velocities)) if len(seg_velocities) > 0 else 0.0
        avg_speed = path_length / dt_total
        vx = dx / dt_total
        vy = dy / dt_total
        vz = dz / dt_total

        # Primary Direction Classification
        abs_x = abs(dx)
        abs_y = abs(dy)
        abs_z = abs(dz)

        if net_dist < 0.05:
            direction = "none"
        elif abs_x >= abs_y and abs_x >= abs_z:
            direction = "right" if dx > 0 else "left"
        elif abs_y >= abs_x and abs_y >= abs_z:
            direction = "down" if dy > 0 else "up"
        else:
            direction = "backward" if dz > 0 else "forward"

        # Direction reversals (zero-crossings of velocity with noise threshold)
        reversals_x = self._count_reversals(diffs[:, 0], threshold=0.012)
        reversals_y = self._count_reversals(diffs[:, 1], threshold=0.012)

        # Scale ratio (palm size change)
        start_scale = observations[0].palm_scale
        end_scale = observations[-1].palm_scale
        scale_ratio = float(end_scale / max(start_scale, 1e-4))

        # Angular traversal for circular detection
        angular_traversal = self._compute_angular_sweep(pts[:, 0], pts[:, 1])

        # Closure distance
        closure_dist = math.sqrt(dx * dx + dy * dy)

        return MotionFeatureVector(
            sample_count=n,
            duration_ms=duration_ms,
            start_pos=start_pos,
            end_pos=end_pos,
            net_dx=dx,
            net_dy=dy,
            net_dz=dz,
            net_distance=net_dist,
            path_length=path_length,
            linearity=linearity,
            avg_velocity_x=vx,
            avg_velocity_y=vy,
            avg_velocity_z=vz,
            speed=avg_speed,
            peak_speed=peak_speed,
            primary_direction=direction,
            reversals_x=reversals_x,
            reversals_y=reversals_y,
            scale_ratio=scale_ratio,
            angular_traversal=angular_traversal,
            closure_distance=closure_dist,
        )

    def compute_instantaneous_velocity(
        self,
        buffer: TemporalFrameBuffer,
        num_frames: int = 4,
    ) -> Tuple[float, float, float, float]:
        """
        Compute instantaneous velocity from the last few frames.
        Returns: (vx, vy, vz, speed) in normalized units/sec.
        """
        obs = buffer.get_observations()
        if len(obs) < 2:
            return 0.0, 0.0, 0.0, 0.0

        recent = obs[-min(len(obs), num_frames):]
        dt = recent[-1].timestamp - recent[0].timestamp
        if dt <= 1e-4:
            return 0.0, 0.0, 0.0, 0.0

        p0 = recent[0].centroid
        p1 = recent[-1].centroid
        vx = (p1[0] - p0[0]) / dt
        vy = (p1[1] - p0[1]) / dt
        vz = (p1[2] - p0[2]) / dt
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        return vx, vy, vz, speed

    @staticmethod
    def _count_reversals(diffs: np.ndarray, threshold: float = 0.01) -> int:
        """Count significant sign changes in incremental coordinate differences."""
        if len(diffs) < 3:
            return 0

        # Filter out minor noise jitter
        filtered_signs = []
        for d in diffs:
            if d > threshold:
                filtered_signs.append(1)
            elif d < -threshold:
                filtered_signs.append(-1)

        if len(filtered_signs) < 2:
            return 0

        # Count sign transitions
        reversals = 0
        current_sign = filtered_signs[0]
        for s in filtered_signs[1:]:
            if s != current_sign:
                reversals += 1
                current_sign = s
        return reversals

    @staticmethod
    def _compute_angular_sweep(xs: np.ndarray, ys: np.ndarray) -> float:
        """
        Compute cumulative angular traversal around the trajectory centroid.
        If trajectory makes a full circle, cumulative angle is ~2*pi (6.28 rad).
        """
        if len(xs) < 6:
            return 0.0

        cx = float(np.mean(xs))
        cy = float(np.mean(ys))

        angles = np.arctan2(ys - cy, xs - cx)
        # Unwrap angles to handle 360-degree boundary wrap
        unwrapped = np.unwrap(angles)
        total_sweep = float(abs(unwrapped[-1] - unwrapped[0]))
        return total_sweep
