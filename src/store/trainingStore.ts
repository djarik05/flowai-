import { create } from 'zustand';
import {
  TrainingConfig,
  TrainingMetrics,
  TrainingStatus,
  DatasetInfo,
  DEFAULT_TRAINING_CONFIG,
} from '../types/training';
import { SAMPLE_DATASET } from '../services/demo/sampleData';

interface TrainingStore {
  dataset: DatasetInfo;
  config: TrainingConfig;
  status: TrainingStatus;
  currentEpoch: number;
  metrics: TrainingMetrics[];
  timerId: number | null;

  updateConfig: (updates: Partial<TrainingConfig>) => void;
  startSimulatedTraining: () => void;
  stopTraining: () => void;
  resetTraining: () => void;
}

export const useTrainingStore = create<TrainingStore>((set, get) => ({
  dataset: SAMPLE_DATASET,
  config: DEFAULT_TRAINING_CONFIG,
  status: 'idle',
  currentEpoch: 0,
  metrics: [],
  timerId: null,

  updateConfig: (updates) => {
    set({ config: { ...get().config, ...updates } });
  },

  startSimulatedTraining: () => {
    // Stop any existing simulation
    if (get().timerId) {
      window.clearInterval(get().timerId!);
    }

    set({
      status: 'training',
      currentEpoch: 0,
      metrics: [],
    });

    const totalEpochs = get().config.epochs;

    const interval = window.setInterval(() => {
      const state = get();
      if (state.status !== 'training') {
        window.clearInterval(interval);
        return;
      }

      const nextEpoch = state.currentEpoch + 1;
      const progress = nextEpoch / totalEpochs;

      // Realistic learning curve simulation with subtle noise
      const noise = (Math.random() - 0.5) * 0.03;
      const trainLoss = Math.max(0.04, Number((1.6 * Math.exp(-progress * 3.5) + 0.05 + noise).toFixed(4)));
      const valLoss = Math.max(0.08, Number((1.7 * Math.exp(-progress * 3.2) + 0.1 + noise * 1.5).toFixed(4)));

      const trainAcc = Math.min(99.6, Number((45 + 53 * (1 - Math.exp(-progress * 4.0)) + noise * 20).toFixed(1)));
      const valAcc = Math.min(97.8, Number((40 + 56 * (1 - Math.exp(-progress * 3.6)) - noise * 15).toFixed(1)));

      const newMetrics: TrainingMetrics = {
        epoch: nextEpoch,
        trainLoss,
        valLoss,
        trainAccuracy: trainAcc,
        valAccuracy: valAcc,
      };

      const updatedList = [...state.metrics, newMetrics];

      if (nextEpoch >= totalEpochs) {
        window.clearInterval(interval);
        set({
          status: 'completed',
          currentEpoch: nextEpoch,
          metrics: updatedList,
          timerId: null,
        });
      } else {
        set({
          currentEpoch: nextEpoch,
          metrics: updatedList,
        });
      }
    }, 280);

    set({ timerId: interval });
  },

  stopTraining: () => {
    const { timerId } = get();
    if (timerId) {
      window.clearInterval(timerId);
    }
    set({ status: 'stopped', timerId: null });
  },

  resetTraining: () => {
    const { timerId } = get();
    if (timerId) {
      window.clearInterval(timerId);
    }
    set({
      status: 'idle',
      currentEpoch: 0,
      metrics: [],
      timerId: null,
    });
  },
}));
