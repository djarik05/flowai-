import { create } from 'zustand';
import {
  DatasetStats,
  DatasetSampleSummary,
  DatasetSample,
  ValidationReport,
  CollectionStatus,
  CollectionState,
} from '../types/dataset';
import { DatasetApi } from '../services/api/dataset';

interface DatasetStore {
  // Stats
  stats: DatasetStats | null;
  isLoadingStats: boolean;
  fetchStats: () => Promise<void>;

  // Samples
  samples: DatasetSampleSummary[];
  samplesTotal: number;
  samplesLimit: number;
  samplesOffset: number;
  selectedGestureFilter: string | null;
  selectedSessionFilter: string | null;
  isLoadingSamples: boolean;
  fetchSamples: (options?: {
    gesture_id?: string;
    session_id?: string;
    limit?: number;
    offset?: number;
  }) => Promise<void>;

  // Inspection
  selectedSample: DatasetSample | null;
  isLoadingSampleDetail: boolean;
  inspectSample: (sampleId: string) => Promise<void>;
  clearInspectedSample: () => void;

  // Deletion
  deleteSample: (sampleId: string) => Promise<boolean>;
  deleteSession: (sessionId: string) => Promise<boolean>;

  // Validation
  validationReport: ValidationReport | null;
  isValidating: boolean;
  runValidation: () => Promise<void>;

  // Live Collection State
  collectionStatus: CollectionStatus;
  isPollingCollection: boolean;
  startCollection: (gestureId: string, targetSamples: number, sampleIntervalMs?: number) => Promise<void>;
  pauseCollection: () => Promise<void>;
  resumeCollection: () => Promise<void>;
  stopCollection: () => Promise<void>;
  pollCollectionStatus: () => Promise<CollectionStatus | null>;
  setCollectionStatus: (status: CollectionStatus) => void;
}

const DEFAULT_COLLECTION_STATUS: CollectionStatus = {
  state: 'idle',
  status: 'idle',
  session_id: null,
  gesture_id: null,
  gesture_name: null,
  target_samples: 50,
  collected_samples: 0,
  progress_pct: 0,
  progress_percent: 0,
  hand_detected: false,
  handedness: 'Unknown',
  fps: 0,
  last_error: null,
};

function normalizeCollectionStatus(data: any): CollectionStatus {
  if (!data) return DEFAULT_COLLECTION_STATUS;
  const rawState = data.state || data.status || 'idle';
  return {
    state: rawState as CollectionState,
    status: rawState,
    session_id: data.session_id ?? null,
    gesture_id: data.gesture_id ?? null,
    gesture_name: data.gesture_name ?? null,
    target_samples: data.target_samples ?? 50,
    collected_samples: data.collected_samples ?? 0,
    progress_pct: data.progress_pct ?? data.progress_percent ?? 0,
    progress_percent: data.progress_percent ?? data.progress_pct ?? 0,
    hand_detected: Boolean(data.hand_detected),
    handedness: data.handedness || 'Unknown',
    fps: data.fps ?? 0,
    last_error: data.last_error ?? null,
  };
}

function normalizeDatasetStats(data: any): DatasetStats {
  if (!data) {
    return {
      total_samples: 0,
      total_gestures: 0,
      gestures_with_insufficient_samples: 0,
      latest_session_id: null,
      completion_percentage: 0,
      gesture_counts: {},
      insufficient_gestures: [],
    };
  }
  const counts = data.gesture_counts || data.samples_per_gesture || {};
  const insufficient = data.insufficient_gestures || data.insufficient_sample_gestures || [];
  return {
    total_samples: data.total_samples ?? 0,
    total_gestures: data.total_gestures ?? 0,
    gestures_with_insufficient_samples:
      data.gestures_with_insufficient_samples ?? insufficient.length,
    latest_session_id: data.latest_session_id ?? null,
    completion_percentage: data.completion_percentage ?? 0,
    gesture_counts: counts,
    samples_per_gesture: counts,
    insufficient_gestures: insufficient,
    insufficient_sample_gestures: insufficient,
  };
}

