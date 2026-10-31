import { create } from 'zustand';
import { GestureDefinition } from '../types/gesture';
import { SAMPLE_GESTURES } from '../services/demo/sampleData';
import { GesturesApi } from '../services/api/gestures';

const GESTURES_STORAGE_KEY = 'gestureflow_gestures_v2';

interface GestureStore {
  gestures: GestureDefinition[];
  isLoading: boolean;
  error: string | null;
  fetchGestures: () => Promise<void>;
  addGesture: (gesture: {
    id?: string;
    name: string;
    type: 'static' | 'temporal';
    description: string;
    action: string;
    confidenceThreshold: number;
    icon?: string;
    customShortcut?: string;
  }) => Promise<GestureDefinition | null>;
  updateGesture: (
    id: string,
    updates: Partial<GestureDefinition>
  ) => Promise<boolean>;
  toggleGestureEnabled: (id: string) => void;
  deleteGesture: (id: string) => Promise<boolean>;
  resetToDefaults: () => void;
}

const loadPersistedGestures = (): GestureDefinition[] => {
  try {
    const raw = localStorage.getItem(GESTURES_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((g: GestureDefinition) => {
          if (g.id === 'open_palm') return { ...g, action: 'move_cursor' as any };
          if (g.id === 'index_finger') return { ...g, action: 'left_click' as any };
          if (g.id === 'two_fingers') return { ...g, action: 'right_click' as any };
          return g;
        });
      }
    }
  } catch (e) {
    console.warn('Failed to parse gestures from storage, using defaults', e);
  }
  return [...SAMPLE_GESTURES];
};

const saveGestures = (gestures: GestureDefinition[]) => {
  try {
    localStorage.setItem(GESTURES_STORAGE_KEY, JSON.stringify(gestures));
  } catch (e) {
    console.error('Failed to save gestures to localStorage', e);
  }
};

export const useGestureStore = create<GestureStore>((set, get) => ({
  gestures: loadPersistedGestures(),
  isLoading: false,
  error: null,

  fetchGestures: async () => {
    set({ isLoading: true, error: null });
    try {
      const backendGestures = await GesturesApi.listGestures();
      if (backendGestures && backendGestures.length > 0) {
        saveGestures(backendGestures);
        set({ gestures: backendGestures, isLoading: false });
        return;
      }
    } catch (err: any) {
      // Backend not running or offline: keep local
      console.warn('Could not sync gestures with backend (using local):', err?.message);
    }
    set({ isLoading: false });
  },

  addGesture: async (gestureData) => {
    try {
      // Attempt to save to backend first
      const created = await GesturesApi.createGesture({
        id: gestureData.id,
        name: gestureData.name,
        description: gestureData.description,
        type: gestureData.type,
        action: gestureData.action,
        confidence_threshold: gestureData.confidenceThreshold,
        icon: gestureData.icon || 'Sparkles',
        custom_shortcut: gestureData.customShortcut,
      });

      const updated = [...get().gestures, created];
      saveGestures(updated);
      set({ gestures: updated });
      return created;
    } catch (err: any) {
      console.warn('Backend create failed, fallback to local creation:', err);
      // Fallback local creation
      const localGesture: GestureDefinition = {
        id: gestureData.id || `G${String(get().gestures.length + 1).padStart(3, '0')}`,
        name: gestureData.name,
        type: gestureData.type,
        description: gestureData.description,
        action: gestureData.action as any,
        confidenceThreshold: gestureData.confidenceThreshold,
        enabled: true,
        isDefault: false,
        icon: gestureData.icon || 'Sparkles',
        customShortcut: gestureData.customShortcut,
        sampleCount: 0,
        sample_count: 0,
      };
      const updated = [...get().gestures, localGesture];
      saveGestures(updated);
      set({ gestures: updated });
      return localGesture;
    }
  },

  updateGesture: async (id, updates) => {
    try {
      await GesturesApi.updateGesture(id, {
        name: updates.name,
        description: updates.description,
        type: updates.type,
        action: updates.action,
        confidence_threshold: updates.confidenceThreshold,
        icon: updates.icon,
        custom_shortcut: updates.customShortcut,
      });
    } catch (err) {
      console.warn('Backend update failed, updating locally only:', err);
    }

    const updated = get().gestures.map((g) => (g.id === id ? { ...g, ...updates } : g));
    saveGestures(updated);
    set({ gestures: updated });
    return true;
  },

  toggleGestureEnabled: (id) => {
    const updated = get().gestures.map((g) => (g.id === id ? { ...g, enabled: !g.enabled } : g));
    saveGestures(updated);
    set({ gestures: updated });
  },

  deleteGesture: async (id) => {
    try {
      await GesturesApi.deleteGesture(id);
    } catch (err) {
      console.warn('Backend delete error (deleting locally):', err);
    }

    const updated = get().gestures.filter((g) => g.id !== id);
    saveGestures(updated);
    set({ gestures: updated });
    return true;
  },

  resetToDefaults: () => {
    saveGestures(SAMPLE_GESTURES);
    set({ gestures: [...SAMPLE_GESTURES] });
  },
}));
