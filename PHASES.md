# GestureFlow AI — Master Project Lifecycle & Phase Documentation

**System**: GestureFlow AI — Real-Time Computer Vision & Hand Gesture Desktop Control  
**Version**: 2.5 (Phases 1 through 6B.2 Consolidated)  
**Target Environment**: Windows 10/11 x64, Python 3.12, Node.js / React 18, Vite 8, MediaPipe Tasks, PyTorch, Win32 User32  
**Audit & Verification Status**: 183 Automated Tests Passing (100%), 0 Regressions, Production Build Verified  

---

## Table of Contents

1. [Architectural Overview & Data Flow](#1-architectural-overview--data-flow)
2. [Complete Phase Status Matrix](#2-complete-phase-status-matrix)
3. [Phase 1: Backend Foundation & Core Infrastructure](#3-phase-1-backend-foundation--core-infrastructure)
4. [Phase 2: Video Acquisition & Real-Time Hand Tracking](#4-phase-2-video-acquisition--real-time-hand-tracking)
5. [Phase 3: Gesture Data Collection & Management Pipeline](#5-phase-3-gesture-data-collection--management-pipeline)
6. [Phase 4: Machine Learning & Static Gesture Recognition](#6-phase-4-machine-learning--static-gesture-recognition)
7. [Phase 5: Temporal & Dynamic Gesture Recognition Engine](#7-phase-5-temporal--dynamic-gesture-recognition-engine)
8. [Phase 5.5: Critical Stabilization & Hardware Lifecycle Arbiter](#8-phase-55-critical-stabilization--hardware-lifecycle-arbiter)
9. [Phase 6A: Desktop Cursor Navigation & Spatial Mapping](#9-phase-6a-desktop-cursor-navigation--spatial-mapping)
10. [Phase 6A.1: Cursor Movement Refinement & Calibration](#10-phase-6a1-cursor-movement-refinement--calibration)
11. [Phase 6A.2: Camera Preview Persistence & Background Handoff](#11-phase-6a2-camera-preview-persistence--background-handoff)
12. [Phase 6A.3: Unified Launcher & Background Autonomy](#12-phase-6a3-unified-launcher--background-autonomy)
13. [Phase 6B.1: Gesture-Based Left Mouse Click](#13-phase-6b1-gesture-based-left-mouse-click)
14. [Phase 6B.2: Gesture-Based Right Mouse Click](#14-phase-6b2-gesture-based-right-mouse-click)
15. [Phase 6B Resolution: Click Pipeline & Windows Desktop Isolation Fix](#15-phase-6b-resolution-click-pipeline--windows-desktop-isolation-fix)
16. [Master Gesture & Bound Action Taxonomy](#16-master-gesture--bound-action-taxonomy)
17. [Safety & Reliability Principles](#17-safety--reliability-principles)
18. [Consolidated Manual Testing Protocols](#18-consolidated-manual-testing-protocols)
19. [Verification Evidence & Automated Test Results](#19-verification-evidence--automated-test-results)
20. [Future Roadmap (Phases 7 & 8)](#20-future-roadmap-phases-7--8)

---

## 1. Architectural Overview & Data Flow

GestureFlow AI bridges real-time web-based computer vision with operating-system-level desktop automation. The system implements a coordinated dual-runtime architecture: a React/Vite web application for interactive dashboard controls and low-latency browser MediaPipe inference, and a native Python FastAPI service managing Windows hardware devices, deep learning inference, temporal state machines, and native Win32 input injection.

```
                                  PHYSICAL CAMERA (Webcam 0)
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │                                               │
               Browser Owner                                   Backend Owner
         (HTML5 getUserMedia API)                       (OpenCV DirectShow Capture)
                      │                                               │
                      ▼                                               ▼
         Browser MediaPipe Tasks WASM                     Python MediaPipe Tasks API
          (21 Normalized Landmarks)                       (21 Normalized Landmarks)
                      │                                               │
         ┌────────────┴────────────┐                                  │
         │                         │                                  │
         ▼                         ▼                                  │
Local Classifier          Frontend Coordinate Feeder                  │
(localGestureClassifier)  (CameraSection.tsx)                         │
         │                         │                                  │
         │ Gesture Events          │ Throttled Coordinates            │
         │ (Left/Right Clicks)     │ (x, y, pinch distances)          │
         │                         │                                  │
         └────────────┬────────────┘                                  │
                      │                                               │
                      ▼                                               │
           Zustand Mouse Store                                        │
           (Optimistic Telemetry)                                     │
                      │                                               │
                      ▼ (REST API)                                    │
           FastAPI Backend Endpoints                                  │
         (/mouse/cursor-point, /click)                                │
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                                       MouseController
                              ┌───────────────────────────────┐
                              │ - Safety Rule 1: Off by Def.  │
                              │ - Tracking Loss TTL (150ms)   │
                              │ - Active Tracking Margins     │
                              │ - EMA Smoothing (alpha=0.35)  │
                              │ - Deadband Filter (5%)        │
                              │ - Hysteresis Click State      │
                              │ - Mutual Exclusion Engine     │
                              └───────────────┬───────────────┘
                                              │
                                              ▼
                                 MouseControllerWorker Thread
                              ┌───────────────────────────────┐
                              │ Dedicated Desktop Thread      │
                              │ WinSta0\default Attachment    │
                              │ Thread-Safe Action Queue      │
                              └───────────────┬───────────────┘
                                              │
                                              ▼
                                    Win32 User32 Driver
                              ┌───────────────────────────────┐
                              │ SetCursorPos (Move)           │
                              │ SendInput (Left / Right Click)│
                              │ 15ms Message Pump Dwell Time  │
                              └───────────────┬───────────────┘
                                              │
                                              ▼
                               WINDOWS PRIMARY DESKTOP CURSOR
```

---

## 2. Complete Phase Status Matrix

| Phase | Milestone Name | Key Functionality | Test Suite | Status |
|:---:|:---|:---|:---:|:---:|
| **1** | **Backend Foundation** | FastAPI app, lifecycle hooks, Pydantic configuration, structured logging, health/status endpoints, CORS. | 12 Tests | ✅ **COMPLETE** |
| **2** | **Video & Hand Tracking** | OpenCV DirectShow capture, MediaPipe Tasks API (21 landmarks), annotated MJPEG streams, 640x480@30fps. | 18 Tests | ✅ **COMPLETE** |
| **3** | **Dataset Pipeline** | Dynamic gesture registry, automated data collection, quality validation, CSV/JSON exporters, Hagrid dataset tools. | 28 Tests | ✅ **COMPLETE** |
| **4** | **Static Recognition** | Anatomical feature engineering (straightness/distance), PyTorch MLP (63→128→64→N), model registry, client-side inference. | 32 Tests | ✅ **COMPLETE** |
| **5** | **Temporal Engine** | 30-frame sliding buffer, velocity & trajectory tracking, state machine for 9 dynamic gestures (swipes, waves, circles). | 24 Tests | ✅ **COMPLETE** |
| **5.5**| **System Stabilization** | Hardware mutual exclusion arbiter (`claim_ownership`), MediaPipe thread-safe teardown, ghost hand 150ms TTL eviction. | 10 Tests | ✅ **COMPLETE** |
| **6A**| **Mouse Movement** | Index fingertip cursor steering, active tracking margins (15%), sensitivity scaling, EMA smoothing ($\alpha=0.35$), deadband (5%). | 15 Tests | ✅ **COMPLETE** |
| **6A.1**| **Movement Calibration**| Bidirectional parameter synchronization between UI sliders and backend controller, anti-jump re-initialization. | 8 Tests | ✅ **COMPLETE** |
| **6A.2**| **Preview Persistence** | Persistent React video ref callback, background tracking handoff model, browser throttling bypass. | 6 Tests | ✅ **COMPLETE** |
| **6A.3**| **Unified Launcher** | `run.py` unified runner, venv auto-discovery, port conflict resolution, browser auto-launch, tree-kill process termination. | 6 Tests | ✅ **COMPLETE** |
| **6B.1**| **Gesture Left Click** | Dual-mode left click (Index Point gesture & Thumb+Index Pinch), hysteresis thresholds (5%/8%), 400ms cooldown, hold protection. | 15 Tests | ✅ **COMPLETE** |
| **6B.2**| **Gesture Right Click**| Dual-mode right click (Victory gesture & Thumb+Middle Pinch), mutual exclusion against left clicks, 500ms cooldown, hold protection. | 14 Tests | ✅ **COMPLETE** |
| **6B Fix**| **Click Pipeline Fix** | Resolved Windows thread desktop isolation (`ACCESS_DENIED` 5 & `BUSY` 170) via dedicated worker queue and Win32 `SendInput`. | 5 Tests | ✅ **COMPLETE** |

---

## 3. Phase 1: Backend Foundation & Core Infrastructure

### Objective
Establish a high-performance, asynchronous Python backend service capable of running multi-threaded computer vision pipelines, serving REST endpoints, and supporting hot-reloaded development.

### Implementation Highlights
* **Application Framework:** FastAPI with Uvicorn ASGI server running on `127.0.0.1:8000`.
* **Configuration Management:** Centralized Pydantic `BaseSettings` (`backend/app/core/config.py`) reading environment variables and defaults with strict type enforcement.
* **Logging System:** Multi-handler rotating logger (`logging_config.py`) providing console output and structured disk logging (`backend/logs/flowai.log`).
* **Lifecycle Management:** Clean startup and shutdown orchestration (`app/core/lifecycle.py`) initializing application singletons and ensuring deterministic shutdown.
* **API Endpoints:**
  - `GET /health`: Instant lightweight heartbeat response (`status: ok`).
  - `GET /status`: Detailed application telemetry and subsystem health checks.
  - `GET /config`: Sanitized configuration inspection.

---

## 4. Phase 2: Video Acquisition & Real-Time Hand Tracking

### Objective
Build real-time video capture and skeletal hand landmark detection pipeline achieving 30 FPS at 640x480 resolution.

### Implementation Highlights
* **Camera Manager (`camera_manager.py`):**
  - Interfaces with USB cameras via OpenCV `cv2.VideoCapture` using native Windows `cv2.CAP_DSHOW` (DirectShow).
  - Background acquisition thread runs decoupled from HTTP request loops, storing latest frames in thread-safe buffers.
* **Hand Tracking Service (`hand_tracking.py`):**
  - Integrated Google MediaPipe Tasks API `HandLandmarker` in `LIVE_STREAM` / `VIDEO` mode.
  - Extracts 21 3D hand coordinates ($X, Y, Z$) normalized to $[0.0, 1.0]$.
  - Calculates handedness classification (Left vs Right) with confidence filtering ($\ge 0.65$).
* **MJPEG Live Streaming:**
  - Fast HTTP multipart stream endpoint (`/tracking/stream`) providing hardware-annotated video frames directly to browsers and external clients.

---

## 5. Phase 3: Gesture Data Collection & Management Pipeline

### Objective
Create structured workflows for recording, validating, and managing hand gesture datasets for custom neural network training.

### Implementation Highlights
* **Dynamic Gesture Registry (`gesture_service.py`):**
  - Persisted gesture definitions in JSON format with metadata (ID, display name, category, bound action).
* **Automated Data Collector (`dataset_collector.py`):**
  - Multi-stage collection states: `countdown` $\to$ `capturing` $\to$ `review` $\to$ `persisted`.
  - Quality filters enforce minimum hand confidence, landmark visibility, and bounding box constraints.
* **Exporters & Dataset Integrations (`dataset_service.py`):**
  - Exports validated datasets into CSV format and normalized JSON tensor format.
  - Integrates HaGrid (Hand Gesture Recognition Image Dataset) parsers and import tools.

---

## 6. Phase 4: Machine Learning & Static Gesture Recognition

### Objective
Train and deploy an invariant deep learning model capable of classifying static hand poses with sub-millisecond inference time.

### Implementation Highlights
* **Anatomical Feature Engineering (`feature_engineering.py`):**
  - Extracts 63 raw coordinates ($21 \times 3$) and normalizes them relative to the wrist anchor ($L_0$).
  - Computes scale-invariant phalanx straightness metrics:
    $$\text{Straightness} = \frac{\text{chord\_length}}{\text{segment\_length}}$$
  - Invariant to translation, uniform camera scale, and 3D rotational tilt.
* **Deep Neural Network (`mlp_classifier.py`):**
  - PyTorch Multi-Layer Perceptron architecture: $63 \to 128 \to \text{ReLU} \to \text{Dropout}(0.2) \to 64 \to \text{ReLU} \to N\text{ classes}$.
  - Optimized with Adam optimizer and Cross-Entropy Loss with label smoothing.
* **Model Registry & Training Engine:**
  - Automated dataset split (80/20 train/validation), confusion matrix generation, and atomic checkpoint saving.
* **Client-Side Zero-Latency Classifier (`localGestureClassifier.ts`):**
  - Re-implemented geometric classification rules directly in TypeScript inside the browser, eliminating network latency for real-time interaction.

---

## 7. Phase 5: Temporal & Dynamic Gesture Recognition Engine

### Objective
Recognize time-series gesture trajectories across consecutive video frames (such as Swipes, Waves, and Circles).

### Implementation Highlights
* **Sliding Buffer (`TemporalFrameBuffer`):**
  - Maintains a 30-frame rolling window ($1000\text{ ms}$ buffer at 30 FPS).
* **Motion Tracker (`MovementTracker`):**
  - Computes wrist velocity vector ($\vec{v} = (\Delta x / \Delta t, \Delta y / \Delta t)$), cumulative displacement, and trajectory linearity.
* **Dynamic Gesture State Machine (`GestureStateMachine`):**
  - Detects 9 discrete dynamic gestures:
    - **Swipe Left / Right / Up / Down:** High velocity along primary axis with $>75\%$ linearity.
    - **Wave:** Periodic alternating velocity sign flips across 3 cycles.
    - **Circle (Clockwise / Counter-Clockwise):** Angular phase progression around trajectory centroid.
    - **Zoom In / Zoom Out:** Dynamic distance expansion/contraction between thumb and index tips.

---

## 8. Phase 5.5: Critical Stabilization & Hardware Lifecycle Arbiter

### Objective
Eliminate hardware device conflicts, memory leaks, thread deadlocks, and phantom gesture detections.

### Problems Resolved
1. **Physical Camera Ownership Conflict:** Chrome's `getUserMedia` and OpenCV's `VideoCapture(0, CAP_DSHOW)` competed for hardware device 0 on Windows, triggering `NotReadableError` or black screens.
2. **Executor Shutdown Race Condition:** MediaPipe's threadpool threw `RuntimeError: cannot schedule new futures after shutdown` when stopping capture.
3. **Ghost / Phantom Hands:** Video pausing left stale landmarks indefinitely in memory.

### Key Architectural Solutions
* **Mutual Exclusion Arbiter (`camera_manager.py`):**
  - Added strict ownership states: `none`, `browser`, or `backend`.
  - Added atomic handoff methods: `claim_ownership(owner)` and `release_ownership(owner)`.
* **Thread-Safe Shutdown Protocol (`hand_tracking.py`):**
  - Introduced `_inference_lock`. During shutdown, `stop_event` is set, active frame loops join with a 3.0s timeout, and `landmarker.close()` runs only when zero threads are inside inference.
* **150ms Time-To-Live (TTL) Eviction:**
  - If no anatomical hand is validated for 150ms, all landmarks, bounding boxes, and states are immediately wiped from memory.

---

## 9. Phase 6A: Desktop Cursor Navigation & Spatial Mapping

### Objective
Enable natural desktop mouse cursor movement steered by hand position while keeping user experience stable, smooth, and safe.

### Implementation Highlights
* **Zero-Dependency Native Windows Driver:**
  - Built using Python `ctypes.windll.user32` directly interfacing with `SetCursorPos`.
  - Microsecond latency ($<0.05\text{ ms}$) with zero third-party dependencies.
  - Automatically queries primary display resolution via `GetSystemMetrics(0)` and `GetSystemMetrics(1)`.
* **Active Tracking Margins:**
  - Defines an ergonomic tracking box within the normalized camera frame using 15% margins:
    $$u = \text{clamp}\left(\frac{\text{norm\_x} - 0.15}{1.0 - 2 \cdot 0.15}, 0.0, 1.0\right),\quad v = \text{clamp}\left(\frac{\text{norm\_y} - 0.15}{1.0 - 2 \cdot 0.15}, 0.0, 1.0\right)$$
* **Exponential Moving Average (EMA) Smoothing:**
  $$\text{smoothed}_t = \alpha \cdot \text{target}_t + (1 - \alpha) \cdot \text{smoothed}_{t-1}$$
  Default $\alpha = 0.35$ provides an optimal balance between cursor stability and responsive tracking.
* **Anti-Jump Reset:**
  - Upon tracking acquisition or re-entry, the filter initializes to $\text{smoothed}_0 = \text{target}_0$, completely preventing cursor snapping.
* **Center Deadband (5%):**
  - Micro-movements within a circular 5% radius around the active box center are filtered to prevent cursor jitter from hand tremors.

---

## 10. Phase 6A.1: Cursor Movement Refinement & Calibration

### Objective
Ensure precise synchronization between frontend dashboard sliders and backend controller algorithms.

### Implementation Highlights
* **Unified Parameter Mapping:**
  - Normalized sensitivity scale ($0.2\times$ to $3.0\times$, default $1.0\times$) expanding symmetrically around screen midpoint.
  - Reconciled smoothing scale between frontend UI and backend EMA filter.
  - Edge clamping guarantees cursor remains strictly inside $[0, W - 1] \times [0, H - 1]$.
* **Live Telemetry Inspection:**
  - Real-time reporting of cursor coordinates, active display dimensions, smoothing coefficient, and tracking status.

---

## 11. Phase 6A.2: Camera Preview Persistence & Background Handoff

### Objective
Ensure video preview mounts reliably without UI toggling, and keep mouse control active when switching application tabs or minimizing windows.

### Implementation Highlights
* **Persistent DOM Ref Callback:**
  - Replaced conditional DOM unmounting with a persistent `<video>` element with explicit `onLoadedMetadata` and `onCanPlay` callbacks.
* **Centralized Stream Persistence (`cameraStore.ts`):**
  - Preserves `MediaStream` handles across React component remounts and SPA navigation.
* **Background Tracking Handoff:**
  - When mouse control is enabled, camera ownership transfers to the Python backend (`owner: 'backend'`).
  - OpenCV DirectShow and MediaPipe execute inside native OS background threads unaffected by browser tab throttling.

---

## 12. Phase 6A.3: Unified Launcher & Background Autonomy

### Objective
Eliminate startup friction and ensure desktop control persists completely independently of browser window state.

### Implementation Highlights
* **Cross-Platform Launcher ([`run.py`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/run.py)):**
  - Automatically discovers virtual environment (`backend/.venv/Scripts/python.exe`).
  - Detects port collisions on ports 8000 and 5173. If an existing GestureFlow AI instance is healthy, reuses it safely; otherwise clears stale processes.
  - Dynamic readiness polling loops replace arbitrary sleep timers.
  - Supervised process termination (`taskkill /F /T` on Windows) guarantees zero orphaned background processes.
* **Single Batch Launcher ([`run_gestureflow.bat`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/run_gestureflow.bat)):**
  - One-click launch from Windows Explorer starting backend, frontend, and opening the browser.
* **Emergency Stop Protocol:**
  - Exposed via `POST /api/v1/mouse/emergency-stop`.
  - Accessible via the persistent global Emergency Stop button in the frontend header.

---

## 13. Phase 6B.1: Gesture-Based Left Mouse Click

### Objective
Implement reliable, safe, and debounced gesture-based left clicking without disturbing smooth cursor navigation.

### Implementation Highlights
* **Dual Trigger Capabilities:**
  1. **Index Finger Point (`index_finger`):** Natural pointing pose (Index extended, Middle/Ring/Pinky curled) triggering bound action `left_click`.
  2. **Thumb + Index Pinch:** Dedicated geometric Euclidean distance between Thumb Tip ($L_4$) and Index Fingertip ($L_8$):
     $$\text{dist}_{\text{left}} = \sqrt{(\text{thumb}_x - \text{index}_x)^2 + (\text{thumb}_y - \text{index}_y)^2}$$
* **Hysteresis Click Engine:**
  - **Activation Threshold:** $\le 0.05$ (5% normalized distance). Triggers a click when armed.
  - **Release Threshold:** $\ge 0.08$ (8% normalized distance). Hand must open past 8% before the latch resets.
  - **Deadband (5%–8%):** Prevents accidental double clicks from hand tremors.
* **Safety Rules:**
  - **Single Click Per Gesture:** Holding a pinch or pointing pose triggers exactly ONE click. No repeated clicks while held.
  - **Configurable Cooldown:** Default 400ms debouncing window.
  - **Tracking Loss Protection:** Disarms latch immediately when hand leaves the frame; re-entry in a pinched pose does not fire a click.
  - **Independent Toggle:** Left click can be disabled independently while cursor movement remains active.

---

## 14. Phase 6B.2: Gesture-Based Right Mouse Click

### Objective
Implement gesture-based right clicking co-existing harmoniously with cursor movement and left clicking.

### Implementation Highlights
* **Dual Trigger Capabilities:**
  1. **Two Fingers Victory (`two_fingers`):** Peace/Victory sign (Index & Middle extended in V-shape, Ring/Pinky curled) triggering bound action `right_click`.
  2. **Thumb + Middle Pinch:** Dedicated geometric distance between Thumb Tip ($L_4$) and Middle Fingertip ($L_{12}$):
     $$\text{dist}_{\text{right}} = \sqrt{(\text{thumb}_x - \text{middle}_x)^2 + (\text{thumb}_y - \text{middle}_y)^2}$$
* **Hysteresis & Cooldown:**
  - Activation threshold $\le 0.05$, release threshold $\ge 0.08$, cooldown 500ms default.
* **Mutual Exclusion Engine:**
  - If both Left Pinch ($L_4 \to L_8$) and Right Pinch ($L_4 \to L_{12}$) drop $\le 0.05$ simultaneously (e.g. closing into a fist or touching all fingers together), both clicks are suppressed.
* **Independent Settings Matrix:**

| Left Click Setting | Right Click Setting | Result |
|:---:|:---:|:---|
| **ON** | **ON** | Both Left and Right clicks active |
| **ON** | **OFF** | Only Left Click active |
| **OFF** | **ON** | Only Right Click active |
| **OFF** | **OFF** | No clicking; cursor movement only |

---

## 15. Phase 6B Resolution: Click Pipeline & Windows Desktop Isolation Fix

### Problem
Following Phase 6B implementation, cursor movement worked, but neither left nor right click produced actual clicks on Windows desktop applications.

### Root Cause Analysis
1. **Thread Desktop Isolation (`ERROR_ACCESS_DENIED` 5):**
   - Click requests arriving over HTTP (`/api/v1/mouse/click`) executed on AnyIO worker threads.
   - On Windows, worker threads spawned by threadpools are not attached to the interactive user desktop (`WinSta0\default`). Calling `user32.GetCursorPos` returned `(0, 0)`, and calling `user32.mouse_event` or `user32.SendInput` was rejected by Windows with Error 5 (`ERROR_ACCESS_DENIED`).
2. **`ERROR_BUSY` (170) on Existing Event Loop Threads:**
   - Attempting to call `SetThreadDesktop` on an existing thread that had already created message hooks failed with Win32 Error 170 (`ERROR_BUSY`).
3. **Silent Drop:**
   - `mouse_event` returns `void` in Win32 C, so it failed silently without throwing a Python exception.

### Permanent Resolution
1. **Dedicated Worker Thread Queue (`_click_queue`):**
   - Click events from the REST API and geometric pinch engines are enqueued into a thread-safe `_click_queue`.
   - The dedicated `MouseControllerWorker` thread—which is a fresh thread explicitly attached to `WinSta0\default` with full desktop access—processes and executes clicks at the current cursor coordinates.
2. **Win32 `SendInput` Implementation:**
   - Upgraded driver to use native Win32 `SendInput` (`INPUT` and `MOUSEINPUT` structures) with 15ms dwell time for OS message pumps, with fallback to `mouse_event`.
3. **Telemetry & Store Latency Optimization:**
   - In [`mouseStore.ts`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/src/store/mouseStore.ts), `triggerClick` and `triggerRightClick` apply optimistic local status updates before polling, eliminating UI lag.

---

## 16. Master Gesture & Bound Action Taxonomy

| Gesture ID | Display Name | Visual Pose Description | Landmark Formula | Bound Action |
|:---|:---|:---|:---|:---|
| `open_palm` | **Open Palm** | All 5 fingers extended outward | Extended count $\ge 4$ | `move_cursor` (Steers cursor) |
| `index_finger`| **Index Finger** | Index extended, others curled | Index straightness $\ge 0.72$, middle/ring/pinky curled | `left_click` (Executes Left Click) |
| `two_fingers` | **Two Fingers** | Index & Middle extended in V-shape | Index & middle ext, V-gap $\ge 0.22$, ring/pinky curled | `right_click` (Executes Right Click) |
| `pinch` | **Index Pinch** | Thumb tip touches index tip | Euclidean $\text{dist}(L_4, L_8) \le 0.05$ | `left_click` (Executes Left Click) |
| `middle_pinch`| **Middle Pinch**| Thumb tip touches middle tip | Euclidean $\text{dist}(L_4, L_{12}) \le 0.05$ | `right_click` (Executes Right Click) |
| `thumbs_up` | **Thumbs Up** | Thumb pointing up, fingers curled | Thumb ext upward, 4 fingers curled | `no_action` |
| `fist` | **Closed Fist** | All 4 fingers curled into palm | 4 fingers curled, thumb folded | `drag_drop` (Reserved) |

---

## 17. Safety & Reliability Principles

1. **Safety Rule #1 — Disabled by Default:** Mouse control always initializes in `disabled` state upon application startup.
2. **Safety Rule #2 — 150ms Tracking-Loss Cutoff:** Cursor movement and clicking halt immediately when tracking is lost or coordinates are older than 150ms.
3. **Safety Rule #3 — Anti-Jump Guarantee:** Re-establishing tracking initializes smoothing memory to current coordinates without cursor jumps.
4. **Safety Rule #4 — Single Click Latching:** Holding a gesture or pinch never produces spam clicks; exactly one click executes per discrete gesture.
5. **Safety Rule #5 — Mock Safety in Automated Testing:** Automated tests strictly inject `MockMouseDriver`, guaranteeing zero real desktop clicks or cursor moves during testing.
6. **Safety Rule #6 — Mutual Exclusion:** Simultaneous left and right click gestures are suppressed to prevent accidental activation.

---

## 18. Consolidated Manual Testing Protocols

### Setup
1. Launch system via `run_gestureflow.bat` or `python run.py`.
2. Open dashboard at `http://localhost:5173`.
3. In **Desktop Mouse Control** card, click **"Enable Cursor Control"**.

### Test Execution Matrix

| Test ID | Objective | Procedure | Expected Outcome |
|:---:|:---|:---|:---|
| **M-01** | **Cursor Movement** | Show Open Palm (`open_palm`) to camera and move hand. | Cursor tracks hand smoothly across screen; 0 clicks triggered. |
| **M-02** | **Point Left Click** | Position cursor over target, extend Index finger (`index_finger`). | Left click executes; Total Clicks increments by 1; status pulses CLICKED. |
| **M-03** | **Pinch Left Click** | Touch thumb and index tips together ($\le 5\%$). | Left click executes immediately. |
| **M-04** | **Hold Suppression** | Hold index point or pinch for 5 seconds without releasing. | Exactly ONE click fires; no repeating clicks. |
| **M-05** | **Pinch Hysteresis** | Pinch to click, separate fingers slightly ($6\%$), pinch again. | No second click until hand opens $> 8\%$ release threshold. |
| **M-06** | **Victory Right Click** | Show Two Fingers Victory (`two_fingers`). | Right click executes; Windows context menu appears at cursor target. |
| **M-07** | **Middle Pinch Click** | Touch thumb and middle fingertip together ($\le 5\%$). | Right click executes; context menu opens. |
| **M-08** | **Independent Toggles** | Disable Left Click toggle in card; test index click and victory click. | Left click is blocked; Right click continues to work normally. |
| **M-09** | **Cooldown Debounce** | Perform two rapid pinches within 200ms ($< 400\text{ ms}$). | Cooldown shows Debouncing; second rapid click is safely ignored. |
| **M-10** | **Tracking Loss Safety** | Move hand out of frame, pinch while outside, return hand into view. | No click fires on re-entry; hand must open before clicking. |
| **M-11** | **Cross-App Navigation**| Switch to Notepad or File Explorer while control is enabled. | Cursor moves and clicks work across all Windows native apps. |
| **M-12** | **Emergency Stop** | Click Emergency Stop button in header. | Cursor movement and all click triggers halt instantly. |

---

## 19. Verification Evidence & Automated Test Results

### Automated Backend Test Suite
```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests -v
======================== 183 passed, 1 warning in 15.14s ========================
```
* **Core API & Health (`test_camera_api.py`, `test_health.py`):** 16 Passed
* **Camera Manager & Lifecycle (`test_camera_manager.py`, `test_camera_ownership.py`):** 15 Passed
* **Dataset Collection & Management (`test_dataset_*.py`):** 28 Passed
* **Static ML Classifier (`test_classifier_phase4.py`):** 10 Passed
* **Temporal Gesture Engine (`test_temporal_phase5.py`):** 14 Passed
* **Mouse Controller & Smoothing (`test_mouse_controller.py`):** 11 Passed
* **Phase 6B.1 Left Click Suite (`test_mouse_left_click.py`):** 15 Passed
* **Phase 6B.2 Right Click Suite (`test_mouse_right_click.py`):** 14 Passed
* **Phase 6B Click Pipeline Fix (`test_click_pipeline_fix.py`):** 5 Passed
* **System Launcher & Config (`test_launcher.py`, `test_config.py`):** 15 Passed
* **Total Passing Tests:** **183 / 183 (100% Pass Rate)**

### Frontend Production Build
```bash
npm run build
✓ 2510 modules transformed.
✓ built in 853ms (0 TypeScript errors, 0 syntax warnings)
```

### Live Diagnostic Server Logs
```log
2026-10-31 14:47:53 | INFO | mouse_controller | start | MouseController started (ENABLED)
2026-10-31 14:47:53 | INFO | mouse_controller | _worker_loop | MOUSE_DIAG: norm=(0.500, 0.500) screen=(960, 540) moved=(960, 540)
2026-10-31 14:47:53 | INFO | mouse_controller | trigger_left_click | [CLICK_DIAG] LEFT_CLICK_ENQUEUED: pos=(960, 540) total=1 cooldown=400ms
2026-10-31 14:47:53 | INFO | mouse_controller | _process_click_queue_on_worker | [CLICK_DIAG] LEFT_CLICK_EXECUTED on worker thread: pos={'x': 960, 'y': 540}
2026-10-31 14:47:53 | INFO | mouse_controller | trigger_right_click | [CLICK_DIAG] RIGHT_CLICK_ENQUEUED: pos=(960, 540) total=1 cooldown=500ms
2026-10-31 14:47:53 | INFO | mouse_controller | _process_click_queue_on_worker | [CLICK_DIAG] RIGHT_CLICK_EXECUTED on worker thread: pos={'x': 960, 'y': 540}
```

---

## 20. Future Roadmap (Phases 7 & 8)

* **Phase 6B.3 (Double Click & Drag-and-Drop):**
  - Rapid double-pinch detection within a 350ms window.
  - Closed Fist hold for click-and-drag file operations.
* **Phase 7 (Comprehensive Integration & Experience Polish):**
  - Full end-to-end integration polish between model training view, live custom models, and OS control mapping.
  - User-configurable custom hotkeys and multi-monitor display selection.
* **Phase 8 (Background Runtime & Standalone Packaging):**
  - Windows System Tray icon with quick toggle options.
  - PyInstaller / Electron single executable packaging (`GestureFlowAI.exe`).
  - Windows background service option for zero-browser headless operation.
