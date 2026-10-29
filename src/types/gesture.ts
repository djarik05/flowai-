// Gesture type definitions for GestureFlow AI

export type GestureType = 'static' | 'temporal';

export type GestureAction =
  | 'move_cursor'
  | 'left_click'
  | 'right_click'
  | 'double_click'
  | 'scroll_up'
  | 'scroll_down'
  | 'drag_drop'
  | 'next_slide'
  | 'prev_slide'
  | 'play_pause'
  | 'volume_up'
  | 'volume_down'
  | 'custom_shortcut'
  | 'no_action';

export const GESTURE_ACTION_LABELS: Record<GestureAction, string> = {
  move_cursor: 'Move Cursor',
  left_click: 'Left Click',
  right_click: 'Right Click',
  double_click: 'Double Click',
  scroll_up: 'Scroll Up',
  scroll_down: 'Scroll Down',
  drag_drop: 'Drag & Drop',
  next_slide: 'Next Slide',
  prev_slide: 'Previous Slide',
  play_pause: 'Play/Pause',
  volume_up: 'Volume Up',
  volume_down: 'Volume Down',
  custom_shortcut: 'Custom Keyboard Shortcut',
  no_action: 'No Action',
};

export interface GestureDefinition {
  id: string;
  name: string;
  type: GestureType;
  description: string;
  action: GestureAction;
  enabled: boolean;
  confidenceThreshold: number;
  isDefault: boolean;
  icon: string; // Lucide icon name
  customShortcut?: string;
}

export interface DetectedGesture {
  gestureId: string;
  name: string;
  confidence: number;
  timestamp: number;
  action: GestureAction;
}

export interface GestureRecognitionStatus {
  isActive: boolean;
  currentGesture: DetectedGesture | null;
  lastGesture: DetectedGesture | null;
  fps: number;
  handDetected: boolean;
  landmarkCount: number;
}
