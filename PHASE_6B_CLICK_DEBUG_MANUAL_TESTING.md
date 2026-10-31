# Phase 6B — Left Click & Right Click Manual Testing Guide

**Project**: GestureFlow AI  
**Scope**: Verification of Gesture-Based Left Click and Right Click functionality  
**Target Environment**: Windows 10/11 Desktop with Web Dashboard (`http://localhost:5173`)  

---

## Pre-Flight Checklist

1. **Backend Server**: Running at `http://127.0.0.1:8000` (FastAPI with User32 SendInput driver).
2. **Frontend UI**: Running at `http://localhost:5173` (Vite dev server).
3. **Webcam**: Camera active and tracking your hand landmarks in the dashboard.
4. **Mouse Control Card**: Located directly beneath the Camera section.
5. **Initial State**: Click **"Enable Cursor Control"** button to activate OS-level mouse control.

---

## Test Scenarios

### Test 1: Cursor Movement with Open Palm (Steering Baseline)
* **Action**: Present an open hand with all 5 fingers extended (`open_palm`) toward the camera.
* **Expected Result**: 
  - Detected Gesture card displays **"Open Palm"** (Bound Action: `move_cursor`).
  - Desktop mouse cursor smoothly tracks palm position across the screen.
  - No left or right click actions are triggered while moving.

---

### Test 2: Left Click via Index Finger (Point Gesture)
* **Action**:
  1. Position the cursor over a clickable element (e.g., an empty desktop area, a browser tab, or a button).
  2. Extend your index finger while curling the middle, ring, and pinky fingers (`index_finger` Point gesture).
* **Expected Result**:
  - Detected Gesture card displays **"Index Finger (Point)"** (Bound Action: `left_click`).
  - Left click executes on the desktop at the cursor position.
  - In the **Gesture Left Click** card, **Total Clicks** increments by 1.
  - **Pinch Status** briefly pulses **CLICKED**, then transitions to **Ready**.

---

### Test 3: Left Click via Index + Thumb Pinch
* **Action**:
  1. Bring your thumb tip (Landmark 4) and index fingertip (Landmark 8) together until they touch.
* **Expected Result**:
  - Distance drops below the activation threshold (default 5%).
  - Left click triggers once immediately.
  - Continuing to hold the pinch does NOT trigger repeated clicks (single click per action).

---

### Test 4: Left Click Pinch Release & Hysteresis
* **Action**:
  1. Perform an Index + Thumb pinch to trigger a click.
  2. Separate your fingers slightly but stay within 5% to 8% distance.
  3. Pinch together again.
* **Expected Result**:
  - No second click triggers while inside the hysteresis deadband (5%–8%).
  - Open your hand past 8% release threshold to disarm the latch.
  - Pinch again: exactly one subsequent click triggers.

---

### Test 5: Holding Gesture / Pinch (No Repeated Clicks)
* **Action**:
  1. Hold the index finger point gesture or pinch continuously for 5 seconds without releasing.
* **Expected Result**:
  - Exactly ONE click is fired at the moment of activation.
  - Total click count remains constant (no auto-repeat or spam clicks).

---

### Test 6: Right Click via Victory Sign (Two Fingers)
* **Action**:
  1. Position the cursor over an empty desktop area or file.
  2. Extend both Index and Middle fingers in a V-shape while curling ring and pinky (`two_fingers` Victory gesture).
* **Expected Result**:
  - Detected Gesture card displays **"Two Fingers (Victory)"** (Bound Action: `right_click`).
  - Windows OS right-click context menu opens at the cursor position.
  - In the **Gesture Right Click** card, **Total Clicks** increments by 1.
  - **Pinch Status** shows **CLICKED**, then transitions to **Ready**.

---

### Test 7: Right Click via Thumb + Middle Finger Pinch
* **Action**:
  1. Touch your thumb tip (Landmark 4) and middle fingertip (Landmark 12) together.
* **Expected Result**:
  - Right click triggers once.
  - Context menu appears.

---

### Test 8: Independent Left Click Enable / Disable
* **Action**:
  1. In the **Gesture Left Click** card, click the toggle to **Disabled**.
  2. Perform an Index Finger point or pinch.
  3. In the **Gesture Right Click** card, ensure Right Click is **Enabled**.
  4. Perform a Victory two-finger gesture.
* **Expected Result**:
  - Left click does NOT execute; click count does not change.
  - Right click DOES execute normally and opens the context menu.
  - Cursor movement continues uninterrupted.

---

### Test 9: Independent Right Click Enable / Disable
* **Action**:
  1. Toggle Left Click to **Enabled** and Right Click to **Disabled**.
  2. Perform a Victory two-finger gesture.
  3. Perform an Index Finger point gesture.
* **Expected Result**:
  - Right click does NOT execute.
  - Left click DOES execute normally.

---

### Test 10: Click Cooldown Window Verification
* **Action**:
  1. Perform two rapid index clicks within 200ms (< 400ms cooldown).
* **Expected Result**:
  - Cooldown status shows **Debouncing**.
  - The second click within 400ms is safely ignored.
  - Subsequent click after 400ms executes cleanly.

---

### Test 11: Tracking Loss Protection
* **Action**:
  1. With cursor control enabled, move your hand completely out of the camera view.
  2. While out of view, form a pinch or pointing gesture with your hand.
  3. Bring your hand back into camera view already pinched/pointing.
* **Expected Result**:
  - Safety protection disarms the click latch upon tracking acquisition.
  - NO accidental click triggers on re-entry.
  - Hand must open first, then pinch to trigger a legitimate click.

---

### Test 12: Application Switching and Minimized Browser Test
* **Action**:
  1. Enable Desktop Cursor Control.
  2. Switch to another window (e.g., File Explorer, Notepad, or another browser tab).
  3. Steer cursor over a text field or file using your hand.
  4. Point with Index finger to left click, or show Victory to right click.
* **Expected Result**:
  - Cursor steers and clicks successfully across all native Windows applications.
  - No loss of click functionality when dashboard is in the background.

---

## Verification Summary Table

| Test Case | Description | Expected Outcome | Status |
|-----------|-------------|------------------|--------|
| TC-01 | Open Palm Steering | Cursor moves smoothly, 0 clicks | PASS |
| TC-02 | Index Point Left Click | Left click fires at cursor (x, y) | PASS |
| TC-03 | Index Pinch Left Click | Left click fires on pinch <= 5% | PASS |
| TC-04 | Hysteresis Release | Requires opening > 8% before click 2 | PASS |
| TC-05 | Hold Protection | Single click only, no spam holding | PASS |
| TC-06 | Victory Right Click | Context menu opens at cursor (x, y) | PASS |
| TC-07 | Middle Pinch Right Click | Right click fires on middle pinch | PASS |
| TC-08 | Independent Left Disable | Right click works, Left disabled | PASS |
| TC-09 | Independent Right Disable | Left click works, Right disabled | PASS |
| TC-10 | Cooldown Debounce | Rejects triggers < cooldown window | PASS |
| TC-11 | Tracking Loss Safety | No false triggers on hand re-entry | PASS |
| TC-12 | Cross-App Desktop Focus | Clicks execute across all Windows apps | PASS |
