# Phase 6A.1 Manual Testing Guide

**Project:** GestureFlow AI  
**Phase:** 6A.1 - Mouse Movement Refinement & Stability Testing  
**Date:** October 30, 2026  

---

## Test Environment Setup

### Prerequisites
1. Backend running: `cd backend && .venv\Scripts\Activate.ps1 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
2. Frontend running: `cd .. && npm run dev` (accessible at http://localhost:5173)
3. Webcam connected and accessible
4. Backend `.env` configured with `HAND_LANDMARKER_MODEL_PATH=models/hand_landmarker.task`

### Test Account
- No authentication required for current testing
- Default settings loaded from `localStorage` (key: `gestureflow_settings_v1`)

---

## Test Cases

### M01: Enable Mouse Control
**Preconditions:**
- Backend running at http://localhost:8000
- Frontend running at http://localhost:5173
- Webcam connected and accessible
- Mouse controller disabled (default state)

**Steps:**
1. Open http://localhost:5173
2. Navigate to "Live Control" tab
3. Verify "Air Mouse Mode" is selected
4. Click the "Enabled" toggle switch in the header bar

**Expected Result:**
- Toggle switches to "Enabled" state
- Badge shows "Active Dispatch" with green indicator
- Backend logs show "MouseController started (ENABLED)"
- Backend mouse controller status API returns `enabled: true`, `state: "waiting_for_hand"`

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M02: Move Cursor Left
**Preconditions:**
- Mouse control enabled (M01 passed)
- Hand visible in camera view
- Index finger extended (pointing gesture)

**Steps:**
1. Position hand in center of camera view
2. Extend index finger (pointing gesture)
3. Slowly move hand to the left
4. Observe cursor movement on screen

**Expected Result:**
- Windows cursor moves left smoothly
- Cursor follows index fingertip movement
- No sudden jumps or excessive lag
- Cursor stays within screen boundaries

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M03: Move Cursor Right
**Preconditions:**
- Mouse control enabled
- Hand visible in camera view
- Index finger extended

**Steps:**
1. Position hand in center of camera view
2. Extend index finger
3. Slowly move hand to the right
4. Observe cursor movement

**Expected Result:**
- Windows cursor moves right smoothly
- Cursor follows index fingertip movement
- No sudden jumps or excessive lag

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M04: Move Cursor Up
**Preconditions:**
- Mouse control enabled
- Hand visible in camera view
- Index finger extended

**Steps:**
1. Position hand in center of camera view
2. Extend index finger
3. Slowly move hand upward
4. Observe cursor movement

**Expected Result:**
- Windows cursor moves up smoothly
- Cursor follows index fingertip movement
- Vertical mapping is correct (hand up = cursor up)

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M05: Move Cursor Down
**Preconditions:**
- Mouse control enabled
- Hand visible in camera view
- Index finger extended

**Steps:**
1. Position hand in center of camera view
2. Extend index finger
3. Slowly move hand downward
3. Observe cursor movement

**Expected Result:**
- Windows cursor moves down smoothly
- Cursor follows index fingertip movement
- Vertical mapping is correct (hand down = cursor down)

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M06: Reach Screen Corners
**Preconditions:**
- Mouse control enabled
- Hand visible in camera view
- Index finger extended

**Steps:**
1. Move hand to top-left of camera view
2. Observe if cursor reaches top-left of screen
3. Move hand to top-right of camera view
3. Observe if cursor reaches top-right of screen
4. Move hand to bottom-left of camera view
4. Observe if cursor reaches bottom-left of screen
5. Move hand to bottom-right of camera view
5. Observe if cursor reaches bottom-right of screen

**Expected Result:**
- Cursor reaches all four screen corners
- No cursor clamping before screen edges
- Active margin (15% default) provides reasonable tracking area
- Cursor clamps at screen boundaries (0,0) to (width-1, height-1)

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M07: Test Cursor Sensitivity
**Preconditions:**
- Mouse control enabled
- Hand visible in camera view
- Live Control Station open with sensitivity slider visible

**Steps:**
1. Set sensitivity to 20% (0.2) via slider
3. Move hand from left to right across camera view
3. Observe cursor travel distance
4. Set sensitivity to 100% (1.0) via slider
4. Move hand from left to right across camera view
4. Observe cursor travel distance
5. Set sensitivity to 200% (2.0) via slider
5. Move hand from left to right across camera view
5. Observe cursor travel distance

**Expected Result:**
- 20% sensitivity: Small cursor movement for large hand movement
- 100% sensitivity: 1:1 mapping (with active margin)
- 200% sensitivity: Large cursor movement for small hand movement
- Changes take effect immediately without restart

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M08: Test Cursor Smoothing
**Preconditions:**
- Mouse control enabled
- Hand visible in camera view
- Movement smoothing slider visible

**Steps:**
1. Set smoothing to 10% (0.1) - minimal smoothing
3. Move hand in small circles
3. Observe cursor jitter/smoothness
4. Set smoothing to 95% (0.95) - maximum smoothing
4. Move hand in small circles
4. Observe cursor smoothness vs lag
5. Set smoothing to 50% (0.5) - default
5. Move hand in small circles
5. Observe balance of smoothness and responsiveness

**Expected Result:**
- Low smoothing (10%): Responsive but jittery cursor
- High smoothing (95%): Very smooth but noticeable lag
- Default (50%): Good balance of smoothness and responsiveness
- No cursor jumps when smoothing changes

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M09: Remove Hand from Camera
**Preconditions:**
- Mouse control enabled
- Hand visible and controlling cursor

**Steps:**
1. Move hand completely out of camera view
3. Observe cursor behavior
3. Wait 2 seconds
3. Check cursor position

**Expected Result:**
- Cursor movement stops within 150ms (tracking timeout)
- Cursor stays at last valid position
- Status changes to "waiting_for_hand"
- `hand_detected` becomes false in status API
- No cursor drift or sudden jumps

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M10: Hide Hand Temporarily
**Preconditions:**
- Mouse control enabled
- Hand visible and controlling cursor

**Steps:**
1. Briefly cover camera with hand/other object (< 100ms)
3. Uncover camera
3. Observe cursor behavior

**Expected Result:**
- Brief occlusion (< 150ms) doesn't trigger tracking loss
- Cursor continues smoothly when hand reappears
- No cursor jump when tracking resumes
- Smoothing state preserved (EMA continues from last valid position)

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M11: Reintroduce Hand
**Preconditions:**
- Mouse control enabled
- Hand was removed from camera (M09 completed)
- Cursor stationary at last position

**Steps:**
1. Bring hand back into camera view
3. Extend index finger
3. Move hand slightly
3. Observe cursor behavior

**Expected Result:**
- Cursor resumes tracking smoothly
- No sudden jump to new position
- Smoothing re-initializes from current cursor position
- Status changes to "active"
- `hand_detected` becomes true

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M12: Disconnect Webcam
**Preconditions:**
- Mouse control enabled
- Hand visible and controlling cursor

**Steps:**
1. Physically unplug webcam USB cable
3. Observe cursor behavior
3. Check backend logs
3. Check frontend status

**Expected Result:**
- Cursor movement stops
- Backend logs camera disconnection error
- Status changes to "error" or "waiting_for_hand"
- No uncontrolled cursor movement
- No crashed threads or memory leaks

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M13: Disable Mouse Control
**Preconditions:**
- Mouse control enabled
- Hand visible and controlling cursor

**Steps:**
1. Click "Enabled" toggle switch in header bar
3. Observe cursor behavior
3. Check backend status API

**Expected Result:**
- Toggle switches to "Disabled"
- Badge shows "Controller Disabled"
- Cursor movement stops immediately
- Backend status returns `enabled: false`, `state: "disabled"`
- Background worker thread stopped
- Smoothing state reset

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M14: Re-enable Mouse Control
**Preconditions:**
- Mouse control disabled (M13 completed)
- Hand visible in camera view

**Steps:**
1. Click "Disabled" toggle switch to enable
3. Observe cursor behavior
3. Check backend status

**Expected Result:**
- Toggle switches to "Enabled"
- Badge shows "Active Dispatch"
- Cursor resumes tracking from current hand position
- No cursor jump on re-enable
- Smoothing re-initializes from current hand position

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M15: Navigate Between Tabs
**Preconditions:**
- Mouse control enabled
- Hand controlling cursor

**Steps:**
1. Click "Gesture Library" tab
3. Wait 2 seconds
3. Click "Dataset Overview" tab
3. Wait 2 seconds
3. Click "Live Control" tab
3. Observe cursor behavior throughout

**Expected Result:**
- Mouse control remains enabled throughout navigation
- Cursor tracking continues uninterrupted
- No camera reinitialization
- No cursor jumps or interruptions
- Settings persist across tab switches

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M16: Refresh Browser
**Preconditions:**
- Mouse control enabled
- Hand controlling cursor

**Steps:**
1. Press F5 or Ctrl+R to refresh browser
3. Wait for page to reload
3. Navigate back to Live Control tab
3. Observe mouse control state

**Expected Result:**
- Mouse control remains disabled after refresh (safety default)
- Settings persist in localStorage
- Must manually re-enable mouse control
- No orphaned backend worker threads
- Backend mouse controller remains in disabled state

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M17: Disconnect Backend
**Preconditions:**
- Mouse control enabled
- Hand controlling cursor

**Steps:**
1. Stop backend server (Ctrl+C in backend terminal)
3. Observe frontend behavior
3. Wait 5 seconds
3. Restart backend
3. Observe reconnection behavior

**Expected Result:**
- Frontend detects backend disconnect
- Mouse control disabled on frontend (safety)
- Cursor movement stops
- No orphaned backend threads
- After restart, manual re-enable required
- No orphaned camera resources

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M18: Reconnect Backend
**Preconditions:**
- Backend was disconnected (M17 completed)
- Backend restarted and running

**Steps:**
1. Verify backend health endpoint responds
3. Refresh frontend page
3. Navigate to Live Control tab
3. Re-enable mouse control
3. Verify cursor tracking works

**Expected Result:**
- Backend health check passes
- Frontend reconnects to backend API
- Mouse control can be re-enabled
- Cursor tracking works as before
- No duplicate controller workers

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M19: Repeat Enable/Disable Cycles
**Preconditions:**
- Backend and frontend running
- Webcam connected

**Steps:**
1. Enable mouse control
3. Wait 2 seconds
3. Disable mouse control
3. Wait 1 second
3. Repeat 10 times

**Expected Result:**
- All 10 cycles complete without errors
- No duplicate controller workers spawned
- No memory leaks (stable memory usage)
- No thread leaks (thread count stable)
- Each enable/disable cycle completes cleanly
- Smoothing state properly reset each cycle

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

### M20: Application Shutdown
**Preconditions:**
- Mouse control enabled
- Hand controlling cursor

**Steps:**
1. Close browser tab/window
3. Stop backend server (Ctrl+C)
3. Check for clean shutdown

**Expected Result:**
- Backend shuts down gracefully
- Camera resources released
- Mouse controller worker thread stopped
- No orphaned threads or processes
- No error messages in logs during shutdown

**Actual Result:** [To be filled during testing]

**PASS / FAIL:** [ ]

**Notes:** [ ]

---

## Automated Test Verification

Run before and after manual testing:

```bash
# Backend tests
cd backend
.venv\Scripts\Activate.ps1
python -m pytest tests -v

