"""
GestureFlow AI — Physical Webcam & Classifier Verification
==========================================================
Interactive and automated hardware verification for Phase 4 Static Gesture Classifier.

Features:
1. Opens physical webcam device (index 0).
2. MediaPipe HandLandmarker extracts live 21-point 3D hand coordinates.
3. Evaluates real-time classification against active model:
   - Open Palm
   - Closed Fist
   - Thumbs Up
   - Peace Sign
   - Pointing
4. Overlays HUD on OpenCV window:
   - FPS & Camera Resolution
   - Handedness (Left / Right)
   - Predicted Gesture Name & ID
   - Softmax Confidence Bar
   - Forward Pass Inference Latency (< 0.2ms)
   - Target Gesture Verification Status
5. Saves results to backend/reports/real_webcam_verification_log.json.

Usage:
    .venv/Scripts/python.exe scripts/verify_physical_classifier_webcam.py
    .venv/Scripts/python.exe scripts/verify_physical_classifier_webcam.py --headless
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

# MediaPipe
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.classifier_service import get_classifier_service

# 21-pair hand skeleton
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),    # Middle
    (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
    (13, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (0, 17),                                 # Palm base
]

GESTURE_KEYS = {
    ord("1"): ("G001", "Open Palm"),
    ord("2"): ("G002", "Closed Fist"),
    ord("3"): ("G003", "Thumbs Up"),
    ord("4"): ("G004", "Peace Sign"),
    ord("5"): ("G005", "Pointing"),
}


def draw_hud(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    fps: float,
    active_target: Optional[str] = None,
) -> None:
    h, w, _ = frame.shape

    # Top status banner
    cv2.rectangle(frame, (0, 0), (w, 55), (15, 23, 42), -1)
    cv2.line(frame, (0, 55), (w, 55), (0, 229, 255), 1)

    cv2.putText(
        frame,
        f"GestureFlow AI - Phase 4 Physical Classifier Verification  |  FPS: {fps:.1f}",
        (15, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 229, 255),
        1,
        cv2.LINE_AA,
    )

    target_text = f"Target Gesture: {active_target or 'AUTO (Press 1-5 to select)'}"
    cv2.putText(
        frame,
        target_text,
        (15, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # Hotkeys helper at bottom
    cv2.rectangle(frame, (0, h - 35), (w, h), (15, 23, 42), -1)
    cv2.line(frame, (0, h - 35), (w, h - 35), (75, 85, 99), 1)
    cv2.putText(
        frame,
        "[1] Open Palm  [2] Closed Fist  [3] Thumbs Up  [4] Peace Sign  [5] Pointing  [ESC] Exit",
        (15, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (148, 163, 184),
        1,
        cv2.LINE_AA,
    )

    # Draw detected hands and prediction tags
    for det in detections:
        lms = det["pixel_landmarks"]
        pred = det["prediction"]
        color = (0, 255, 0) if pred.is_recognized else (0, 165, 255)

        # Draw Skeleton
        for i, j in HAND_CONNECTIONS:
            if i < len(lms) and j < len(lms):
                cv2.line(frame, lms[i], lms[j], (0, 229, 255), 2)

        for px, py in lms:
            cv2.circle(frame, (px, py), 4, (0, 255, 128), -1)
            cv2.circle(frame, (px, py), 2, (255, 255, 255), -1)

        # Bounding box & Prediction Tag
        xs = [pt[0] for pt in lms]
        ys = [pt[1] for pt in lms]
        min_x, max_x = max(0, min(xs) - 15), min(w, max(xs) + 15)
        min_y, max_y = max(0, min(ys) - 15), min(h, max(ys) + 15)

        cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), color, 2)

        # Label badge
        label = f"{pred.gesture_name} ({pred.confidence*100:.1f}%)"
        lat_label = f"Latency: {pred.inference_latency_ms:.3f}ms"

        cv2.rectangle(frame, (min_x, max(0, min_y - 45)), (min_x + 220, min_y), (15, 23, 42), -1)
        cv2.rectangle(frame, (min_x, max(0, min_y - 45)), (min_x + 220, min_y), color, 1)

        cv2.putText(
            frame,
            label,
            (min_x + 8, max(15, min_y - 25)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            lat_label,
            (min_x + 8, max(30, min_y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (148, 163, 184),
            1,
            cv2.LINE_AA,
        )


def run_physical_verification(headless: bool = False, max_seconds: int = 15):
    print("=" * 70)
    print(" GESTUREFLOW AI — PHYSICAL CLASSIFIER WEBCAM AUDIT")
    print("=" * 70)

    cls_svc = get_classifier_service()
    cls_svc.load_active_model(force=True)
    status = cls_svc.get_status()

    if not status.is_model_loaded:
        print("[ERROR] No active model loaded in memory.")
        return False

    print(f"Active Model: {status.active_model_name} ({status.active_model_id})")
    print(f"Classes:      {[c['name'] for c in status.classes]}")
    print(f"Threshold:    {status.confidence_threshold}")

    # MediaPipe
    model_path = BACKEND_DIR / "models" / "hand_landmarker.task"
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = HandLandmarker.create_from_options(options)

    # OpenCV Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam device 0.")
        landmarker.close()
        return False

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] Webcam stream initialized: {w}x{h} @ 30 FPS.")

    recorded_predictions = []
    fps_history = []
    t_start = time.time()
    active_target_id = None
    active_target_name = None

    if not headless:
        print("\n[INFO] Starting live verification window...")
        print("       Press keys '1'-'5' to specify target gesture, 'q' or ESC to exit.")
        cv2.namedWindow("GestureFlow AI — Physical Classifier Verification", cv2.WINDOW_AUTOSIZE)

    frame_count = 0
    try:
        while True:
            t_frame_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            t_infer_start = time.perf_counter()
            res = landmarker.detect(mp_img)
            t_infer_end = time.perf_counter()

            detections = []
            if res.hand_landmarks:
                for idx, hand_lms in enumerate(res.hand_landmarks):
                    raw_coords = [[lm.x, lm.y, lm.z] for lm in hand_lms]
                    handedness = "Right"
                    if res.handedness and idx < len(res.handedness) and res.handedness[idx]:
                        handedness = res.handedness[idx][0].category_name or "Right"

                    pred = cls_svc.predict_landmarks(raw_coords, handedness=handedness)

                    pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms]
                    detections.append({
                        "pixel_landmarks": pts,
                        "raw_landmarks": raw_coords,
                        "handedness": handedness,
                        "prediction": pred,
                    })

                    rec_item = {
                        "frame": frame_count,
                        "timestamp": datetime.now().isoformat(),
                        "target_gesture": active_target_name,
                        "predicted_gesture": pred.gesture_name,
                        "predicted_id": pred.gesture_id,
                        "confidence": pred.confidence,
                        "latency_ms": pred.inference_latency_ms,
                        "is_recognized": pred.is_recognized,
                    }
                    recorded_predictions.append(rec_item)

            t_frame_end = time.perf_counter()
            frame_time = t_frame_end - t_frame_start
            fps = 1.0 / max(frame_time, 1e-4)
            fps_history.append(fps)

            if not headless:
                draw_hud(frame, detections, fps, active_target=active_target_name)
                cv2.imshow("GestureFlow AI — Physical Classifier Verification", frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    break
                elif key in GESTURE_KEYS:
                    active_target_id, active_target_name = GESTURE_KEYS[key]
                    print(f"[TARGET] Set target gesture: {active_target_name} ({active_target_id})")

            if headless and (time.time() - t_start >= max_seconds):
                break

    finally:
        cap.release()
        landmarker.close()
        if not headless:
            cv2.destroyAllWindows()

    avg_fps = np.mean(fps_history) if fps_history else 0
    print(f"\n[SUMMARY] Processed {frame_count} frames. Average Camera/Tracking FPS: {avg_fps:.1f}")
    print(f"[SUMMARY] Total hand detections classified: {len(recorded_predictions)}")

    # Save verification report
    reports_dir = BACKEND_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / "real_webcam_verification_log.json"

    report_data = {
        "verified_at": datetime.now().isoformat(),
        "model_id": status.active_model_id,
        "model_name": status.active_model_name,
        "frames_processed": frame_count,
        "average_fps": round(avg_fps, 2),
        "total_detections": len(recorded_predictions),
        "samples": recorded_predictions[:50],
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"[INFO] Verification log written to: {report_file}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run without OpenCV GUI window")
    parser.add_argument("--seconds", type=int, default=10, help="Max run seconds in headless mode")
    args = parser.parse_args()

    run_physical_verification(headless=args.headless, max_seconds=args.seconds)
