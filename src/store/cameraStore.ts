// Persistent Camera & Tracking Lifecycle Store (Phase 6A.2)
// Ensures camera preview and tracking survive SPA tab transitions and browser minimize events.

import { create } from 'zustand';
import { API_BASE_URL } from '../services/api/client';
import { useAppStore } from './appStore';

export interface CameraDeviceOption {
  deviceId: string;
  label: string;
  index: number;
}

export interface CameraTelemetry {
  cameraFps: number;
  inferenceFps: number;
  avgInferenceMs: number;
  endToEndLatencyMs: number;
  droppedFrames: number;
  resolution: string;
}

// Module-level persistent MediaStream reference
// Survives React component unmounting during SPA tab transitions
let persistentMediaStream: MediaStream | null = null;

export const getPersistentMediaStream = (): MediaStream | null => persistentMediaStream;

export const setPersistentMediaStream = (stream: MediaStream | null): void => {
  if (persistentMediaStream && persistentMediaStream !== stream) {
    try {
      persistentMediaStream.getTracks().forEach((track) => track.stop());
    } catch {}
  }
  persistentMediaStream = stream;
};

interface CameraStore {
  // Operational state
  isCameraActive: boolean;
  isStarting: boolean;
  streamSource: 'webcam' | 'backend';
  cameraOwner: 'none' | 'browser' | 'backend';
  cameraError: string | null;
  backendAvailable: boolean | null;

  // Device & resolution settings
  availableDevices: CameraDeviceOption[];
  selectedDeviceId: string;
  selectedResolution: '640x480' | '320x240' | '1280x720';
  cameraResolution: { width: number; height: number };
  backendCameraIndex: number;
  backendDevices: { index: number; name: string }[];

  // Display toggles
  isMirrored: boolean;
  showOverlays: boolean;

  // Real-time metrics
  detectedHandsCount: number;
  telemetry: CameraTelemetry;

  // Methods
  startWebcam: (deviceId?: string, resolution?: '640x480' | '320x240' | '1280x720') => Promise<MediaStream | null>;
  stopWebcam: () => Promise<void>;
  pauseWebcamForBackend: () => void;
  setStreamSource: (source: 'webcam' | 'backend') => Promise<void>;
  refreshDevices: () => Promise<void>;
  syncOwnershipFromBackend: () => Promise<void>;
  setIsMirrored: (mirrored: boolean) => void;
  setShowOverlays: (show: boolean) => void;
  setSelectedDeviceId: (id: string) => void;
  setSelectedResolution: (res: '640x480' | '320x240' | '1280x720') => void;
  setBackendCameraIndex: (idx: number) => void;
  setDetectedHandsCount: (count: number) => void;
  setTelemetry: (update: Partial<CameraTelemetry>) => void;
  setCameraError: (err: string | null) => void;
}