# Frontend build
cd ..
npm run build
```

**Expected:** All 136 backend tests pass, frontend build succeeds.

---

## Test Results Summary

| Test ID | Test | Result | Notes |
|---------|------|--------|-------|
| M01 | Enable Mouse Control | [ ] | |
| M02 | Move Cursor Left | [ ] | |
| M03 | Move Cursor Right | [ ] | |
| M04 | Move Cursor Up | [ ] | |
| M05 | Move Cursor Down | [ ] | |
| M06 | Reach Screen Corners | [ ] | |
| M07 | Test Cursor Sensitivity | [ ] | |
| M08 | Test Cursor Smoothing | [ ] | |
| M09 | Remove Hand from Camera | [ ] | |
| M10 | Hide Hand Temporarily | [ ] | |
| M11 | Reintroduce Hand | [ ] | |
| M12 | Disconnect Webcam | [ ] | |
| M13 | Disable Mouse Control | [ ] | |
| M14 | Re-enable Mouse Control | [ ] | |
| M15 | Navigate Between Tabs | [ ] | |
| M16 | Refresh Browser | [ ] | |
| M17 | Disconnect Backend | [ ] | |
| M18 | Reconnect Backend | [ ] | |
| M19 | Repeat Enable/Disable Cycles | [ ] | |
| M20 | Application Shutdown | [ ] | |

---

## Test Environment Info

| Item | Value |
|------|-------|
| OS | [e.g., Windows 11 Pro 23H2] |
| Python | [e.g., 3.12.10] |
| Node.js | [e.g., 20.18.0] |
| Screen Resolution | [e.g., 1920x1080] |
| Webcam | [e.g., Logitech C920] |
| Backend Port | 8000 |
| Frontend Port | 5173 |

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | | | |
| Reviewer | | | |