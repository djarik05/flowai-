import { create } from 'zustand';
import { GestureDefinition } from '../types/gesture';
import { SAMPLE_GESTURES } from '../services/demo/sampleData';

const GESTURES_STORAGE_KEY = 'gestureflow_gestures_v1';

interface GestureStore {
  gestures: GestureDefinition[];
  addGesture: (gesture: Omit<GestureDefinition, 'id' | 'isDefault'>) => void;
  updateGesture: (id: string, updates: Partial<GestureDefinition>) => void;
  toggleGestureEnabled: (id: string) => void;
  deleteGesture: (id: string) => void;
  resetToDefaults: () => void;
}

const loadPersistedGestures = (): GestureDefinition[] => {
  try {
    const raw = localStorage.getItem(GESTURES_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
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

  addGesture: (gestureData) => {
    const newGesture: GestureDefinition = {
      ...gestureData,
      id: `custom_${Date.now()}`,
      isDefault: false,
    };
    const updated = [...get().gestures, newGesture];
    saveGestures(updated);
    set({ gestures: updated });
  },

  updateGesture: (id, updates) => {
    const updated = get().gestures.map((g) => (g.id === id ? { ...g, ...updates } : g));
    saveGestures(updated);
    set({ gestures: updated });
  },

  toggleGestureEnabled: (id) => {
    const updated = get().gestures.map((g) => (g.id === id ? { ...g, enabled: !g.enabled } : g));
    saveGestures(updated);
    set({ gestures: updated });
  },

  deleteGesture: (id) => {
    const target = get().gestures.find((g) => g.id === id);
    if (target?.isDefault) {
      console.warn('Cannot delete a default system gesture');
      return;
    }
    const updated = get().gestures.filter((g) => g.id !== id);
    saveGestures(updated);
    set({ gestures: updated });
  },

  resetToDefaults: () => {
    saveGestures(SAMPLE_GESTURES);
    set({ gestures: [...SAMPLE_GESTURES] });
  },
}));
