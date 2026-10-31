# Phase 6B — Left Click & Right Click Bug Fix Debug Report

**Project**: GestureFlow AI  
**Author**: Antigravity Engineering  
**Date**: October 31, 2026  
**Status**: RESOLVED & VERIFIED  

---

## 1. Executive Summary

During testing of the desktop mouse control system, mouse cursor movement tracked smoothly across the screen, but neither Left Click nor Right Click produced any clicks on the Windows desktop.

This investigation traced both click pipelines end-to-end from the camera frame and landmark extraction through gesture classification, frontend REST dispatch, backend FastAPI controllers, and native Windows User32 OS drivers.

The root cause was identified, verified with diagnostic probes, and resolved by implementing **native Win32 SendInput with dedicated interactive desktop worker queue execution**. All 183 automated tests are passing with zero regressions, and live end-to-end execution of both Left and Right clicks has been verified.

---

## 2. Root Cause Analysis

### Root Cause 1: Windows User32 Thread Desktop Isolation (`ERROR_ACCESS_DENIED` 5 & `ERROR_BUSY` 170)
* **The Failure**:
  - When the frontend triggered `/api/v1/mouse/click` or `/api/v1/mouse/click-right`, FastAPI routed the request onto worker threads in the asyncio/AnyIO thread pool.
  - On Windows, worker threads spawned by services or thread pools default to an unattached desktop context.
  - Calling `user32.GetCursorPos` on an unattached thread returns `(0, 0)` without error.
  - Calling `user32.mouse_event` or `user32.SendInput` on an unattached thread fails with Windows Win32 Error 5 (`ERROR_ACCESS_DENIED`).
  - Attempting to call `SetThreadDesktop` on an existing thread that has already initialized GUI or message loop structures fails with Windows Win32 Error 170 (`ERROR_BUSY`).
  - Because `mouse_event` has a `void` return type in Win32 C, it dropped the click silently without raising a Python exception.

### Root Cause 2: Asynchronous Multi-Thread Input Injection
* **The Failure**:
  - Moving the cursor was handled on a dedicated background worker thread (`MouseControllerWorker`), while clicks arriving via HTTP were executing synchronously on whatever thread received the HTTP request.
  - This caused click attempts to occur on unattached threads with coordinates defaulting to `(0, 0)`.

### Root Cause 3: Frontend Landmark Parameter Forwarding
* **The Failure**:
  - In `CameraSection.tsx`, `feedCursorPoint(feedX, feedY)` was called without forwarding `pinchDist`, `rightPinchDist`, `thumbX`, `thumbY`, `middleX`, `middleY` when in `open_palm` mode.
  - The backend's geometric pinch detector received `None` for all pinch parameters from the web client.

---

## 3. End-to-End Pipeline Trace & Fixes

### Left Click Pipeline
```
Webcam Frame
  ↓
MediaPipe Hand Landmarks (21 points)
  ↓
Local Classifier (`localGestureClassifier.ts`)
  • Index Finger Point: Index extended, Middle/Ring/Pinky curled
  • Index + Thumb Pinch: Euclidean dist(L4, L8) <= 0.05
  ↓
Frontend Safety Latch (`CameraSection.tsx`)
  • Cooldown check (>= 400ms)
  • Single-fire latch (`!hasTriggeredIndexClickRef`)
  • Hysteresis release reset when dist >= 0.08 or gesture changed
  ↓
Zustand Store & API Client (`mouseStore.ts` & `mouse.ts`)
  • Optimistic UI state update (`click_count`, `last_click_time`, `pinched`)
  • HTTP POST `http://127.0.0.1:8000/api/v1/mouse/click`
  ↓
FastAPI Route (`backend/app/api/routes/mouse.py`)
  • `get_mouse_controller().trigger_left_click()`
  ↓
Mouse Controller (`mouse_controller.py`)
  • Verifies `is_enabled` and `left_click_enabled`
  • Validates cooldown window
  • Enqueues action `"left"` into `_click_queue`
  • Signals `_target_event`
  ↓
Dedicated Attached Worker (`MouseControllerWorker`)
  • Fresh dedicated thread attached to `WinSta0\default` via `prepare_thread()`
  • Resolves exact physical screen coordinates `(x, y)`
  • Executes Windows `SendInput(MOUSEEVENTF_LEFTDOWN)`
  • Delivers 15ms dwell time for OS window message pump
  • Executes Windows `SendInput(MOUSEEVENTF_LEFTUP)`
  • Fallback to `mouse_event` if SendInput unavailable
  ↓
Windows OS Left Click Executed at Cursor Target
```

### Right Click Pipeline
```
Webcam Frame
  ↓
MediaPipe Hand Landmarks (21 points)
  ↓
Local Classifier (`localGestureClassifier.ts`)
  • Two Fingers (Victory): Index & Middle extended in V-shape, Ring/Pinky curled
  • Middle + Thumb Pinch: Euclidean dist(L4, L12) <= 0.05
  ↓
