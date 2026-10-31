# Phase 6B.1: Gesture-Based Left Click — Manual Testing Guide

**Document Version:** 1.0.0  
**Target Milestone:** Phase 6B.1 (Left Mouse Click)  
**Date:** 2026-10-31  

This manual testing guide provides end-to-end verification procedures for Phase 6B.1 gesture-based left mouse clicking in GestureFlow AI. Test cases cover functional accuracy, hysteresis mechanics, debouncing, safety protections, and background operation.

---

## Pre-requisites & Setup

1. **Start Application Services:**
   ```bash
   python run.py
   ```
   Or start services independently:
   - Backend: `http://127.0.0.1:8000`
   - Frontend: `http://localhost:5173`
2. **Camera Initialization:**
   - Verify camera preview is active in the Dashboard viewport.
   - Hand landmarks (neon green joints and bone connections) should appear when placing hand in view.
3. **Cursor Control Activation:**
   - Click **Enable Cursor Control** in the Desktop Mouse Control panel.
   - Status badge transitions to **Active & Tracking**.

---

## Test Execution Matrix

| Test ID | Test Scenario | Steps & Verification | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-6B-01** | **Left-Click Enable / Disable Toggle** | 1. In Desktop Mouse Control, locate the **Gesture Left Click** section.<br>2. Click the **Enabled/Disabled** button.<br>3. Verify backend telemetry updates. | Toggle switches between green **Enabled** and red **Disabled**. When disabled, pinch actions produce 0 clicks while cursor movement remains functional. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-02** | **Pinch Activation (Index + Thumb)** | 1. Bring hand into view.<br>2. Move index finger (Landmark 8) to target a desktop icon or button.<br>3. Bring thumb tip (Landmark 4) to touch index fingertip (distance ≤ 5%). | Left mouse click triggers immediately at the current cursor position. The UI displays **CLICK TRIGGERED** and updates the **Last Click Event** coordinates and count. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-03** | **Pinch Release & Hysteresis** | 1. After pinch activation, keep fingers slightly touching or within 6% distance.<br>2. Slowly open fingers past 8% distance. | No secondary click fires while fingers remain in the 5%–8% hysteresis deadband. Once distance exceeds 8%, the pinch state returns to **IDLE (Awaiting Pinch)**. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-04** | **One Click Per Pinch (Hold Protection)** | 1. Pinch index finger and thumb together.<br>2. Hold the pinch tightly for 3–5 seconds without releasing. | Strictly **one click** occurs. The cursor can be moved or held, but no repeated or rapid-fire clicks occur while pinch is maintained. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-05** | **Cooldown Debouncing (400ms)** | 1. Pinch and release rapidly multiple times in under 300ms.<br>2. Observe the **Cooldown Status** telemetry. | Clicks occurring within the 400ms cooldown window are safely debounced. The UI displays **Cooldown Active (Debouncing...)** until the timer expires. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-06** | **Repeated Pinch Actions** | 1. Perform 5 distinct pinch-release cycles with ~0.5s pause between each.<br>2. Target a counter, browser tab, or test button. | Exactly 5 distinct left clicks are registered. The **Total clicks** counter increments from $N$ to $N+5$. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-07** | **Tracking Loss Protection** | 1. While hovering over a desktop icon, quickly pull hand out of camera frame.<br>2. Observe system behavior. | Cursor halts immediately within 150ms. No phantom or accidental click is triggered. Telemetry displays **NO (Stopped)**. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-08** | **Re-entry Pinched Hand Safety** | 1. Move hand out of camera view.<br>2. Pinch index and thumb together *outside* the camera view.<br>3. Bring pinched hand back into camera view. | The system acquires hand tracking but **does not click** on entry. Hand must be opened past the release threshold (≥ 8%) before a new click can be armed. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-09** | **Camera Disconnect Protection** | 1. With mouse control and left click active, click **Turn Off** on the webcam.<br>2. Try performing pinch gestures in front of the lens. | Webcam hardware tracks are released. Mouse control transitions safely to disabled/standby. Zero clicks are executed. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-10** | **Mouse Control Disable Protection** | 1. Click **Disable Cursor Control**.<br>2. Move hand and pinch index and thumb. | Cursor does not move, and left click does not fire. All OS interactions are safely locked. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-11** | **Browser Tab Switching (In-App)** | 1. With cursor control and left click enabled, navigate to **Settings** or **Activity Logs** tab.<br>2. Perform pinch gesture. | Background heartbeat maintains tracking. Click triggers accurately without stopping or dropping connection. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |
| **TC-6B-12** | **Minimized Window & Background Operation** | 1. Minimize the browser window to the Windows Taskbar.<br>2. Move your hand to move the Windows desktop cursor.<br>3. Pinch index finger and thumb over a desktop shortcut or taskbar icon. | Windows desktop cursor moves accurately and left click opens/activates the targeted item while the browser remains completely minimized. | [ ] PASS<br>[ ] FAIL<br>[ ] NOT TESTED |

---

## Tester Sign-Off

- **Tester Name:** ___________________________
- **Date Tested:** ___________________________
- **Environment:** Windows 10/11 x64, Chromium Browser (Chrome/Edge), 720p/1080p Webcam
- **Overall Result:** [ ] PASS  [ ] FAIL
