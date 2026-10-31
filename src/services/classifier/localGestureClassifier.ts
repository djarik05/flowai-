/**
 * Local Real-Time Hand Gesture Classifier.
 *
 * Classifies 21-point MediaPipe hand landmarks in the browser with zero latency.
 * Supports standard static gestures:
 * - Open Palm (all 5 fingers extended)
 * - Fist / Closed Fist (all fingers curled into palm)
 * - Index Finger (Point) (index extended, others curled)
 * - Two Fingers (Victory / Peace Sign) (index & middle extended in V-shape, others curled)
 * - Thumbs Up (thumb extended upward, others curled)
 * - Pinch (index and thumb tips touching together)
 */

import { GestureAction } from '../../types/gesture';
import { useGestureStore } from '../../store/gestureStore';

export interface ClassifiedGestureResult {
  gestureId: string;
  name: string;
  action: GestureAction;
  confidence: number;
  isRecognized: boolean;
  fingerStates: {
    thumb: boolean;
    index: boolean;
    middle: boolean;
    ring: boolean;
    pinky: boolean;
  };
}

/**
 * Resolve configured action for a gesture ID or gesture name from user settings.
 */
function getActionForGesture(id: string, defaultAction: GestureAction): GestureAction {
  try {
    const gestures = useGestureStore.getState().gestures;
    const match = gestures.find(
      (g) => g.id === id || g.name.toLowerCase() === id.toLowerCase()
    );
    if (match && match.action) {
      return match.action as GestureAction;
    }
  } catch {}
  return defaultAction;
}

