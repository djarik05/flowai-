"""
Profile Before Optimization for GestureFlow AI Hand Tracking Pipeline.
Benchmarks:
1. MediaPipe IMAGE mode (current backend baseline) vs VIDEO mode.
2. Resolutions: 320x240, 640x480, 1280x720.
3. Zero hands, One hand, Two hands.
4. Per-frame import overhead (from mediapipe import Image, ImageFormat).
5. Frame copy overhead (np.ndarray.copy).
6. CameraManager frame capture rate.
"""

import os
import sys
import time
from pathlib import Path
import numpy as np
import cv2

# Set path to backend
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import Image, ImageFormat

MODEL_PATH = str((BACKEND_DIR / "models" / "hand_landmarker.task").resolve())

def create_synthetic_frames(width, height):
    """Create test frames: 0 hands (empty), 1 hand (colored ellipse pattern), 2 hands."""
    # 0 hands - uniform/gradient background
    frame_0 = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        frame_0[y, :] = (int(30 + 40 * y / height), int(40 + 50 * y / height), int(50 + 60 * y / height))
        
    # 1 hand - flesh tones skin-like patch with palm and fingers
    frame_1 = frame_0.copy()
    cv2.ellipse(frame_1, (int(width * 0.5), int(height * 0.55)), (int(width * 0.12), int(height * 0.16)), 0, 0, 360, (130, 160, 210), -1)
    for i in range(5):
        fx = int(width * (0.42 + i * 0.04))
        fy = int(height * 0.35)
        cv2.line(frame_1, (int(width * 0.5), int(height * 0.5)), (fx, fy), (130, 160, 210), int(width * 0.025))

    # 2 hands
    frame_2 = frame_0.copy()
    # Hand left
    cv2.ellipse(frame_2, (int(width * 0.3), int(height * 0.55)), (int(width * 0.1), int(height * 0.14)), -15, 0, 360, (130, 160, 210), -1)
    # Hand right
    cv2.ellipse(frame_2, (int(width * 0.7), int(height * 0.55)), (int(width * 0.1), int(height * 0.14)), 15, 0, 360, (130, 160, 210), -1)

    return frame_0, frame_1, frame_2


def benchmark_mode(running_mode_str, resolution=(640, 480), max_hands=2, iterations=60):
    width, height = resolution
    frame_0, frame_1, frame_2 = create_synthetic_frames(width, height)

    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    
    if running_mode_str == "IMAGE":
        mode = vision.RunningMode.IMAGE
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mode,
            num_hands=max_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        detector = vision.HandLandmarker.create_from_options(options)

        # Warmup
        rgb = cv2.cvtColor(frame_1, cv2.COLOR_BGR2RGB)
        mp_img = Image(image_format=ImageFormat.SRGB, data=rgb)
        for _ in range(5):
            detector.detect(mp_img)

        # Measure 0 hands
        rgb0 = cv2.cvtColor(frame_0, cv2.COLOR_BGR2RGB)
        mp_img0 = Image(image_format=ImageFormat.SRGB, data=rgb0)
        t0 = time.perf_counter()
        for _ in range(iterations):
            detector.detect(mp_img0)
        dur0 = (time.perf_counter() - t0) / iterations * 1000

        # Measure 1 hand
        rgb1 = cv2.cvtColor(frame_1, cv2.COLOR_BGR2RGB)
        mp_img1 = Image(image_format=ImageFormat.SRGB, data=rgb1)
        t1 = time.perf_counter()
        for _ in range(iterations):
            detector.detect(mp_img1)
        dur1 = (time.perf_counter() - t1) / iterations * 1000

        # Measure 2 hands
        rgb2 = cv2.cvtColor(frame_2, cv2.COLOR_BGR2RGB)
        mp_img2 = Image(image_format=ImageFormat.SRGB, data=rgb2)
        t2 = time.perf_counter()
        for _ in range(iterations):
            detector.detect(mp_img2)
        dur2 = (time.perf_counter() - t2) / iterations * 1000

        detector.close()

    else:  # VIDEO mode
        mode = vision.RunningMode.VIDEO
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mode,
            num_hands=max_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        detector = vision.HandLandmarker.create_from_options(options)

        rgb1 = cv2.cvtColor(frame_1, cv2.COLOR_BGR2RGB)
        mp_img1 = Image(image_format=ImageFormat.SRGB, data=rgb1)
        # Warmup
        for i in range(5):
            detector.detect_for_video(mp_img1, i * 33)

        # Measure 0 hands
        rgb0 = cv2.cvtColor(frame_0, cv2.COLOR_BGR2RGB)
        mp_img0 = Image(image_format=ImageFormat.SRGB, data=rgb0)
        t0 = time.perf_counter()
        for i in range(iterations):
            detector.detect_for_video(mp_img0, (10 + i) * 33)
        dur0 = (time.perf_counter() - t0) / iterations * 1000

        # Measure 1 hand
        t1 = time.perf_counter()
        for i in range(iterations):
            detector.detect_for_video(mp_img1, (1000 + i) * 33)
        dur1 = (time.perf_counter() - t1) / iterations * 1000

        # Measure 2 hands
        rgb2 = cv2.cvtColor(frame_2, cv2.COLOR_BGR2RGB)
        mp_img2 = Image(image_format=ImageFormat.SRGB, data=rgb2)
        t2 = time.perf_counter()
        for i in range(iterations):
            detector.detect_for_video(mp_img2, (2000 + i) * 33)
        dur2 = (time.perf_counter() - t2) / iterations * 1000

        detector.close()

    return {
        "0_hands_ms": dur0,
        "1_hand_ms": dur1,
        "2_hands_ms": dur2,
        "avg_ms": (dur0 + dur1 + dur2) / 3.0,
        "est_fps": 1000.0 / ((dur0 + dur1 + dur2) / 3.0),
    }


