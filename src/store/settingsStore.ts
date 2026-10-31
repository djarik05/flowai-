import { create } from 'zustand';
import {
  AppSettings,
  DEFAULT_SETTINGS,
  GeneralSettings,
  CameraSettings,
  RecognitionSettings,
  ControllerSettings,
  DragDropSettings,
  BackgroundSettings,
  toBackendMouseSettings,
  fromBackendMouseSettings,
} from '../types/settings';
import { DatasetApi } from '../services/api/dataset';
import { MouseApi } from '../services/api/mouse';

const SETTINGS_STORAGE_KEY = 'gestureflow_settings_v1';

interface SettingsStore {
  // Settings
  settings: AppSettings;
  updateGeneral: (updates: Partial<GeneralSettings>) => void;
  updateCamera: (updates: Partial<CameraSettings>) => void;
  updateRecognition: (updates: Partial<RecognitionSettings>) => void;
  updateController: (updates: Partial<ControllerSettings>) => void;
  updateDragDrop: (updates: Partial<DragDropSettings>) => void;
  updateBackground: (updates: Partial<BackgroundSettings>) => void;
  resetAll: () => void;

  // Backend sync for mouse controller settings
  syncMouseSettingsToBackend: () => Promise<void>;
  syncMouseSettingsFromBackend: () => Promise<void>;
}

const loadPersistedSettings = (): AppSettings => {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw);
    if (parsed && parsed.version === DEFAULT_SETTINGS.version) {
      return {
        ...DEFAULT_SETTINGS,
        ...parsed,
        general: { ...DEFAULT_SETTINGS.general, ...parsed.general },
        camera: { ...DEFAULT_SETTINGS.camera, ...parsed.camera },
        recognition: { ...DEFAULT_SETTINGS.recognition, ...parsed.recognition },
        controller: { ...DEFAULT_SETTINGS.controller, ...parsed.controller },
        dragDrop: { ...DEFAULT_SETTINGS.dragDrop, ...parsed.dragDrop },
        background: { ...DEFAULT_SETTINGS.background, ...parsed.background },
      };
    }
  } catch (e) {
    console.warn('Failed to parse settings from storage, using defaults', e);
  }
  return DEFAULT_SETTINGS;
};

const saveSettings = (settings: AppSettings) => {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch (e) {
    console.error('Failed to save settings to localStorage', e);
  }
};

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  settings: loadPersistedSettings(),

  updateGeneral: (updates) => {
    const newSettings = {
      ...get().settings,
      general: { ...get().settings.general, ...updates },
    };
    saveSettings(newSettings);
    set({ settings: newSettings });
  },

  updateCamera: (updates) => {
    const newSettings = {
      ...get().settings,
      camera: { ...get().settings.camera, ...updates },
    };
    saveSettings(newSettings);
    set({ settings: newSettings });
  },

  updateRecognition: (updates) => {
    const newSettings = {
      ...get().settings,
      recognition: { ...get().settings.recognition, ...updates },
    };
    saveSettings(newSettings);
    set({ settings: newSettings });
  },

  updateController: (updates) => {
    const newSettings = {
      ...get().settings,
      controller: { ...get().settings.controller, ...updates },
    };
    saveSettings(newSettings);
    set({ settings: newSettings });

    // Sync to backend if controller is enabled
    if (get().settings.controller.enabled) {
      get().syncMouseSettingsToBackend().catch(console.warn);
    }
  },

  updateDragDrop: (updates) => {
    const newSettings = {
      ...get().settings,
      dragDrop: { ...get().settings.dragDrop, ...updates },
    };
    saveSettings(newSettings);
    set({ settings: newSettings });
  },

  updateBackground: (updates) => {
    const newSettings = {
      ...get().settings,
      background: { ...get().settings.background, ...updates },
    };
    saveSettings(newSettings);
    set({ settings: newSettings });
  },

  resetAll: () => {
    saveSettings(DEFAULT_SETTINGS);
    set({ settings: DEFAULT_SETTINGS });
  },

  syncMouseSettingsToBackend: async () => {
    const controller = get().settings.controller;
    try {
      const { MouseApi } = await import('../services/api/mouse');
      const backendSettings = {
        sensitivity: controller.cursorSensitivity * 2.0,
        smoothing_alpha: 1.0 - controller.movementSmoothing,
        active_margin_x: 0.15,
        active_margin_y: 0.15,
        dead_zone: controller.deadZone,
        tracking_timeout_ms: 150,
      };
      await MouseApi.updateSettings(backendSettings);
    } catch (err) {
      console.warn('Failed to sync mouse settings to backend:', err);
    }
  },

  syncMouseSettingsFromBackend: async () => {
    try {
      const { MouseApi } = await import('../services/api/mouse');
      const status = await MouseApi.getStatus();
      const updates = {
        cursorSensitivity: status.sensitivity / 2.0,
        movementSmoothing: 1.0 - status.smoothing_alpha,
        deadZone: status.dead_zone,
      };
      set((state) => ({
        settings: {
          ...state.settings,
          controller: { ...state.settings.controller, ...updates },
        },
      }));
    } catch (err) {
      console.warn('Failed to sync mouse settings from backend:', err);
    }
  },
}));