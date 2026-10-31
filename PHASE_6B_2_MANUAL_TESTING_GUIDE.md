# GestureFlow AI — Phase 6B.2: Gesture-Based Right Click Manual Testing Guide

## 1. Overview & Objective

Phase 6B.2 introduces **Gesture-Based Right Mouse Clicking** using **Thumb Tip (Landmark 4) + Middle Fingertip (Landmark 12)** pinch detection.
This runs alongside the existing:
- Cursor Movement (Index Fingertip, Landmark 8)
- Phase 6B.1 Left Click (Thumb Tip, Landmark 4 + Index Fingertip, Landmark 8)
- Background Mouse Control & Tab Persistence

---

## 2. Default Configuration & Telemetry

| Parameter | Default Value | Recommended Range | Description |
|---|---|---|---|
| **Right Click Enabled** | `true` | `true` / `false` | Independent toggle for middle-finger right click |
| **Right Pinch Activation Threshold** | `0.05` (5%) | `0.02` - `0.12` | Distance between L4 & L12 required to trigger right click |
| **Right Pinch Release Threshold** | `0.08` (8%) | `0.04` - `0.20` | Distance required to disarm hysteresis latch |
| **Right Click Cooldown** | `500.0 ms` | `150 ms` - `1000 ms` | Minimum delay between successive right clicks |

---

## 3. Step-by-Step Verification Procedures

### Test 1: Desktop Mouse Control Card Initial State
1. Open the application at [http://localhost:5173/](http://localhost:5173/).
2. Confirm the **Desktop Mouse Control** card shows:
   - Status badge: `Disabled (Safe)`
   - Main Button: `Enable Cursor Control`
   - **Gesture Left Click** panel: Toggle `Enabled`, activation gesture `Thumb + Index Pinch`
   - **Gesture Right Click** panel: Toggle `Enabled`, activation gesture `Thumb + Middle Pinch`
   - No offline warning banners.

### Test 2: Enable Cursor Control & Camera Preview
1. Click **Enable Cursor Control**.
2. The status badge transitions to `Awaiting Hand`.
3. Start the camera preview.
4. Bring your hand into the camera view. Status updates to `Active & Tracking`.

### Test 3: Right Click Activation via Middle Finger Pinch
1. Move your hand to position the Windows cursor over an empty desktop area or file.
2. Keep your index finger extended (cursor movement point).
3. Bring your **middle fingertip** to touch your **thumb tip** (Landmark 4 to Landmark 12).
4. **Expected Result:**
   - A native Windows right-click context menu opens immediately.
   - Right Click Total Clicks counter increments by 1.
   - Right Pinch Status shows `RIGHT CLICK TRIGGERED`.

### Test 4: Hold-Protection (No Rapid Repeated Right Clicks)
1. Pinch thumb and middle fingertip together and hold the pinch closed for 3 seconds.
2. **Expected Result:**
   - Exactly ONE right click is executed.
   - The context menu remains open; no spam or repeated clicking occurs while holding.

### Test 5: Hysteresis & Release Verification
1. Open your middle finger slightly (e.g. to ~6% distance, between activation 5% and release 8%).
2. Attempt to pinch again without fully opening.
3. **Expected Result:** No right click triggers because the release threshold (8%) was not cleared.
4. Fully separate thumb and middle finger past 8%.
5. Pinch together again.
6. **Expected Result:** A second right click triggers cleanly.

### Test 6: Mutual Exclusion (Fist / All Fingers Closed Protection)
1. Close your whole hand into a fist (or bring thumb, index, and middle fingers together simultaneously).
2. **Expected Result:**
   - NEITHER left click NOR right click triggers.
   - Both latches engage safely to prevent accidental commands.
3. Open hand and pinch ONLY thumb + middle finger.
4. **Expected Result:** Right click fires as intended.

### Test 7: Independent Left & Right Click Toggles
1. In the **Gesture Left Click** panel, click **Enabled** to toggle it to `Disabled`.
2. Perform index finger pinch (L4 + L8). **Expected Result:** No left click occurs.
3. Perform middle finger pinch (L4 + L12). **Expected Result:** Right click triggers normally.
4. Re-enable Left Click and disable Right Click.
5. Perform middle finger pinch. **Expected Result:** No right click occurs.
6. Perform index finger pinch. **Expected Result:** Left click triggers normally.
