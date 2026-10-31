# GestureFlow AI — Phase 6A: Mouse Movement Debug & Verification Report

**Date:** 2026-10-30  
**Status:** Root Causes Diagnosed & Fixed | Automated Verified | Windows OS-Level Verified  

---

## 1. Executive Summary & Root Cause Analysis

When Desktop Mouse Control (Phase 6A) was enabled in the UI:
- The card changed state to `Awaiting Hand`.
- Moving the index finger in front of the camera did not move the Windows desktop cursor.

A rigorous, end-to-end trace of the data pipeline revealed **three distinct root causes**:

### Root Cause 1: Windows Window Station & Desktop Permission Isolation
- **Observed:** Calling `user32.GetCursorPos()` or `user32.SetCursorPos()` returned `False` with error code `5` (`ERROR_ACCESS_DENIED`).
- **Explanation:** When Python runs from terminal, background task, or service sessions on Windows, its thread is created inside the window station `WinSta0`, but its thread desktop may point to a non-interactive desktop session (`exebox-...` or console) rather than the active user desktop (`default`). Without explicitly opening and attaching the thread to the `default` desktop, Windows User32 security blocks cursor control and telemetry calls.

### Root Cause 2: Client-Server Clock Skew & Artificial Staleness Rejection
- **Observed:** In `MouseController._worker_loop`, points were continuously discarded and the state remained locked in `waiting_for_hand`.
- **Explanation:** In `on_landmark_point()`, the controller set `_last_landmark_time = capture_time or time.time()`. The frontend client passed `timestamp: Date.now() / 1000` (browser wall-clock time in seconds). Whenever browser clock skew or HTTP network flight latency caused the client timestamp to lag behind Python's `time.time()` by more than the 150ms TTL threshold, `(now - _last_landmark_time > 0.150)` evaluated to `True`. The worker loop rejected every incoming frame as stale, wiped smoothing state, and refused to move the cursor.

### Root Cause 3: Non-DPI-Aware Display Virtualization
- **Observed:** Display metrics reported `1536 x 864` instead of the physical `1920 x 1080` monitor display.
- **Explanation:** Without explicit Per-Monitor DPI awareness (`SetProcessDpiAwareness(2)`), Windows virtualized cursor positions to a scaled viewport, leading to coordinate clipping and cursor bounds distortion.

---

## 2. Broken Connections in the Data Flow

| Pipeline Stage | Expected Behavior | Actual Behavior Before Fix | Status |
| :--- | :--- | :--- | :--- |
| **Webcam $\rightarrow$ MediaPipe** | Detect 21 landmarks | Detected valid 21 points | ✅ Working |
| **Landmark 8 Extraction** | Extract index tip $(x, y)$ | Extracted accurately from `primaryLms[8]` | ✅ Working |
| **Frontend API Client** | Send $(x, y)$ via HTTP POST | Sent points with client timestamp; socket pool saturation risk | ⚠️ Fixed (in-flight guard added) |
| **FastAPI Route** | Enqueue $(x, y)$ to controller | Handled request with 200 OK | ✅ Working |
| **Controller Timestamping** | Measure frame age | Compared server time with client clock $\rightarrow$ **FALSE STALE REJECTION** | ❌ **Broken $\rightarrow$ Fixed** |
| **Worker Loop $\rightarrow$ Driver** | Call `SetCursorPos(x, y)` | Blocked by Windows User32 (`ERROR_ACCESS_DENIED 5`) | ❌ **Broken $\rightarrow$ Fixed** |
| **OS Windows Cursor** | Move on interactive desktop | Blocked by missing desktop station association | ❌ **Broken $\rightarrow$ Fixed** |

---

## 3. Files Modified

1. [`backend/app/services/mouse_controller.py`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/backend/app/services/mouse_controller.py)
   - Added `prepare_thread()` to `WindowsUser32MouseDriver`: opens `WinSta0\default` interactive desktop and attaches the thread using `SetThreadDesktop()`.
   - Enabled per-monitor DPI awareness via `shcore.SetProcessDpiAwareness(2)` / `user32.SetProcessDPIAware()`.
   - Updated `on_landmark_point()` to always stamp arrival time using server `time.time()`, eliminating client clock skew.
   - Added throttled 1 Hz diagnostic logging (`MOUSE_DIAG`).