export function classifyHandLandmarks(
  landmarks: { x: number; y: number; z?: number }[],
  _handedness: string = 'Right'
): ClassifiedGestureResult | null {
  if (!landmarks || landmarks.length !== 21) return null;

  const dist = (i: number, j: number) => {
    const p1 = landmarks[i];
    const p2 = landmarks[j];
    const dz = (p1.z ?? 0) - (p2.z ?? 0);
    return Math.hypot(p1.x - p2.x, p1.y - p2.y, dz * 0.5);
  };

  // Reference palm scale: wrist (0) to middle MCP (9)
  const palmScale = dist(0, 9);
  if (palmScale < 0.02) return null;

  // Palm unit vector u from wrist (0) to middle MCP (9)
  const ux = (landmarks[9].x - landmarks[0].x) / palmScale;
  const uy = (landmarks[9].y - landmarks[0].y) / palmScale;

  // Anatomical phalanx straightness metric (rotation and scale invariant)
  // MCP -> PIP -> DIP -> TIP
  const evaluateFinger = (tip: number, dip: number, pip: number, mcp: number) => {
    const segmentLength = dist(mcp, pip) + dist(pip, dip) + dist(dip, tip);
    const chordLength = dist(mcp, tip);
    const straightness = segmentLength > 0 ? chordLength / segmentLength : 0;

    const dTipWrist = dist(tip, 0);
    const dPipWrist = dist(pip, 0);
    const dMcpWrist = dist(mcp, 0);

    // Finger is extended if it has high straightness and tip is farther from wrist than PIP/MCP
    const isExt = straightness >= 0.72 && dTipWrist > dPipWrist * 1.05 && dTipWrist > dMcpWrist * 1.10;

    // Finger is curled if tip folds toward palm/wrist
    const isCurl = straightness < 0.68 || dTipWrist < dPipWrist * 1.04 || dist(tip, mcp) < dist(pip, mcp) * 1.20;

    return { isExt, isCurl, straightness };
  };

  const index = evaluateFinger(8, 7, 6, 5);
  const middle = evaluateFinger(12, 11, 10, 9);
  const ring = evaluateFinger(16, 15, 14, 13);
  const pinky = evaluateFinger(20, 19, 18, 17);

  // Thumb evaluation: CMC (1), MCP (2), IP (3), TIP (4)
  const thumbTipPinkyMcp = dist(4, 17);
  const thumbMcpPinkyMcp = dist(2, 17);
  const thumbExt = thumbTipPinkyMcp > thumbMcpPinkyMcp * 1.20 && dist(4, 0) > dist(2, 0) * 1.12;
  const thumbCurl = thumbTipPinkyMcp < thumbMcpPinkyMcp * 1.10 || dist(4, 9) < dist(3, 9);

  // Thumbs Up check: Thumb extended outward/upward while all 4 fingers curled
  const thumbTipWrist = dist(4, 0);
  const thumbMcpWrist = dist(2, 0);
  const isThumbUp = thumbExt && thumbTipWrist > thumbMcpWrist * 1.15 && index.isCurl && middle.isCurl && ring.isCurl && pinky.isCurl;

  // Pinch check: Index tip (8) and Thumb tip (4) touching together
  const pinchDist = dist(4, 8) / palmScale;
  const isPinch = pinchDist < 0.24 && !thumbCurl;

  const fingerStates = {
    thumb: thumbExt,
    index: index.isExt,
    middle: middle.isExt,
    ring: ring.isExt,
    pinky: pinky.isExt,
  };

  // 1. Pinch (Index + Thumb)
  if (isPinch && (middle.isExt || ring.isExt || pinky.isExt || (!middle.isCurl && !ring.isCurl))) {
    const conf = Math.min(0.98, Math.max(0.82, 1.0 - pinchDist * 1.2));
    return {
      gestureId: 'pinch',
      name: 'Pinch (Index + Thumb)',
      action: getActionForGesture('pinch', 'left_click'),
      confidence: Number(conf.toFixed(2)),
      isRecognized: true,
      fingerStates,
    };
  }

  // 2. Thumbs Up
  if (isThumbUp) {
    return {
      gestureId: 'thumbs_up',
      name: 'Thumbs Up',
      action: getActionForGesture('thumbs_up', 'no_action'),
      confidence: 0.95,
      isRecognized: true,
      fingerStates,
    };
  }

  // 3. Fist (All 4 fingers curled)
  if (index.isCurl && middle.isCurl && ring.isCurl && pinky.isCurl && !index.isExt && !middle.isExt) {
    return {
      gestureId: 'fist',
      name: 'Fist',
      action: getActionForGesture('fist', 'drag_drop'),
      confidence: 0.96,
      isRecognized: true,
      fingerStates,
    };
  }

  // 4. Open Palm (Checked BEFORE Victory to prevent open hands from falsely triggering Victory)
  // All 4 fingers extended, or 3 fingers extended + thumb extended
  const extCount = [index.isExt, middle.isExt, ring.isExt, pinky.isExt].filter(Boolean).length;
  if ((extCount >= 4) || (extCount >= 3 && thumbExt && (ring.isExt || pinky.isExt))) {
    const conf = Math.min(0.99, 0.85 + extCount * 0.035);
    return {
      gestureId: 'open_palm',
      name: 'Open Palm',
      action: getActionForGesture('open_palm', 'move_cursor'),
      confidence: Number(conf.toFixed(2)),
      isRecognized: true,
      fingerStates,
    };
  }

  // 5. Index Finger (Point) - Index extended, Middle, Ring, Pinky curled
  const indexDominant = dist(8, 0) > dist(12, 0) * 1.10;
  if (index.isExt && (middle.isCurl || indexDominant) && ring.isCurl && pinky.isCurl && !middle.isExt) {
    return {
      gestureId: 'index_finger',
      name: 'Index Finger (Point)',
      action: getActionForGesture('index_finger', 'left_click'),
      confidence: 0.96,
      isRecognized: true,
      fingerStates,
    };
  }

  // 6. Two Fingers (Victory / Peace Sign)
  // Requires:
  // a) Index extended AND Middle extended
  // b) Ring and Pinky curled
  // c) Distinct V-gap separation between Index (8) and Middle (12) tips
  const fingerGap = dist(8, 12) / palmScale;
  if (index.isExt && middle.isExt && ring.isCurl && pinky.isCurl && fingerGap >= 0.22) {
    const conf = Math.min(0.98, 0.88 + fingerGap * 0.15);
    return {
      gestureId: 'two_fingers',
      name: 'Two Fingers (Victory)',
      action: getActionForGesture('two_fingers', 'right_click'),
      confidence: Number(conf.toFixed(2)),
      isRecognized: true,
      fingerStates,
    };
  }

  return null;
}