export const useDatasetStore = create<DatasetStore>((set, get) => ({
  stats: null,
  isLoadingStats: false,

  samples: [],
  samplesTotal: 0,
  samplesLimit: 20,
  samplesOffset: 0,
  selectedGestureFilter: null,
  selectedSessionFilter: null,
  isLoadingSamples: false,

  selectedSample: null,
  isLoadingSampleDetail: false,

  validationReport: null,
  isValidating: false,

  collectionStatus: DEFAULT_COLLECTION_STATUS,
  isPollingCollection: false,

  fetchStats: async () => {
    set({ isLoadingStats: true });
    try {
      const rawStats = await DatasetApi.getStats();
      const stats = normalizeDatasetStats(rawStats);
      set({ stats, isLoadingStats: false });
    } catch (err) {
      console.warn('Could not fetch dataset stats:', err);
      set({ isLoadingStats: false });
    }
  },

  fetchSamples: async (options) => {
    set({ isLoadingSamples: true });
    try {
      const gesture_id = options?.gesture_id !== undefined ? options.gesture_id : get().selectedGestureFilter || undefined;
      const session_id = options?.session_id !== undefined ? options.session_id : get().selectedSessionFilter || undefined;
      const limit = options?.limit !== undefined ? options.limit : get().samplesLimit;
      const offset = options?.offset !== undefined ? options.offset : get().samplesOffset;

      const res = await DatasetApi.getSamples({
        gesture_id,
        session_id,
        limit,
        offset,
      });

      set({
        samples: res.samples,
        samplesTotal: res.total,
        samplesLimit: res.limit,
        samplesOffset: res.offset,
        selectedGestureFilter: gesture_id || null,
        selectedSessionFilter: session_id || null,
        isLoadingSamples: false,
      });
    } catch (err) {
      console.warn('Could not fetch dataset samples:', err);
      set({ isLoadingSamples: false });
    }
  },

  inspectSample: async (sampleId: string) => {
    set({ isLoadingSampleDetail: true });
    try {
      const sample = await DatasetApi.getSample(sampleId);
      set({ selectedSample: sample, isLoadingSampleDetail: false });
    } catch (err) {
      console.error('Could not inspect sample:', err);
      set({ isLoadingSampleDetail: false });
    }
  },

  clearInspectedSample: () => {
    set({ selectedSample: null });
  },

  deleteSample: async (sampleId: string) => {
    try {
      await DatasetApi.deleteSample(sampleId);
      // Refresh samples list & stats
      get().fetchSamples();
      get().fetchStats();
      if (get().selectedSample?.sample_id === sampleId) {
        set({ selectedSample: null });
      }
      return true;
    } catch (err) {
      console.error('Failed to delete sample:', err);
      return false;
    }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await DatasetApi.deleteSession(sessionId);
      get().fetchSamples();
      get().fetchStats();
      return true;
    } catch (err) {
      console.error('Failed to delete session:', err);
      return false;
    }
  },

  runValidation: async () => {
    set({ isValidating: true });
    try {
      const report = await DatasetApi.validateDataset();
      set({ validationReport: report, isValidating: false });
    } catch (err) {
      console.error('Validation failed:', err);
      set({ isValidating: false });
    }
  },

  startCollection: async (gestureId: string, targetSamples: number, sampleIntervalMs = 80) => {
    try {
      const raw = await DatasetApi.startCollection(gestureId, targetSamples, sampleIntervalMs);
      const status = normalizeCollectionStatus(raw);
      set({ collectionStatus: status, isPollingCollection: true });
    } catch (err: any) {
      console.error('Failed to start collection:', err);
      set({
        collectionStatus: {
          ...get().collectionStatus,
          state: 'error',
          status: 'error',
          last_error: err?.message || 'Collection start failed',
        },
      });
      throw err;
    }
  },

  pauseCollection: async () => {
    try {
      const raw = await DatasetApi.pauseCollection();
      const status = normalizeCollectionStatus(raw);
      set({ collectionStatus: status });
    } catch (err) {
      console.error('Failed to pause collection:', err);
    }
  },

  resumeCollection: async () => {
    try {
      const raw = await DatasetApi.resumeCollection();
      const status = normalizeCollectionStatus(raw);
      set({ collectionStatus: status });
    } catch (err) {
      console.error('Failed to resume collection:', err);
    }
  },

  stopCollection: async () => {
    try {
      const raw = await DatasetApi.stopCollection();
      const status = normalizeCollectionStatus(raw);
      set({ collectionStatus: status, isPollingCollection: false });
      // Refresh stats & samples after collection ends
      get().fetchStats();
      get().fetchSamples();
    } catch (err) {
      console.error('Failed to stop collection:', err);
      set({ isPollingCollection: false });
    }
  },

  pollCollectionStatus: async () => {
    try {
      const raw = await DatasetApi.getCollectionStatus();
      const status = normalizeCollectionStatus(raw);
      set({ collectionStatus: status });

      if (status.state === 'completed' || status.state === 'error' || status.state === 'idle') {
        set({ isPollingCollection: false });
        get().fetchStats();
      }

      return status;
    } catch {
      return null;
    }
  },

  setCollectionStatus: (status) => {
    set({ collectionStatus: normalizeCollectionStatus(status) });
  },
}));
