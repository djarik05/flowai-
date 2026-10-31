"""
Dataset Seeder Utility for GestureFlow AI.

Generates realistic anatomical 3D MediaPipe hand landmarks for standard gestures:
- G001: Open Palm
- G002: Closed Fist
- G003: Thumbs Up
- G004: Peace Sign
- G005: Pointing

Used to populate clean initial training sets and unit test fixtures with
anatomically sound finger configurations.
"""

import math
import random
import time
from typing import Dict, List, Optional
import numpy as np

from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.dataset_service import DatasetService
from app.services.gesture_service import GestureService


class DatasetSeeder:
    """Generates realistic anatomical hand gesture sample sets."""

    def __init__(
        self,
        dataset_service: Optional[DatasetService] = None,
        gesture_service: Optional[GestureService] = None,
    ):
        self._dataset_service = dataset_service or DatasetService()
        self._gesture_service = gesture_service or GestureService()

    @staticmethod
    def _generate_landmarks(gesture_type: str, seed: int = 0) -> List[LandmarkCoord]:
        """
        Generate 21 standard 3D MediaPipe landmarks for a specific gesture pose.
        Wrist at index 0 around (0.5, 0.7, 0.0).
        """
        rng = random.Random(seed)
        jitter = lambda scale=0.008: (rng.random() - 0.5) * scale

        # Base wrist
        wx = 0.5 + jitter(0.02)
        wy = 0.72 + jitter(0.02)
        wz = 0.0 + jitter(0.005)

        # Standard knuckle base positions (MCP joints: thumb 1-2, index 5, middle 9, ring 13, pinky 17)
        mcp_coords = {
            1: (wx - 0.04, wy - 0.05, wz - 0.01),   # Thumb CMC
            2: (wx - 0.07, wy - 0.10, wz - 0.015),  # Thumb MCP
            5: (wx - 0.05, wy - 0.16, wz + 0.005),  # Index MCP
            9: (wx - 0.01, wy - 0.17, wz + 0.003),  # Middle MCP
            13: (wx + 0.03, wy - 0.16, wz + 0.001), # Ring MCP
            17: (wx + 0.06, wy - 0.14, wz - 0.002), # Pinky MCP
        }

        # Determine extension / curled state per finger
        # Format: (thumb_ext, index_ext, middle_ext, ring_ext, pinky_ext)
        if gesture_type == "G001":  # Open Palm: all 5 extended
            ext = (True, True, True, True, True)
        elif gesture_type == "G002":  # Closed Fist: all 5 curled
            ext = (False, False, False, False, False)
        elif gesture_type == "G003":  # Thumbs Up: thumb extended up, others curled
            ext = (True, False, False, False, False)
        elif gesture_type == "G004":  # Peace Sign: index & middle extended, ring & pinky curled
            ext = (False, True, True, False, False)
        elif gesture_type == "G005":  # Pointing: index extended, others curled
            ext = (False, True, False, False, False)
        else:
            ext = (True, True, True, True, True)

        lms: Dict[int, LandmarkCoord] = {
            0: LandmarkCoord(index=0, x=round(wx, 4), y=round(wy, 4), z=round(wz, 4))
        }

        # Thumb
        t_cmc = mcp_coords[1]
        t_mcp = mcp_coords[2]
        lms[1] = LandmarkCoord(index=1, x=round(t_cmc[0] + jitter(), 4), y=round(t_cmc[1] + jitter(), 4), z=round(t_cmc[2] + jitter(), 4))
        lms[2] = LandmarkCoord(index=2, x=round(t_mcp[0] + jitter(), 4), y=round(t_mcp[1] + jitter(), 4), z=round(t_mcp[2] + jitter(), 4))

        if ext[0] and gesture_type == "G003":
            # Thumbs Up points upward (-y)
            lms[3] = LandmarkCoord(index=3, x=round(t_mcp[0] - 0.03 + jitter(), 4), y=round(t_mcp[1] - 0.07 + jitter(), 4), z=round(t_mcp[2] + jitter(), 4))
            lms[4] = LandmarkCoord(index=4, x=round(t_mcp[0] - 0.04 + jitter(), 4), y=round(t_mcp[1] - 0.14 + jitter(), 4), z=round(t_mcp[2] + jitter(), 4))
        elif ext[0]:
            # Open Palm thumb points outwards (-x, -y)
            lms[3] = LandmarkCoord(index=3, x=round(t_mcp[0] - 0.05 + jitter(), 4), y=round(t_mcp[1] - 0.05 + jitter(), 4), z=round(t_mcp[2] + jitter(), 4))
            lms[4] = LandmarkCoord(index=4, x=round(t_mcp[0] - 0.09 + jitter(), 4), y=round(t_mcp[1] - 0.09 + jitter(), 4), z=round(t_mcp[2] + jitter(), 4))
        else:
            # Curled thumb folds across palm (+x, -z)
            lms[3] = LandmarkCoord(index=3, x=round(t_mcp[0] + 0.03 + jitter(), 4), y=round(t_mcp[1] - 0.01 + jitter(), 4), z=round(t_mcp[2] + 0.04 + jitter(), 4))
            lms[4] = LandmarkCoord(index=4, x=round(t_mcp[0] + 0.06 + jitter(), 4), y=round(t_mcp[1] + 0.02 + jitter(), 4), z=round(t_mcp[2] + 0.05 + jitter(), 4))

        # Four fingers generator
        finger_bases = [
            (5, 6, 7, 8, mcp_coords[5], ext[1], -0.015),   # Index
            (9, 10, 11, 12, mcp_coords[9], ext[2], 0.0),    # Middle
            (13, 14, 15, 16, mcp_coords[13], ext[3], 0.015), # Ring
            (17, 18, 19, 20, mcp_coords[17], ext[4], 0.03),  # Pinky
        ]

        for mcp_idx, pip_idx, dip_idx, tip_idx, base, is_extended, spread in finger_bases:
            lms[mcp_idx] = LandmarkCoord(
                index=mcp_idx,
                x=round(base[0] + jitter(), 4),
                y=round(base[1] + jitter(), 4),
                z=round(base[2] + jitter(), 4),
            )
            if is_extended:
                # Extended upward (-y, spread)
                lms[pip_idx] = LandmarkCoord(index=pip_idx, x=round(base[0] + spread * 0.4 + jitter(), 4), y=round(base[1] - 0.06 + jitter(), 4), z=round(base[2] + jitter(), 4))
                lms[dip_idx] = LandmarkCoord(index=dip_idx, x=round(base[0] + spread * 0.7 + jitter(), 4), y=round(base[1] - 0.11 + jitter(), 4), z=round(base[2] + jitter(), 4))
                lms[tip_idx] = LandmarkCoord(index=tip_idx, x=round(base[0] + spread * 1.0 + jitter(), 4), y=round(base[1] - 0.16 + jitter(), 4), z=round(base[2] + jitter(), 4))
            else:
                # Curled downward into palm (+y, +z)
                lms[pip_idx] = LandmarkCoord(index=pip_idx, x=round(base[0] + jitter(), 4), y=round(base[1] - 0.03 + jitter(), 4), z=round(base[2] + 0.03 + jitter(), 4))
                lms[dip_idx] = LandmarkCoord(index=dip_idx, x=round(base[0] + jitter(), 4), y=round(base[1] + 0.02 + jitter(), 4), z=round(base[2] + 0.04 + jitter(), 4))
                lms[tip_idx] = LandmarkCoord(index=tip_idx, x=round(base[0] + jitter(), 4), y=round(base[1] + 0.04 + jitter(), 4), z=round(base[2] + 0.03 + jitter(), 4))

        return [lms[i] for i in range(21)]

    def seed_standard_gestures(
        self,
        samples_per_gesture: int = 15,
        gesture_ids: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """
        Populate sample sets for gestures.
        Returns dict of {gesture_id: added_samples_count}.
        """
        target_ids = gesture_ids or ["G001", "G002", "G003", "G004", "G005"]
        all_gestures = {g.id: g.name for g in self._gesture_service.get_all()}
        results: Dict[str, int] = {}

        for gid in target_ids:
            if gid not in all_gestures:
                continue
            gname = all_gestures[gid]
            session_id = f"session_seed_{gid.lower()}_{int(time.time())}"
            added = 0

            for i in range(samples_per_gesture):
                lms = self._generate_landmarks(gid, seed=i * 100 + int(gid[1:]))
                sample_id = f"s_seed_{gid.lower()}_{i+1:03d}"
                sample = DatasetSample(
                    sample_id=sample_id,
                    gesture_id=gid,
                    gesture_name=gname,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    handedness="Right" if i % 4 != 0 else "Left",
                    handedness_confidence=0.96,
                    landmarks=lms,
                    session_id=session_id,
                )
                try:
                    self._dataset_service.save_sample(sample)
                    added += 1
                except Exception:
                    pass

            results[gid] = added

        return results
