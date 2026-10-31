# GestureFlow AI — Phase 6A.2 Manual Testing Guide

**Date:** 2026-10-30  
**Phase:** 6A.2 (Camera Lifecycle, Preview, and Background Mouse Control)  
**Execution Environment:** Windows 10/11 x64, Python 3.12, Node.js v20+

---

## 1. Test Suite C01 – C16

| Test ID | Test Name | Preconditions | Exact Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C01** | First Camera Launch Preview | App started, camera off | Click **Start Camera** button on dashboard | Webcam powers on; video preview renders immediately without touching options | PASS |
| **C02** | Camera Toggle Off / On | Camera currently active | 1. Click **Turn Off**.<br>2. Wait 1 second.<br>3. Click **Start Camera** | Camera shuts down cleanly on Turn Off, re-attaches and displays live preview on Start Camera | PASS |
| **C03** | SPA Tab Switching Persistence | Camera active on Dashboard | 1. Click **Settings** in left sidebar.<br>2. Click **Activity Logs**.<br>3. Return to **Dashboard** | Stream is not terminated; video preview remains continuous with no re-prompting | PASS |
| **C04** | Gesture Manager Remount | Camera active on Dashboard | 1. Click **Gesture Studio** in sidebar.<br>2. Return to **Dashboard** | Camera stream remains active; landmarks continue tracking without restart | PASS |
| **C05** | Mirror Toggle Reflection | Camera active on Dashboard | 1. Click **Mirror** toggle button.<br>2. Raise right hand | Video flips horizontally; moving right hand moves visual overlay right | PASS |
| **C06** | Real Hand Detection (Open Palm) | Camera active | Extend all 5 fingers flat towards camera | "Open Palm" displayed with high confidence (>90%); no false "Two Fingers" classification | PASS |
| **C07** | Real Hand Detection (Point) | Camera active | Extend index finger, curl other 4 fingers | "Index Finger (Point)" displayed with high confidence; action displays MOVE CURSOR | PASS |
| **C08** | Real Hand Detection (Peace / Victory) | Camera active | Extend index & middle fingers with distinct V-gap | "Two Fingers (Victory)" displayed with high confidence; action displays RIGHT CLICK | PASS |
| **C09** | Closed Fist Detection | Camera active | Curl all 4 fingers tightly into palm | "Fist" displayed with high confidence; action displays DRAG DROP | PASS |
| **C10** | Zero Hand Clean State | Camera active | Remove hands completely from camera frame | "Searching for hand..." displayed with 0% confidence; no frozen gesture names | PASS |
| **C11** | Mouse Control Activation | Backend running on port 8000 | Click **Enable Cursor Control** | Status switches to "Awaiting Hand"; hardware ownership claimed by backend | PASS |
| **C12** | Desktop Cursor Tracking | Mouse Control enabled | Show index finger and move across frame | Primary Windows OS desktop cursor moves smoothly in accordance with index fingertip | PASS |
| **C13** | Background Browser Minimize | Mouse Control enabled | Minimize browser window or press Win+D | Cursor movement continues responding to index finger in real time from the desktop | PASS |
| **C14** | Browser Tab Switching Control | Mouse Control enabled | Switch to another browser tab (e.g. Google) | Cursor control remains fully responsive on the desktop without interruption | PASS |
| **C15** | Tracking Loss Safety (150ms TTL) | Mouse Control enabled | Move index finger, then suddenly drop hand out of camera view | Cursor immediately halts in place; zero cursor jump or drift | PASS |
| **C16** | Clean Mouse Control Disable | Mouse Control active | Click **Disable Cursor Control** | Status transitions to "Disabled (Safe)"; backend releases camera ownership cleanly | PASS |

---

## 2. Launch Instructions

To launch the complete GestureFlow AI environment:

1. **Start Backend (Terminal 1):**
   ```cmd
   cd backend
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Start Frontend (Terminal 2):**
   ```cmd
   npm run dev
   ```

3. **Or run the one-click batch launcher:**
   ```cmd
   run_gestureflow.bat
   ```
