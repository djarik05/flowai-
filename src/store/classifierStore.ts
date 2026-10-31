// Zustand store for Phase 4 Static Gesture Classifier & Model Registry
import { create } from 'zustand';
import { ClassifierApi } from '../services/api/classifier';
import {
  ClassifierStatusResponse,
  DatasetReadinessReport,
  ModelMetadata,
  TrainingConfigRequest,
  TrainingJobStatus,
} from '../types/classifier';

export const DEFAULT_CLASSIFIER_CONFIG: TrainingConfigRequest = {
  model_name: 'GestureMLP_v1',
  hidden_layers: [128, 64],
  dropout_rates: [0.25, 0.2],
  epochs: 40,
  batch_size: 16,
  learning_rate: 0.001,
  train_split: 0.7,
  val_split: 0.15,
  test_split: 0.15,
  confidence_threshold: 0.7,
  session_aware_split: true,
};

interface ClassifierState {
  readiness: DatasetReadinessReport | null;
  isLoadingReadiness: boolean;
  config: TrainingConfigRequest;
  currentJob: TrainingJobStatus | null;
  isTraining: boolean;
  pollIntervalId: number | null;
  models: ModelMetadata[];
  activeModel: ModelMetadata | null;
  selectedModel: ModelMetadata | null;
  classifierStatus: ClassifierStatusResponse | null;
  isSeeding: boolean;
  actionLoading: string | null;
  error: string | null;

  // Actions
  fetchReadiness: () => Promise<void>;
  seedDemoDataset: () => Promise<void>;
  updateConfig: (updates: Partial<TrainingConfigRequest>) => void;
  startTraining: () => Promise<void>;
  pollTrainingJob: (jobId: string) => void;
  stopPolling: () => void;
  fetchModels: () => Promise<void>;
  fetchActiveModel: () => Promise<void>;
  fetchClassifierStatus: () => Promise<void>;
  activateModel: (modelId: string) => Promise<void>;
  deactivateModel: (modelId: string) => Promise<void>;
  deleteModel: (modelId: string) => Promise<void>;
  selectModelForInspection: (model: ModelMetadata | null) => void;
  clearError: () => void;
}

export const useClassifierStore = create<ClassifierState>((set, get) => ({
  readiness: null,
  isLoadingReadiness: false,
  config: DEFAULT_CLASSIFIER_CONFIG,
  currentJob: null,
  isTraining: false,
  pollIntervalId: null,
  models: [],
  activeModel: null,
  selectedModel: null,
  classifierStatus: null,
  isSeeding: false,
  actionLoading: null,
  error: null,

  fetchReadiness: async () => {
    set({ isLoadingReadiness: true, error: null });
    try {
      const report = await ClassifierApi.getDatasetReadiness(5);
      set({ readiness: report, isLoadingReadiness: false });
    } catch (err: any) {
      set({
        isLoadingReadiness: false,
        error: `Failed to audit dataset readiness: ${err.message || err}`,
      });
    }
  },

  seedDemoDataset: async () => {
    set({ isSeeding: true, error: null });
    try {
      await ClassifierApi.seedDemoSamples(15);
      await get().fetchReadiness();
      set({ isSeeding: false });
    } catch (err: any) {
      set({
        isSeeding: false,
        error: `Failed to seed demo samples: ${err.message || err}`,
      });
    }
  },

  updateConfig: (updates) => {
    set({ config: { ...get().config, ...updates } });
  },

  startTraining: async () => {
    const { config, pollIntervalId } = get();
    if (pollIntervalId) {
      window.clearInterval(pollIntervalId);
    }

    set({ isTraining: true, currentJob: null, error: null });

    try {
      const job = await ClassifierApi.startTraining(config);
      set({ currentJob: job });
      get().pollTrainingJob(job.job_id);
    } catch (err: any) {
      set({
        isTraining: false,
        error: `Failed to start training: ${err.message || err}`,
      });
    }
  },

  pollTrainingJob: (jobId: string) => {
    const interval = window.setInterval(async () => {
      try {
        const job = await ClassifierApi.getTrainingJob(jobId);
        set({ currentJob: job });

        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          window.clearInterval(interval);
          set({ isTraining: false, pollIntervalId: null });

          // Refresh models list, active model and readiness
          await get().fetchModels();
          await get().fetchActiveModel();
          await get().fetchClassifierStatus();

          // If completed, automatically inspect the new model
          if (job.status === 'completed' && job.created_model_id) {
            try {
              const details = await ClassifierApi.getModelDetails(job.created_model_id);
              set({ selectedModel: details });
            } catch {
              // ignore
            }
          }
        }
      } catch (err: any) {
        window.clearInterval(interval);
        set({
          isTraining: false,
          pollIntervalId: null,
          error: `Error polling training job: ${err.message || err}`,
        });
      }
    }, 600);

    set({ pollIntervalId: interval });
  },

  stopPolling: () => {
    const { pollIntervalId } = get();
    if (pollIntervalId) {
      window.clearInterval(pollIntervalId);
      set({ pollIntervalId: null, isTraining: false });
    }
  },

  fetchModels: async () => {
    try {
      const list = await ClassifierApi.listModels();
      set({ models: list });
      if (!get().selectedModel && list.length > 0) {
        const active = list.find((m) => m.is_active);
        set({ selectedModel: active || list[0] });
      }
    } catch (err: any) {
      // ignore
    }
  },

  fetchActiveModel: async () => {
    try {
      const active = await ClassifierApi.getActiveModel();
      set({ activeModel: active });
      if (active && !get().selectedModel) {
        set({ selectedModel: active });
      }
    } catch (err: any) {
      // ignore
    }
  },

  fetchClassifierStatus: async () => {
    try {
      const status = await ClassifierApi.getStatus();
      set({ classifierStatus: status });
    } catch (err: any) {
      // ignore
    }
  },

  activateModel: async (modelId: string) => {
    set({ actionLoading: `activate_${modelId}`, error: null });
    try {
      await ClassifierApi.activateModel(modelId);
      await get().fetchModels();
      await get().fetchActiveModel();
      await get().fetchClassifierStatus();
      set({ actionLoading: null });
    } catch (err: any) {
      set({
        actionLoading: null,
        error: `Failed to activate model: ${err.message || err}`,
      });
    }
  },

  deactivateModel: async (modelId: string) => {
    set({ actionLoading: `deactivate_${modelId}`, error: null });
    try {
      await ClassifierApi.deactivateModel(modelId);
      await get().fetchModels();
      await get().fetchActiveModel();
      await get().fetchClassifierStatus();
      set({ actionLoading: null });
    } catch (err: any) {
      set({
        actionLoading: null,
        error: `Failed to deactivate model: ${err.message || err}`,
      });
    }
  },

  deleteModel: async (modelId: string) => {
    set({ actionLoading: `delete_${modelId}`, error: null });
    try {
      await ClassifierApi.deleteModel(modelId);
      if (get().selectedModel?.model_id === modelId) {
        set({ selectedModel: null });
      }
      await get().fetchModels();
      await get().fetchActiveModel();
      await get().fetchClassifierStatus();
      set({ actionLoading: null });
    } catch (err: any) {
      set({
        actionLoading: null,
        error: `Failed to delete model: ${err.message || err}`,
      });
    }
  },

  selectModelForInspection: (model: ModelMetadata | null) => {
    set({ selectedModel: model });
  },

  clearError: () => {
    set({ error: null });
  },
}));
