// Training type definitions

export type ModelType = 'mlp_landmark' | 'temporal_gesture' | 'cnn_experimental';

export const MODEL_TYPE_LABELS: Record<ModelType, string> = {
  mlp_landmark: 'MLP Landmark Classifier',
  temporal_gesture: 'Temporal Gesture Classifier',
  cnn_experimental: 'Experimental CNN Classifier',
};

export const MODEL_TYPE_DESCRIPTIONS: Record<ModelType, string> = {
  mlp_landmark: 'Classifies static hand poses from landmark coordinates',
  temporal_gesture: 'Recognizes time-based gesture sequences',
  cnn_experimental: 'Experimental image-based classifier (research only)',
};

export interface DatasetInfo {
  name: string;
  gestureClasses: number;
  totalSamples: number;
  balance: Record<string, number>;
  lastUpdated: string;
}

export interface TrainingConfig {
  modelType: ModelType;
  trainSplit: number;
  valSplit: number;
  testSplit: number;
  epochs: number;
  batchSize: number;
  learningRate: number;
  sequenceLength: number;
}

export interface TrainingMetrics {
  epoch: number;
  trainLoss: number;
  valLoss: number;
  trainAccuracy: number;
  valAccuracy: number;
}

export type TrainingStatus = 'idle' | 'preparing' | 'training' | 'completed' | 'failed' | 'stopped';

export interface TrainingState {
  status: TrainingStatus;
  config: TrainingConfig;
  currentEpoch: number;
  totalEpochs: number;
  metrics: TrainingMetrics[];
  startTime: number | null;
  endTime: number | null;
  error: string | null;
}

export const DEFAULT_TRAINING_CONFIG: TrainingConfig = {
  modelType: 'mlp_landmark',
  trainSplit: 0.7,
  valSplit: 0.15,
  testSplit: 0.15,
  epochs: 50,
  batchSize: 32,
  learningRate: 0.001,
  sequenceLength: 30,
};
