"""
Rule-based heuristic gesture matching engine for Phase 5 Dynamic Gestures.
"""

import math
from typing import Optional, Tuple
from app.services.temporal.motion_features import MotionFeatureVector
from app.services.temporal.temporal_config import TemporalConfig, TEMPORAL_GESTURE_CATALOG


class GestureRuleMatcher:
    """
    Evaluates extracted MotionFeatureVector against calibrated geometric and kinematic criteria.
    Returns: (gesture_id, gesture_name, confidence) if matched, else None.
    """

    @classmethod
    def evaluate(cls, feat: MotionFeatureVector) -> Optional[Tuple[str, str, float]]:
        """
        Evaluate features in prioritized order.
        Returns:
            (gesture_id, gesture_name, confidence) or None.
        """
        # 1. Circle Check (Looping trajectories should take priority over swipes)
        circle_res = cls._match_circle(feat)
        if circle_res:
            return circle_res

        # 2. Wave Check (Oscillations take priority over linear swipes)
        wave_res = cls._match_wave(feat)
        if wave_res:
            return wave_res

        # 3. Linear Swipes (Left, Right, Up, Down)
        swipe_res = cls._match_swipes(feat)
        if swipe_res:
            return swipe_res

        # 4. Experimental Depth Gestures (Push, Pull, Double Tap)
        depth_res = cls._match_depth_gestures(feat)
        if depth_res:
            return depth_res

        return None

    @classmethod
    def _match_swipes(cls, feat: MotionFeatureVector) -> Optional[Tuple[str, str, float]]:
        """Evaluate horizontal and vertical swipe gestures."""
        # Duration check
        if not (TemporalConfig.SWIPE_MIN_DURATION_MS <= feat.duration_ms <= TemporalConfig.SWIPE_MAX_DURATION_MS):
            return None

        # Speed and linearity check
        if feat.speed < TemporalConfig.SWIPE_MIN_VELOCITY or feat.linearity < TemporalConfig.SWIPE_MIN_LINEARITY:
            return None

        abs_dx = abs(feat.net_dx)
        abs_dy = abs(feat.net_dy)

        # A. Horizontal Swipes (Left / Right)
        if abs_dx >= TemporalConfig.SWIPE_MIN_DISPLACEMENT and abs_dx > abs_dy * TemporalConfig.SWIPE_PRIMARY_AXIS_RATIO:
            confidence = min(
                0.98,
                0.65 + (feat.linearity * 0.20) + (min(1.0, abs_dx / 0.35) * 0.15)
            )
            if feat.net_dx < 0:
                return "T001", "Swipe Left", round(confidence, 3)
            else:
                return "T002", "Swipe Right", round(confidence, 3)

        # B. Vertical Swipes (Up / Down) - Screen Y: 0 is top, 1 is bottom
        if abs_dy >= TemporalConfig.SWIPE_MIN_DISPLACEMENT and abs_dy > abs_dx * TemporalConfig.SWIPE_PRIMARY_AXIS_RATIO:
            confidence = min(
                0.98,
                0.65 + (feat.linearity * 0.20) + (min(1.0, abs_dy / 0.35) * 0.15)
            )
            if feat.net_dy < 0:
                # -Y is upward
                return "T003", "Swipe Up", round(confidence, 3)
            else:
                # +Y is downward
                return "T004", "Swipe Down", round(confidence, 3)

        return None

    @classmethod
    def _match_wave(cls, feat: MotionFeatureVector) -> Optional[Tuple[str, str, float]]:
        """Evaluate oscillating hand wave."""
        if not (TemporalConfig.WAVE_MIN_DURATION_MS <= feat.duration_ms <= TemporalConfig.WAVE_MAX_DURATION_MS):
            return None

        # Wave requires >= 3 reversals in X, high cumulative path length, and bounded net displacement
        if (
            feat.reversals_x >= TemporalConfig.WAVE_MIN_DIRECTION_CHANGES
            and feat.path_length >= TemporalConfig.WAVE_MIN_PATH_LENGTH
            and abs(feat.net_dx) <= TemporalConfig.WAVE_MAX_NET_DISPLACEMENT
        ):
            reversal_bonus = min(0.15, (feat.reversals_x - 3) * 0.05)
            confidence = min(0.96, 0.75 + reversal_bonus + (min(1.0, feat.path_length / 0.6) * 0.10))
            return "T005", "Wave", round(confidence, 3)

        return None

    @classmethod
    def _match_circle(cls, feat: MotionFeatureVector) -> Optional[Tuple[str, str, float]]:
        """Evaluate circular looping trajectory."""
        if not (TemporalConfig.CIRCLE_MIN_DURATION_MS <= feat.duration_ms <= TemporalConfig.CIRCLE_MAX_DURATION_MS):
            return None

        # Angular traversal must be >= 4.8 radians (~275 degrees)
        # Closure distance (start to end) must be small relative to path
        max_allowed_gap = (feat.path_length / math.pi) * TemporalConfig.CIRCLE_CLOSURE_RATIO
        if (
            feat.angular_traversal >= TemporalConfig.CIRCLE_MIN_ANGULAR_TRAVERSAL_RAD
            and feat.path_length >= 0.28
            and feat.closure_distance <= max_allowed_gap
        ):
            confidence = min(
                0.95,
                0.70 + (min(1.0, feat.angular_traversal / (2 * math.pi)) * 0.15) + (min(1.0, feat.path_length / 0.5) * 0.10)
            )
            return "T006", "Circle", round(confidence, 3)

        return None

    @classmethod
    def _match_depth_gestures(cls, feat: MotionFeatureVector) -> Optional[Tuple[str, str, float]]:
        """Evaluate experimental depth/scale gestures (Push, Pull, Double Tap)."""
        lateral_move = math.sqrt(feat.net_dx * feat.net_dx + feat.net_dy * feat.net_dy)
        if lateral_move > TemporalConfig.PUSH_PULL_MAX_XY_DISPLACEMENT:
            return None

        # Push: hand expands towards camera (scale ratio increases) or -dz
        if (
            TemporalConfig.PUSH_PULL_MIN_DURATION_MS <= feat.duration_ms <= TemporalConfig.PUSH_PULL_MAX_DURATION_MS
            and (feat.scale_ratio >= 1.0 + TemporalConfig.PUSH_PULL_MIN_SCALE_CHANGE or feat.net_dz < -0.15)
        ):
            confidence = min(0.90, 0.65 + (feat.scale_ratio - 1.0) * 0.8)
            return "T007", "Push", round(confidence, 3)

        # Pull: hand shrinks away from camera (scale ratio decreases) or +dz
        if (
            TemporalConfig.PUSH_PULL_MIN_DURATION_MS <= feat.duration_ms <= TemporalConfig.PUSH_PULL_MAX_DURATION_MS
            and (feat.scale_ratio <= 1.0 - TemporalConfig.PUSH_PULL_MIN_SCALE_CHANGE or feat.net_dz > 0.15)
        ):
            confidence = min(0.90, 0.65 + (1.0 - feat.scale_ratio) * 0.8)
            return "T008", "Pull", round(confidence, 3)

        # Double Tap (Experimental): High peak velocity with low net lateral distance
        if (
            250.0 <= feat.duration_ms <= TemporalConfig.DOUBLE_TAP_MAX_INTERVAL_MS
            and feat.peak_speed >= TemporalConfig.DOUBLE_TAP_MIN_PEAK_VELOCITY * 1.5
            and lateral_move < 0.08
        ):
            return "T009", "Double Tap", 0.72

        return None
