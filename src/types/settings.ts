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
  cursorSensitivity: number;
  movementSmoothing: number;
  deadZone: number;
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
