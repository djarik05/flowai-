// Phase 6A: Mouse Movement Control Zustand Store

import { create } from 'zustand';
import { MouseStatus, MouseSettingsUpdate } from '../types/mouse';
import { MouseApi } from '../services/api/mouse';
import { useCameraStore } from './cameraStore';

interface MouseStore {
  status: MouseStatus;
  isLoading: boolean;
  error: string | null;
  isBackendConnected: boolean;

  fetchStatus: () => Promise<void>;
  enableMouse: () => Promise<void>;
  disableMouse: () => Promise<void>;
  emergencyStop: () => Promise<void>;
  toggleMouse: () => Promise<void>;
  toggleLeftClick: () => Promise<void>;
  toggleRightClick: () => Promise<void>;
  triggerClick: () => Promise<void>;
  triggerRightClick: () => Promise<void>;
  updateSettings: (settings: MouseSettingsUpdate) => Promise<void>;
  feedCursorPoint: (
    x: number,
    y: number,
    pinchDistance?: number,
    thumbX?: number,
    thumbY?: number,
    rightPinchDistance?: number,
    middleX?: number,
    middleY?: number
  ) => Promise<void>;
}

const DEFAULT_MOUSE_STATUS: MouseStatus = {
  enabled: false,
  state: 'disabled',
  hand_detected: false,
  control_point: null,
  cursor_position: { x: 0, y: 0 },
  screen_size: { width: 1920, height: 1080 },
  sensitivity: 1.0,
  smoothing_alpha: 0.35,
  active_margin_x: 0.15,
  active_margin_y: 0.15,
  dead_zone: 0.05,
  last_error: null,
  left_click_enabled: true,
  pinch_distance: null,
  pinch_state: 'idle',
  pinch_activation_threshold: 0.05,
  pinch_release_threshold: 0.08,
  click_cooldown_ms: 400.0,
  last_click_time: null,
  last_click_position: null,
  click_count: 0,
  right_click_enabled: true,
  right_pinch_distance: null,
  right_pinch_state: 'idle',
  right_pinch_activation_threshold: 0.05,
  right_pinch_release_threshold: 0.08,
  right_click_cooldown_ms: 500.0,
  last_right_click_time: null,
  last_right_click_position: null,
  right_click_count: 0,
};

// Silent audio keep-alive node:
// In Chromium, playing inaudible audio marks the tab as an Active Media Tab,
// preventing the browser process from being frozen or throttled by Windows power management when minimized.
let silentAudioCtx: AudioContext | null = null;

function ensureBackgroundAudio() {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    if (!silentAudioCtx || silentAudioCtx.state === 'closed') {
      silentAudioCtx = new AudioCtx();
      const osc = silentAudioCtx.createOscillator();
      const gain = silentAudioCtx.createGain();
      gain.gain.value = 0.0001; // completely inaudible
      osc.connect(gain);
      gain.connect(silentAudioCtx.destination);
      osc.start();
    }
    if (silentAudioCtx.state === 'suspended') {
      silentAudioCtx.resume().catch(() => {});
    }
  } catch {}
}

function releaseBackgroundAudio() {
  try {
    if (silentAudioCtx && silentAudioCtx.state !== 'closed') {
      silentAudioCtx.close().catch(() => {});
      silentAudioCtx = null;
    }
  } catch {}
}