Frontend Safety Latch (`CameraSection.tsx`)
  • Cooldown check (>= 500ms)
  • Single-fire latch (`!hasTriggeredVictoryClickRef`)
  • Hysteresis release reset when dist >= 0.08 or gesture changed
  ↓
Zustand Store & API Client (`mouseStore.ts` & `mouse.ts`)
  • Optimistic UI state update (`right_click_count`, `last_right_click_time`)
  • HTTP POST `http://127.0.0.1:8000/api/v1/mouse/click-right`
  ↓
FastAPI Route (`backend/app/api/routes/mouse.py`)
  • `get_mouse_controller().trigger_right_click()`
  ↓
Mouse Controller (`mouse_controller.py`)
  • Verifies `is_enabled` and `right_click_enabled`
  • Validates cooldown window
  • Enqueues action `"right"` into `_click_queue`
  • Signals `_target_event`
  ↓
Dedicated Attached Worker (`MouseControllerWorker`)
  • Resolves physical screen coordinates
  • Executes Windows `SendInput(MOUSEEVENTF_RIGHTDOWN)`
  • Delivers 15ms dwell time
  • Executes Windows `SendInput(MOUSEEVENTF_RIGHTUP)`
  ↓
Windows OS Right Click Context Menu Displayed
```

---

## 4. Key Code Modifications

| File | Nature of Change |
|------|------------------|
| `backend/app/services/mouse_controller.py` | 1. Implemented native Win32 `SendInput` structure (`INPUT`, `MOUSEINPUT`) with fallback to `mouse_event`.<br>2. Added thread-local desktop attachment via `_ensure_attached()` and `prepare_thread()` connecting to `WinSta0\default`.<br>3. Created `_click_queue` to route all OS click execution onto the dedicated `MouseControllerWorker` thread.<br>4. Implemented `_process_click_queue_on_worker()` running continuously with 120 Hz loop.<br>5. Added throttled diagnostic logging (`[CLICK_DIAG]`).<br>6. Added fallback coordinates to `(last_moved_x, last_moved_y)` when querying cursor position from unattached contexts. |
| `src/components/camera/CameraSection.tsx` | 1. Forwarded live `pinchDist`, `rightPinchDist`, `thumbX`, `thumbY`, `middleX`, `middleY` during cursor feeding.<br>2. Implemented strict single-fire hysteresis latches for Index Click and Victory Click.<br>3. Added client-side throttled diagnostic console logs. |
| `src/store/mouseStore.ts` | Optimistic click count and timestamp updates in `triggerClick` and `triggerRightClick` to eliminate UI latency. |
| `backend/tests/test_click_pipeline_fix.py` | Created automated test suite verifying mock safety, queue execution, independent toggling, tracking loss protection, and mutual exclusion. |

---

## 5. Verification Results

### 1. Automated Test Suite
```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
======================== 183 passed, 1 warning in 15.14s ========================
```
- Total tests: 183 passed, 0 failed.
- Left-click test suite (`test_mouse_left_click.py`): 15/15 passed.
- Right-click test suite (`test_mouse_right_click.py`): 14/14 passed.
- Fix regression suite (`test_click_pipeline_fix.py`): 5/5 passed.

### 2. Live HTTP & Worker Verification
```
1. Enable: True
2. Feed Point (0.5, 0.5): {'success': True, 'enabled': True, 'clicked': False}
3. Left Click: {'success': True, 'enabled': True, 'click_count': 1}
4. Right Click: {'success': True, 'enabled': True, 'right_click_count': 1}
5. Cursor pos: {'x': 960, 'y': 540}
6. Last click pos: {'x': 960, 'y': 540}
7. Last right click pos: {'x': 960, 'y': 540}
8. Click counts: Left = 1, Right = 1
```

### 3. Server Diagnostic Log Output
```log
[CLICK_DIAG] LEFT_CLICK_ENQUEUED: pos=(960, 540) total=1 cooldown=400ms
[CLICK_DIAG] LEFT_CLICK_EXECUTED on worker thread: pos={'x': 960, 'y': 540}
[CLICK_DIAG] RIGHT_CLICK_ENQUEUED: pos=(960, 540) total=1 cooldown=500ms
[CLICK_DIAG] RIGHT_CLICK_EXECUTED on worker thread: pos={'x': 960, 'y': 540}
```

---

## 6. Safety Commitments Maintained

1. **Safety Rule #1**: Mouse control remains **Disabled by default** on startup.
2. **Safety Rule #2**: Tracking loss immediately disarms all clickers and halts cursor movement (150ms TTL).
3. **Safety Rule #3**: Clicks are strictly mocked in automated test environments; no live OS clicks occur during test runs.
4. **Safety Rule #4**: Single click per gesture action; holding a pinch or pointing pose does not trigger repeat clicks.
5. **Safety Rule #5**: Independent enable/disable settings for Left and Right clicks.