2. [`src/services/api/mouse.ts`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/src/services/api/mouse.ts)
   - Added in-flight request lock (`isFeedingInFlight`) to prevent browser socket pool exhaustion and queued request lag.

3. [`src/store/mouseStore.ts`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/src/store/mouseStore.ts)
   - Added `isBackendConnected` tracking and descriptive connection guidance.

4. [`src/features/dashboard/components/MouseControlCard.tsx`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/src/features/dashboard/components/MouseControlCard.tsx)
   - Updated UI to display clean backend offline warnings with retry connection button and dynamic polling backoff.

5. [`run_gestureflow.bat`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/run_gestureflow.bat) & [`package.json`](file:///c:/Users/SONTU%20ZARIKA/Desktop/flowai/package.json)
   - Added one-click startup scripts to run both FastAPI backend and Vite frontend together.

---

## 4. Verification Results

### A. Automated Test Suite (Mock Driver)
- **Command:** `cd backend; .\.venv\Scripts\python.exe -m pytest tests -v`
- **Result:** **136 passed / 136 tests** in 11.33s (100% passing).
- **Targeted Tests:** `tests/test_mouse_controller.py` (8/8 passed).
  - `test_mouse_controller_disabled_by_default` PASSED
  - `test_mouse_controller_start_stop_idempotent` PASSED
  - `test_coordinate_mapping_center` PASSED
  - `test_coordinate_mapping_boundaries_and_clamping` PASSED
  - `test_sensitivity_scaling` PASSED
  - `test_smoothing_calculation_and_jump_prevention` PASSED
  - `test_tracking_loss_and_stale_rejection` PASSED
  - `test_mouse_api_endpoints` PASSED

### B. Frontend Production Build
- **Command:** `npm run build`
- **Result:** PASSED in 872ms, 0 errors, 0 warnings.

### C. Windows OS-Level Native Movement Verification (Direct Hardware Call)
- **Test Procedure:**
  1. Attached test thread to interactive desktop `default` using `SetThreadDesktop(OpenDesktopW('default', ...))`.
  2. Captured starting cursor position: `(670, 618)`.
  3. Displaced cursor by `(+5, +5)`: position moved to `(675, 623)` (`ret = 1`, `err = 0`).
  4. Restored cursor to `(670, 618)`: position restored cleanly to `(670, 618)` (`ret = 1`, `err = 0`).
- **Verdict:** **PASS (Hardware Verified)**.

### D. End-to-End Live Backend Pipeline Verification
- **Test Procedure:**
  1. `POST /api/v1/mouse/enable` $\rightarrow$ `{"enabled": true, "state": "waiting_for_hand", "screen_size": {"width": 1920, "height": 1080}}`.
  2. `POST /api/v1/mouse/cursor-point` with `{"x": 0.5, "y": 0.5}` $\rightarrow$ `{"success": true, "enabled": true}`.
  3. `GET /api/v1/mouse/status` $\rightarrow$ `{"enabled": true, "state": "active", "hand_detected": true, "control_point": {"x": 0.5, "y": 0.5}}`.
  4. Backend log output: `MOUSE_DIAG: norm=(0.500, 0.500) screen=(960, 540) moved=(960, 540)`.
  5. `POST /api/v1/mouse/disable` $\rightarrow$ `{"enabled": false, "state": "disabled"}`.
- **Verdict:** **PASS (Backend Pipeline Verified)**.

---

## 5. Physical Manual Verification Distinction

| Verification Category | Status | Details |
| :--- | :--- | :--- |
| **Automated Mock Tests** | ✅ Verified | 136/136 tests passed without actual cursor displacement. |
| **Windows OS-Level API** | ✅ Verified | `SetThreadDesktop` + `SetCursorPos` executed on physical desktop. |
| **Backend Route Pipeline** | ✅ Verified | Live HTTP requests enable, feed, track, and disable controller. |
| **Physical Webcam Tracking** | 🟡 Pending User Motion | Requires user to point with hand in front of camera in active session. |

---

## 6. How the User Can Verify Right Now

1. Ensure the browser is open at `http://localhost:5173/`.
2. Confirm the **Desktop Mouse Control** card shows `Disabled (Safe)` with no red errors.
3. Click **Enable Cursor Control** $\rightarrow$ card changes to **`Awaiting Hand`**.
4. Hold up your hand facing the camera with your **index finger pointing**.
5. As your index fingertip moves, the physical Windows desktop cursor will smoothly glide across your screen.