export const useCameraStore = create<CameraStore>((set, get) => ({
  isCameraActive: false,
  isStarting: false,
  streamSource: 'webcam',
  cameraOwner: 'none',
  cameraError: null,
  backendAvailable: null,

  availableDevices: [],
  selectedDeviceId: '',
  selectedResolution: '640x480',
  cameraResolution: { width: 640, height: 480 },
  backendCameraIndex: 0,
  backendDevices: [],

  isMirrored: true,
  showOverlays: true,

  detectedHandsCount: 0,
  telemetry: {
    cameraFps: 30.0,
    inferenceFps: 0.0,
    avgInferenceMs: 0.0,
    endToEndLatencyMs: 0.0,
    droppedFrames: 0,
    resolution: '640x480',
  },

  refreshDevices: async () => {
    // 1. Fetch discovered backend devices from Python backend
    let backendDevs: { index: number; name: string }[] = [];
    try {
      const res = await fetch(`${API_BASE_URL}/camera/devices`);
      if (res.ok) {
        const data = await res.json();
        if (data && Array.isArray(data.devices)) {
          backendDevs = data.devices.map((d: any) => ({
            index: d.index,
            name: d.name || `Camera ${d.index} (Name unavailable)`,
          }));
          set({ backendDevices: backendDevs });
        }
      }
    } catch {}

    // 2. Query browser device enumeration and merge device friendly names
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = devices.filter((d) => d.kind === 'videoinput');
      const options: CameraDeviceOption[] = videoInputs.map((d, i) => {
        const backendMatch = backendDevs[i]?.name;
        const rawLabel = d.label?.trim();
        const displayLabel = rawLabel || backendMatch || `Camera ${i} (Name unavailable)`;
        return {
          deviceId: d.deviceId,
          label: displayLabel,
          index: i,
        };
      });
      set({ availableDevices: options });
      if (options.length > 0 && !get().selectedDeviceId) {
        set({ selectedDeviceId: options[0].deviceId });
      }
    } catch (e) {
      console.warn('Could not enumerate browser cameras:', e);
    }
  },

  syncOwnershipFromBackend: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/camera/owner`);
      if (res.ok) {
        const data = await res.json();
        set({ cameraOwner: data.owner || 'none', backendAvailable: true });
      } else {
        set({ backendAvailable: false });
      }
    } catch {
      set({ backendAvailable: false });
    }
  },

  startWebcam: async (deviceIdToUse, resolutionToUse) => {
    set({ isStarting: true, cameraError: null });

    const targetId = deviceIdToUse || get().selectedDeviceId;
    const resStr = resolutionToUse || get().selectedResolution;
    const [targetW, targetH] = resStr.split('x').map(Number);

    // Stop existing stream first if switching
    if (persistentMediaStream) {
      persistentMediaStream.getTracks().forEach((track) => track.stop());
      setPersistentMediaStream(null);
    }

    // Coordinated ownership claim: inform backend that browser claims physical hardware
    try {
      await fetch(`${API_BASE_URL}/camera/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner: 'browser' }),
      });
      set({ cameraOwner: 'browser' });
    } catch {
      // Backend offline: proceed with browser standalone
    }

    let stream: MediaStream | null = null;
    let lastErr: any = null;

    // Strategy 1: Exact target constraints
    try {
      const constraints: MediaStreamConstraints = targetId
        ? {
            video: {
              deviceId: { exact: targetId },
              width: { ideal: targetW },
              height: { ideal: targetH },
              frameRate: { ideal: 30 },
            },
            audio: false,
          }
        : {
            video: {
              width: { ideal: targetW },
              height: { ideal: targetH },
              frameRate: { ideal: 30 },
            },
            audio: false,
          };
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch (err1: any) {
      lastErr = err1;
      // Strategy 2: Ideal target constraints
      try {
        const constraints: MediaStreamConstraints = targetId
          ? {
              video: {
                deviceId: { ideal: targetId },
                width: { ideal: targetW },
                height: { ideal: targetH },
              },
              audio: false,
            }
          : {
              video: {
                width: { ideal: targetW },
                height: { ideal: targetH },
              },
              audio: false,
            };
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err2: any) {
        lastErr = err2;
        // Strategy 3: Fallback basic video
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        } catch (err3: any) {
          lastErr = err3;
        }
      }
    }

    if (stream) {
      setPersistentMediaStream(stream);

      // Refresh labels after permission grant
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoInputs = devices.filter((d) => d.kind === 'videoinput');
        const options = videoInputs.map((d, i) => ({
          deviceId: d.deviceId,
          label: d.label || `Camera ${i + 1}`,
          index: i,
        }));
        set({ availableDevices: options });

        const track = stream.getVideoTracks()[0];
        if (track) {
          const settings = track.getSettings();
          if (settings.deviceId) {
            set({ selectedDeviceId: settings.deviceId });
          }
          if (settings.width && settings.height) {
            set({ cameraResolution: { width: settings.width, height: settings.height } });
          }
        }
      } catch {}

      set({
        isCameraActive: true,
        isStarting: false,
        streamSource: 'webcam',
        cameraError: null,
      });
      return stream;
    } else {
      setPersistentMediaStream(null);
      set({
        isCameraActive: false,
        isStarting: false,
        cameraError:
          lastErr?.name === 'NotAllowedError'
            ? 'Camera permission denied. Please allow camera permissions in your browser address bar.'
            : lastErr?.name === 'NotReadableError'
            ? 'Webcam is currently in use by another application. Please close other camera apps and retry.'
            : lastErr?.name === 'OverconstrainedError'
            ? 'Selected camera does not support requested settings. Try selecting another camera.'
            : 'Could not connect to webcam. Please select another camera option.',
      });
      return null;
    }
  },

  pauseWebcamForBackend: () => {
    if (persistentMediaStream) {
      persistentMediaStream.getTracks().forEach((track) => track.stop());
      setPersistentMediaStream(null);
    }
  },

  stopWebcam: async () => {
    if (persistentMediaStream) {
      persistentMediaStream.getTracks().forEach((track) => track.stop());
      setPersistentMediaStream(null);
    }

    set({
      isCameraActive: false,
      isStarting: false,
      detectedHandsCount: 0,
      cameraOwner: 'none',
    });

    // Clear gesture recognition status in appStore
    try {
      useAppStore.getState().setDetectedGesture(null);
      useAppStore.getState().setHandDetected(false);
      useAppStore.getState().setRecognitionState('no_hand');
    } catch {}

    // Scenario D: Auto-disable mouse control when camera is turned off
    try {
      import('./mouseStore').then((m) => {
        const mouseState = m.useMouseStore.getState();
        if (mouseState.status.enabled) {
          mouseState.disableMouse();
        }
      }).catch(() => {});
    } catch {}

    try {
      await fetch(`${API_BASE_URL}/camera/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner: 'browser' }),
        keepalive: true,
      });
    } catch {}
  },

  setStreamSource: async (source) => {
    const current = get().streamSource;
    if (current === source) return;

    if (source === 'backend') {
      // Pause browser camera hardware so backend OpenCV can claim device
      get().pauseWebcamForBackend();
      set({ streamSource: 'backend', isCameraActive: true });
    } else {
      // Return to browser webcam
      set({ streamSource: 'webcam' });
      await get().startWebcam(get().selectedDeviceId);
    }
  },

  setIsMirrored: (isMirrored) => set({ isMirrored }),
  setShowOverlays: (showOverlays) => set({ showOverlays }),
  setSelectedDeviceId: (selectedDeviceId) => set({ selectedDeviceId }),
  setSelectedResolution: (selectedResolution) => set({ selectedResolution }),
  setBackendCameraIndex: (backendCameraIndex) => set({ backendCameraIndex }),
  setDetectedHandsCount: (detectedHandsCount) => set({ detectedHandsCount }),
  setTelemetry: (update) => set((s) => ({ telemetry: { ...s.telemetry, ...update } })),
  setCameraError: (cameraError) => set({ cameraError }),
}));
