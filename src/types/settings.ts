// Settings type definitions for GestureFlow AI

export interface GeneralSettings {
  autoLaunch: boolean;
  theme: 'dark' | 'system';
  animationsEnabled: boolean;
  reducedMotion: boolean;
  language: string;
}

export interface CameraSettings {
  deviceId: string;
  resolution: '480p' | '720p' | '1080p';
  frameRate: 15 | 30 | 60;
  mirrorPreview: boolean;
}

export interface RecognitionSettings {
  confidenceThreshold: number;
  predictionSmoothing: number;
  gestureCooldown: number;
  unknownGestureAction: 'ignore' | 'notify' | 'log';
}

export interface ControllerSettings {
  enabled: boolean;
  cursorSensitivity: number;        // Maps to backend sensitivity (0.1-2.0 -> 0.1-5.0)
  movementSmoothing: number;        // Maps to backend smoothing_alpha (inverted: higher = smoother)
  deadZone: number;                 // Maps to backend dead_zone (0.0-0.3)
  scrollSpeed: number;
  dragSensitivity: number;
  clickCooldown: number;
  gestureActivationDelay: number;
}

export interface DragDropSettings {
  enabled: boolean;
  activationGesture: string;
  releaseGesture: string;
  activationDelay: number;
  minHoldDuration: number;
  cursorSmoothing: number;
  dragSensitivity: number;
  accidentalReleasePrevention: boolean;
  safetyStopShortcut: string;
}

export interface BackgroundSettings {
  hideUI: boolean;
  startMinimized: boolean;
  returnShortcut: string;
  emergencyStopShortcut: string;
}

export interface AppSettings {
  general: GeneralSettings;
  camera: CameraSettings;
  recognition: RecognitionSettings;
  controller: ControllerSettings;
  dragDrop: DragDropSettings;
  background: BackgroundSettings;
  version: number;
}

// Conversion helpers for backend API
export function toBackendMouseSettings(frontend: ControllerSettings): {
  sensitivity: number;
  smoothing_alpha: number;
  active_margin_x: number;
  active_margin_y: number;
  dead_zone: number;
  tracking_timeout_ms: number;
} {
  return {
    sensitivity: frontend.cursorSensitivity * 2.0,           // 0.1-2.0 -> 0.2-4.0 (clamped to 0.1-5.0)
    smoothing_alpha: 1.0 - frontend.movementSmoothing,       // 0.1-0.95 -> 0.9-0.05 (inverted)
    active_margin_x: 0.15,                                   // Fixed for now
    active_margin_y: 0.15,                                   // Fixed for now
    dead_zone: frontend.deadZone,                             // 1:1 mapping
    tracking_timeout_ms: 150,                                 // Fixed for now
  };
}

export function fromBackendMouseSettings(backend: {
  sensitivity: number;
  smoothing_alpha: number;
  active_margin_x: number;
  active_margin_y: number;
  dead_zone: number;
  tracking_timeout_ms: number;
}): Partial<ControllerSettings> {
  return {
    cursorSensitivity: Math.max(0.1, Math.min(2.0, backend.sensitivity / 2.0)),
    movementSmoothing: Math.max(0.01, Math.min(0.99, 1.0 - backend.smoothing_alpha)),
    deadZone: Math.max(0.0, Math.min(0.3, backend.dead_zone)),
    // Note: active_margin_x, active_margin_y, tracking_timeout_ms not exposed in frontend yet
  };
}

export const DEFAULT_SETTINGS: AppSettings = {
  general: {
    autoLaunch: false,
    theme: 'dark',
    animationsEnabled: true,
    reducedMotion: false,
    language: 'en',
  },
  camera: {
    deviceId: 'default',
    resolution: '720p',
    frameRate: 30,
    mirrorPreview: true,
  },
  recognition: {
    confidenceThreshold: 0.75,
    predictionSmoothing: 0.5,
    gestureCooldown: 300,
    unknownGestureAction: 'ignore',
  },
  controller: {
    enabled: false,
    cursorSensitivity: 0.5,
    movementSmoothing: 0.6,
    deadZone: 0.05,
    scrollSpeed: 0.5,
    dragSensitivity: 0.5,
    clickCooldown: 500,
    gestureActivationDelay: 200,
  },
  dragDrop: {
    enabled: false,
    activationGesture: 'pinch',
    releaseGesture: 'open_palm',
    activationDelay: 300,
    minHoldDuration: 500,
    cursorSmoothing: 0.7,
    dragSensitivity: 0.5,
    accidentalReleasePrevention: true,
    safetyStopShortcut: 'Escape',
  },
  background: {
    hideUI: false,
    startMinimized: false,
    returnShortcut: 'Ctrl+Shift+G',
    emergencyStopShortcut: 'Ctrl+Shift+X',
  },
  version: 1,
};