export const useMouseStore = create<MouseStore>((set, get) => ({
  status: DEFAULT_MOUSE_STATUS,
  isLoading: false,
  error: null,
  isBackendConnected: false,

  fetchStatus: async () => {
    try {
      const status = await MouseApi.getStatus();
      set({ status, error: null, isBackendConnected: true });
    } catch (err: any) {
      const isNetworkErr = err?.message?.includes('fetch') || err?.name === 'TypeError';
      const msg = isNetworkErr
        ? 'FastAPI backend offline (port 8000). Start backend to activate desktop cursor control.'
        : err.message || 'Failed to fetch mouse status';
      set({ error: msg, isBackendConnected: false });
    }
  },

  enableMouse: async () => {
    set({ isLoading: true, error: null });
    try {
      ensureBackgroundAudio();
      const status = await MouseApi.enable();
      set({ status, isLoading: false, error: null, isBackendConnected: true });
    } catch (err: any) {
      const isNetworkErr = err?.message?.includes('fetch') || err?.name === 'TypeError';
      const msg = isNetworkErr
        ? 'FastAPI backend offline (port 8000). Run "run_gestureflow.bat" or "npm run backend" to start the desktop cursor engine.'
        : err.message || 'Failed to enable mouse control';
      set({
        isLoading: false,
        error: msg,
        isBackendConnected: false,
      });
    }
  },

  disableMouse: async () => {
    set({ isLoading: true, error: null });
    try {
      releaseBackgroundAudio();
      const status = await MouseApi.disable();
      set({ status, isLoading: false, error: null, isBackendConnected: true });
    } catch (err: any) {
      const isNetworkErr = err?.message?.includes('fetch') || err?.name === 'TypeError';
      const msg = isNetworkErr
        ? 'FastAPI backend offline (port 8000). Run "run_gestureflow.bat" or "npm run backend" to start the desktop cursor engine.'
        : err.message || 'Failed to disable mouse control';
      set({
        isLoading: false,
        error: msg,
        isBackendConnected: false,
      });
    }
  },

  emergencyStop: async () => {
    set({ isLoading: true, error: null });
    try {
      releaseBackgroundAudio();
      const status = await MouseApi.emergencyStop();
      set({ status, isLoading: false, error: null, isBackendConnected: true });
    } catch (err: any) {
      set((s) => ({
        status: { ...s.status, enabled: false, state: 'disabled' },
        isLoading: false,
        error: err.message || 'Emergency stop applied locally',
      }));
    }
  },

  toggleMouse: async () => {
    const { status, enableMouse, disableMouse } = get();
    if (status.enabled) {
      await disableMouse();
    } else {
      await enableMouse();
    }
  },

  toggleLeftClick: async () => {
    const { status, updateSettings } = get();
    await updateSettings({ left_click_enabled: !status.left_click_enabled });
  },

  toggleRightClick: async () => {
    const { status, updateSettings } = get();
    await updateSettings({ right_click_enabled: !status.right_click_enabled });
  },

  triggerClick: async () => {
    try {
      const res = await MouseApi.triggerClick();
      set((state) => ({
        status: {
          ...state.status,
          click_count: res.click_count ?? (state.status.click_count + 1),
          last_click_time: Date.now() / 1000,
          pinch_state: 'pinched',
        },
      }));
      await get().fetchStatus();
    } catch (err: any) {
      console.error('[mouseStore] Left click error:', err);
    }
  },

  triggerRightClick: async () => {
    try {
      const res = await MouseApi.triggerRightClick();
      set((state) => ({
        status: {
          ...state.status,
          right_click_count: res.right_click_count ?? (state.status.right_click_count + 1),
          last_right_click_time: Date.now() / 1000,
          right_pinch_state: 'pinched',
        },
      }));
      await get().fetchStatus();
    } catch (err: any) {
      console.error('[mouseStore] Right click error:', err);
    }
  },

  updateSettings: async (settingsUpdate: MouseSettingsUpdate) => {
    try {
      const status = await MouseApi.updateSettings(settingsUpdate);
      set({ status, error: null, isBackendConnected: true });
    } catch (err: any) {
      const isNetworkErr = err?.message?.includes('fetch') || err?.name === 'TypeError';
      const msg = isNetworkErr
        ? 'FastAPI backend offline (port 8000). Settings will sync when backend starts.'
        : err.message || 'Failed to update mouse settings';
      // Optimistically update local settings even if backend is temporarily offline
      set((state) => ({
        status: {
          ...state.status,
          ...settingsUpdate,
        },
        error: msg,
        isBackendConnected: false,
      }));
    }
  },

  feedCursorPoint: async (
    x: number,
    y: number,
    pinchDistance?: number,
    thumbX?: number,
    thumbY?: number,
    rightPinchDistance?: number,
    middleX?: number,
    middleY?: number
  ) => {
    const { status, isBackendConnected } = get();
    if (!status.enabled || !isBackendConnected) return;
    await MouseApi.feedCursorPoint(x, y, undefined, pinchDistance, thumbX, thumbY, rightPinchDistance, middleX, middleY);
  },
}));