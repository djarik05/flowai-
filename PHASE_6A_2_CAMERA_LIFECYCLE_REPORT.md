# GestureFlow AI — Phase 6A.2 Camera Lifecycle & Background Mouse Control Report

**Generated:** 2026-10-30  
**Phase:** 6A.2 (Camera Preview, Persistent Tracking & Background Mouse Control)  
**Status:** Verification & Stabilization Complete  

---

## 1. Executive Summary

Phase 6A.2 resolves two critical operational anomalies in GestureFlow AI:
1. **Camera Preview Mount Race Condition (Bug 1):** Video preview was failing to render upon first initialization and required toggling camera devices or options to appear.
2. **Background Mouse Control Throttling (Bug 2):** When navigating away from the dashboard tab or minimizing the browser window, browser-based hand tracking and mouse control halted due to OS/browser resource throttling.
3. **Demo Cycle / Recognition Override:** The simulated gesture loop was previously enabled by default, causing the UI to show simulated gestures (such as "Two Fingers (Victory) 86%") instead of real user gestures detected by the camera.

---

## 2. Technical Root Cause Analysis

### Bug 1: Initial Camera Preview Blank Screen
- **Root Cause:** In earlier versions of `CameraSection.tsx`, the `<video>` element was conditionally mounted based on `{isCameraActive ? <video ref={videoRef} /> : <CameraPlaceholder />}`. When `startWebcam()` executed, `isCameraActive` was initially `false`, leaving `<video>` unmounted in the DOM. Consequently, `videoRef.current` was `null` during stream acquisition, and assigning `video.srcObject = stream` was skipped. When a user subsequently switched camera devices, `isCameraActive` was already `true`, mounting the video element and finally attaching the stream.
- **Permanent Solution:** Replaced conditional unmounting with a persistent ref callback `attachStreamToVideo` and dedicated React synchronization effects. The `<video>` element is permanently available in the DOM structure with explicit `onLoadedMetadata` and `onCanPlay` callbacks that invoke `video.play()` as soon as frames are ready. Furthermore, camera stream state was centralized in `cameraStore.ts` with module-level `persistentMediaStream` persistence across component remounts.

### Bug 2: Background Mouse Control Interruption
- **Root Cause:** Modern web browsers (Chromium, Firefox, Safari) enforce aggressive power-saving and background throttling policies. When a tab is switched or the browser is minimized, `requestAnimationFrame` and `requestVideoFrameCallback` are throttled down to 0–1 Hz or suspended entirely. If desktop mouse control relies on client-side JavaScript frame extraction, minimizing the window instantly halts cursor movement.
- **Permanent Solution:** Implemented an architectural handoff model. When Desktop Mouse Control is enabled, hardware camera ownership is transferred to the Python FastAPI backend (`owner: 'backend'`). OpenCV and MediaPipe run in native OS background threads independent of browser window visibility. Landmark 8 (index fingertip) is continuously routed to `MouseController` using native Windows `user32.SetCursorPos`, ensuring 100% background persistence.

---

## 3. Camera Ownership Architecture Matrix

| State / Owner | Physical Camera Master | Capture Mechanism | MediaPipe Runner | Target Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **`none`** | Released | Inactive | Inactive | App idle, camera turned off |
| **`browser`** | Chrome / Edge | HTML5 `getUserMedia` | WebAssembly / WebGL | Local low-latency preview, dataset recording studio, zero-backend mode |
| **`backend`** | FastAPI / OpenCV | `cv2.VideoCapture` (DirectShow) | Python MediaPipe Tasks API | Background desktop mouse control, temporal recognition engine, tab-independent control |

### Coordinated Handoff Protocol
On Windows, physical USB webcams are exclusive single-client hardware devices. Attempting simultaneous capture from browser `getUserMedia` and backend OpenCV DirectShow causes hardware lockups. GestureFlow AI enforces coordinated handoff:
1. **Browser to Backend (Enable Mouse):** Frontend invokes `pauseWebcamForBackend()`, stopping all browser video tracks. Backend then claims `owner: 'backend'` and initializes OpenCV capture.
2. **Backend to Browser (Disable Mouse):** Frontend invokes `/api/v1/mouse/disable`. Backend stops `MouseController` and `HandTrackingService`, releases ownership (`owner: 'none'`), and frontend safely re-acquires the webcam via `getUserMedia`.

---

## 4. End-to-End Data Flow Diagram

```mermaid
flowchart TD
    subgraph Hardware ["Hardware Layer"]
        CAM["Physical Webcam Device"]
        SCREEN["Primary Windows Display (1920x1080)"]
    end

    subgraph BackendEngine ["FastAPI Backend (Background Native Process)"]
        CM["CameraManager (OpenCV DirectShow)"]
        HT["HandTrackingService (MediaPipe Python)"]
        MC["MouseController (Worker Thread @ 120Hz)"]
        WIN32["Windows user32.SetCursorPos"]
    end

    subgraph BrowserUI ["React Frontend (User Interface)"]
        CSTORE["cameraStore.ts (State & Stream Persistence)"]
        MSTORE["mouseStore.ts (Control & Telemetry)"]
        DASH["DashboardView / MouseControlCard"]
    end

    CAM -->|Exclusive Ownership| CM
    CM -->|Raw BGR Frames (640x480 @ 30 FPS)| HT
    HT -->|Landmark 8: Index Fingertip (x, y)| MC
    MC -->|Active Tracking Box Normalization| MC
    MC -->|EMA Smoothing (alpha=0.35)| MC
    MC -->|Clamped Screen Coordinates| WIN32
    WIN32 -->|Native OS Hook| SCREEN

    MC -.->|Status Polling (400ms)| MSTORE
    MSTORE -.->|UI Telemetry & Controls| DASH
```

---

## 5. Verification Matrix

| Area | Component | Verification Level | Result |
| :--- | :--- | :--- | :--- |
| Camera Preview | `CameraSection.tsx` ref callback | Automated & Manual | Verified (Video attaches immediately on initial power on) |
| SPA Tab Switching | `cameraStore.ts` persistent stream | Automated & Manual | Verified (Navigating tabs retains active camera stream) |
| Camera Ownership | `/api/v1/camera/claim`, `/owner` | Automated Test Suite | Verified (`test_camera_ownership.py` 4/4 passed) |
| Mouse Controller | `backend/app/services/mouse_controller.py` | Automated Test Suite | Verified (`test_mouse_controller.py` 11/11 passed) |
| Backend Pytest | Entire backend test suite | Automated CI Execution | **139 / 139 passed (100%)** |
| Frontend Build | TypeScript & Vite bundling | Production Build | **Passed (0 errors in 876ms)** |
| Static Classifier | `src/services/classifier/localGestureClassifier.ts` | Refined Invariant Metric | Verified (Phalanx straightness metric prevents false Victory) |
| Demo Override | `src/store/appStore.ts` (`isDemoCycling: false`) | Architectural Audit | Verified (Real camera gestures no longer overwritten) |
