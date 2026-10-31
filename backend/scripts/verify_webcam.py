#!/usr/bin/env python
"""
GestureFlow AI — Standalone Webcam Hand-Tracking Verification
=============================================================
Opens the physical webcam, loads the real MediaPipe Hand Landmarker model,
detects hands in live frames, and draws all 21 landmarks + connections on
an OpenCV preview window with a HUD overlay.

Press ESC to quit.  No mocks — real hardware only.

Usage:
    cd <backend_dir>
    .venv/Scripts/python.exe scripts/verify_webcam.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# MediaPipe imports
# ---------------------------------------------------------------------------
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
    RunningMode,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BACKEND_DIR / "models" / "hand_landmarker.task"

# 21-pair hand skeleton (MediaPipe standard)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),       # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17),                                # Palm base
]

# Per-hand colours (BGR)
HAND_COLORS = [
    (0, 255, 0),    # Green  — 1st hand
    (255, 128, 0),  # Blue   — 2nd hand
    (0, 0, 255),    # Red    — 3rd hand (unlikely but safe)
    (255, 255, 0),  # Cyan   — 4th hand
]

LANDMARK_RADIUS = 4
CONNECTION_THICKNESS = 2
HUD_FONT = cv2.FONT_HERSHEY_SIMPLEX
HUD_SCALE = 0.55
HUD_COLOR = (0, 255, 255)  # Yellow
HUD_SHADOW = (0, 0, 0)     # Black shadow for readability
HUD_THICKNESS = 1

WINDOW_NAME = "GestureFlow AI — Webcam Verification"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_model_path() -> Path:
    """Return the absolute path to the hand_landmarker.task model file."""
    env_path = os.environ.get("HAND_LANDMARKER_MODEL_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        p = p.resolve()
    else:
        p = DEFAULT_MODEL_PATH.resolve()

    if not p.exists():
        print(f"[ERROR] Model file not found: {p}")
        print(
            "Download it with:\n"
            "  curl -L -o models/hand_landmarker.task "
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        )
        sys.exit(1)

    print(f"[INFO] Model: {p}  ({p.stat().st_size:,} bytes)")
    return p


def draw_hand(
    frame: np.ndarray,
    landmarks: list[tuple[float, float, float]],
    color: tuple[int, int, int],
    h: int,
    w: int,
) -> None:
    """Draw landmarks + connections for one hand on *frame* (BGR)."""
    pts = [(int(lm[0] * w), int(lm[1] * h)) for lm in landmarks]

    # Connections
    for i, j in HAND_CONNECTIONS:
        if i < len(pts) and j < len(pts):
            cv2.line(frame, pts[i], pts[j], color, CONNECTION_THICKNESS)

    # Landmarks
    for px, py in pts:
        cv2.circle(frame, (px, py), LANDMARK_RADIUS, color, -1)
        cv2.circle(frame, (px, py), LANDMARK_RADIUS, (255, 255, 255), 1)


def put_text(frame: np.ndarray, text: str, x: int, y: int) -> None:
    """Draw text with a dark shadow for readability on any background."""
    cv2.putText(frame, text, (x + 1, y + 1), HUD_FONT, HUD_SCALE, HUD_SHADOW, HUD_THICKNESS + 1)
    cv2.putText(frame, text, (x, y), HUD_FONT, HUD_SCALE, HUD_COLOR, HUD_THICKNESS)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  GestureFlow AI — Webcam Hand-Tracking Verification")
    print("=" * 60)

    # --- Model -----------------------------------------------------------
    model_path = resolve_model_path()

    # --- Landmarker (IMAGE mode — one frame at a time) -------------------
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = HandLandmarker.create_from_options(options)
    print("[INFO] HandLandmarker initialised.")

    # --- Camera ----------------------------------------------------------
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam (index 0).")
        landmarker.close()
        sys.exit(1)

    cam_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cam_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cam_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"[INFO] Camera opened: {cam_w}x{cam_h} @ {cam_fps:.0f} fps")
    print("[INFO] Press ESC to quit.\n")

    frame_count = 0
    total_hands_detected = 0
    fps = 0.0
    prev_time = time.time()
    detection_status = "Starting…"

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                detection_status = "Camera read failed"
                # Show a blank frame with status for a moment then retry
                blank = np.zeros((cam_h, cam_w, 3), dtype=np.uint8)
                put_text(blank, detection_status, 10, 30)
                cv2.imshow(WINDOW_NAME, blank)
                if cv2.waitKey(100) & 0xFF == 27:
                    break
                continue

            frame_count += 1

            # --- Detect ------------------------------------------------
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            try:
                result: HandLandmarkerResult = landmarker.detect(mp_image)
            except Exception as exc:
                detection_status = f"Error: {exc}"
                result = None

            # --- Draw hands --------------------------------------------
            num_hands = 0
            hand_labels: list[str] = []

            if result and result.hand_landmarks:
                num_hands = len(result.hand_landmarks)
                total_hands_detected += num_hands

                for idx, (lms, handedness_list) in enumerate(
                    zip(result.hand_landmarks, result.handedness)
                ):
                    color = HAND_COLORS[idx % len(HAND_COLORS)]

                    # Convert NormalizedLandmark → (x, y, z) tuples
                    landmarks = [(lm.x, lm.y, lm.z) for lm in lms]
                    draw_hand(frame, landmarks, color, cam_h, cam_w)

                    # Handedness label
                    if handedness_list:
                        cat = handedness_list[0]
                        label = f"{cat.category_name} ({cat.score:.0%})"
                    else:
                        label = "Unknown"
                    hand_labels.append(label)

                detection_status = "Detecting"
            else:
                detection_status = "No hands"

            # --- FPS ---------------------------------------------------
            now = time.time()
            dt = now - prev_time
            if dt > 0:
                fps = 1.0 / dt
            prev_time = now

            # --- HUD overlay ------------------------------------------
            y0 = 22
            dy = 22
            put_text(frame, f"Camera: {cam_w}x{cam_h} @ {cam_fps:.0f}fps", 10, y0)
            put_text(frame, f"FPS: {fps:.1f}", 10, y0 + dy)
            put_text(frame, f"Hands: {num_hands}", 10, y0 + 2 * dy)
            put_text(frame, f"Status: {detection_status}", 10, y0 + 3 * dy)

            for i, lbl in enumerate(hand_labels):
                color = HAND_COLORS[i % len(HAND_COLORS)]
                cv2.putText(
                    frame,
                    f"  Hand {i+1}: {lbl}",
                    (11, y0 + (4 + i) * dy + 1),
                    HUD_FONT, HUD_SCALE, HUD_SHADOW, HUD_THICKNESS + 1,
                )
                cv2.putText(
                    frame,
                    f"  Hand {i+1}: {lbl}",
                    (10, y0 + (4 + i) * dy),
                    HUD_FONT, HUD_SCALE, color, HUD_THICKNESS,
                )

            cv2.imshow(WINDOW_NAME, frame)

            # ESC to quit
            if cv2.waitKey(1) & 0xFF == 27:
                print("\n[INFO] ESC pressed — shutting down.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C — shutting down.")

    finally:
        # --- Cleanup ----------------------------------------------------
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()
        elapsed = time.time() - (prev_time - (1 / max(fps, 1)))
        print(f"[INFO] Processed {frame_count} frames.")
        print(f"[INFO] Total hand detections (cumulative): {total_hands_detected}")
        print("[INFO] Resources released. Done.")


if __name__ == "__main__":
    main()
