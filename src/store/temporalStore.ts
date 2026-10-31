// Zustand store for Phase 5 Temporal Gesture Recognition & Live Kinematics
import { create } from 'zustand';
import { TemporalApi } from '../services/api/temporal';
import {
  MovementTelemetry,
  TemporalEngineStatusResponse,
  TemporalGestureDefinition,
  TemporalGestureEvent,
} from '../types/temporal';

interface TemporalState {
  engineStatus: TemporalEngineStatusResponse | null;
  gestures: TemporalGestureDefinition[];
  recentEvents: TemporalGestureEvent[];
  latestEvent: TemporalGestureEvent | null;
  rightTelemetry: MovementTelemetry | null;
  leftTelemetry: MovementTelemetry | null;
  isPolling: boolean;
  pollIntervalId: number | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchStatus: () => Promise<void>;
  fetchGestures: () => Promise<void>;
  fetchEvents: () => Promise<void>;
  resetEngine: () => Promise<void>;
  startPolling: (intervalMs?: number) => void;
  stopPolling: () => void;
  clearError: () => void;
}

export const useTemporalStore = create<TemporalState>((set, get) => ({
  engineStatus: null,
  gestures: [],
  recentEvents: [],
  latestEvent: null,
  rightTelemetry: null,
  leftTelemetry: null,
  isPolling: false,
  pollIntervalId: null,
  isLoading: false,
  error: null,

  fetchStatus: async () => {
    try {
      const status = await TemporalApi.getStatus();
      const rightTelem = status.movement_telemetry['Right'] || null;
      const leftTelem = status.movement_telemetry['Left'] || null;
      const latestEvt = status.recent_events && status.recent_events.length > 0
        ? status.recent_events[status.recent_events.length - 1]
        : get().latestEvent;

      set({
        engineStatus: status,
        recentEvents: status.recent_events || [],
        latestEvent: latestEvt,
        rightTelemetry: rightTelem,
        leftTelemetry: leftTelem,
      });
    } catch (err: any) {
      // ignore transient network errors during rapid polling
    }
  },

  fetchGestures: async () => {
    set({ isLoading: true });
    try {
      const list = await TemporalApi.getGestures();
      set({ gestures: list, isLoading: false });
    } catch (err: any) {
      set({ isLoading: false, error: `Failed to load dynamic gestures: ${err.message || err}` });
    }
  },

  fetchEvents: async () => {
    try {
      const events = await TemporalApi.getEvents(20);
      set({
        recentEvents: events,
        latestEvent: events.length > 0 ? events[events.length - 1] : get().latestEvent,
      });
    } catch {
      // ignore
    }
  },

  resetEngine: async () => {
    try {
      await TemporalApi.resetEngine();
      await get().fetchStatus();
    } catch (err: any) {
      set({ error: `Failed to reset temporal engine: ${err.message || err}` });
    }
  },

  startPolling: (intervalMs: number = 250) => {
    const { pollIntervalId } = get();
    if (pollIntervalId) return;

    get().fetchGestures();
    get().fetchStatus();

    const interval = window.setInterval(() => {
      get().fetchStatus();
    }, intervalMs);

    set({ isPolling: true, pollIntervalId: interval });
  },

  stopPolling: () => {
    const { pollIntervalId } = get();
    if (pollIntervalId) {
      window.clearInterval(pollIntervalId);
      set({ isPolling: false, pollIntervalId: null });
    }
  },

  clearError: () => set({ error: null }),
}));