def benchmark_copy_and_imports(iterations=500):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Copy overhead
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = frame.copy()
    copy_ms = (time.perf_counter() - t0) / iterations * 1000

    # In-loop dynamic import overhead
    t1 = time.perf_counter()
    for _ in range(iterations):
        from mediapipe import Image, ImageFormat
        _ = Image
        _ = ImageFormat
    import_ms = (time.perf_counter() - t1) / iterations * 1000

    # Color conversion
    t2 = time.perf_counter()
    for _ in range(iterations):
        _ = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cvtColor_ms = (time.perf_counter() - t2) / iterations * 1000

    return {
        "copy_ms": copy_ms,
        "import_ms": import_ms,
        "cvtColor_ms": cvtColor_ms,
    }


def main():
    print("=" * 65)
    print("GESTUREFLOW AI: HAND TRACKING PIPELINE PROFILING (BASELINE)")
    print("=" * 65)
    print(f"Model: {MODEL_PATH}")

    # Micro-benchmarks
    micro = benchmark_copy_and_imports()
    print("\n[1] Micro-benchmarks (Frame overhead per cycle):")
    print(f"  Frame copy (640x480):         {micro['copy_ms']:.3f} ms")
    print(f"  In-loop dynamic import:       {micro['import_ms']:.4f} ms")
    print(f"  cv2.cvtColor BGR->RGB:        {micro['cvtColor_ms']:.3f} ms")

    # Benchmark IMAGE mode (current backend baseline)
    print("\n[2] CURRENT BACKEND: MediaPipe IMAGE Mode:")
    for res in [(320, 240), (640, 480), (1280, 720)]:
        r = benchmark_mode("IMAGE", resolution=res, iterations=40)
        print(f"  Resolution {res[0]}x{res[1]}:")
        print(f"    0 hands: {r['0_hands_ms']:.2f} ms | 1 hand: {r['1_hand_ms']:.2f} ms | 2 hands: {r['2_hands_ms']:.2f} ms")
        print(f"    Average: {r['avg_ms']:.2f} ms -> Max possible FPS: {r['est_fps']:.1f} FPS")

    # Benchmark VIDEO mode (proposed optimization)
    print("\n[3] OPTIMIZED TARGET: MediaPipe VIDEO Mode:")
    for res in [(320, 240), (640, 480), (1280, 720)]:
        r = benchmark_mode("VIDEO", resolution=res, iterations=40)
        print(f"  Resolution {res[0]}x{res[1]}:")
        print(f"    0 hands: {r['0_hands_ms']:.2f} ms | 1 hand: {r['1_hand_ms']:.2f} ms | 2 hands: {r['2_hands_ms']:.2f} ms")
        print(f"    Average: {r['avg_ms']:.2f} ms -> Max possible FPS: {r['est_fps']:.1f} FPS")

    # Compare 1 hand vs 2 hands in VIDEO mode at 640x480
    r_1hand = benchmark_mode("VIDEO", resolution=(640, 480), max_hands=1, iterations=40)
    r_2hands = benchmark_mode("VIDEO", resolution=(640, 480), max_hands=2, iterations=40)
    print("\n[4] Hand Count Comparison (VIDEO mode @ 640x480):")
    print(f"  1-Hand Cap:   Avg {r_1hand['avg_ms']:.2f} ms ({r_1hand['est_fps']:.1f} FPS)")
    print(f"  2-Hands Cap:  Avg {r_2hands['avg_ms']:.2f} ms ({r_2hands['est_fps']:.1f} FPS)")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    main()
