// TypeScript types for Phase 4 Static Gesture Classifier & Model Registry

export interface DatasetReadinessClassReport {
  gesture_id: string;
  gesture_name: string;
  sample_count: number;
  valid_sample_count: number;
  invalid_sample_count: number;
  missing_landmarks_count: number;
  coordinate_schema: '3D' | '2D';
  handedness_distribution: Record<string, number>;
  dataset_compatibility: 'compatible_3d' | '2d_only' | 'incompatible';
  is_ready: boolean;
  warnings: string[];
}

export interface DatasetReadinessReport {
  total_gestures: number;
  total_samples: number;
  valid_samples: number;
  invalid_samples: number;
  ready_classes_count: number;
  min_samples_per_class: number;
  classes: DatasetReadinessClassReport[];
  class_imbalance_ratio: number;
  is_training_ready: boolean;
  summary: string;
  warnings: string[];
}

export interface TrainingConfigRequest {
  gesture_ids?: string[] | null;
  model_name: string;
  hidden_layers: number[];
  dropout_rates: number[];
  epochs: number;
  batch_size: number;
  learning_rate: number;
  train_split: number;
  val_split: number;
  test_split: number;
  confidence_threshold: number;
  session_aware_split: boolean;
}

export interface TrainingMetricItem {
  epoch: number;
  train_loss: number;
  val_loss: number;
  train_accuracy: number;
  val_accuracy: number;
}

export interface ClassEvaluationMetric {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface EvaluationMetrics {
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  f1_macro: number;
  confusion_matrix: number[][];
  class_labels: string[];
  per_class: Record<string, ClassEvaluationMetric>;
  test_samples_count: number;
}

export interface ModelMetadata {
  model_id: string;
  model_name: string;
  version: string;
  created_at: string;
  dataset_version: string;
  classes: { id: string; name: string }[];
  feature_schema: string;
  feature_dim: number;
  preprocessing_config: Record<string, any>;
  training_config: Record<string, any>;
  metrics: EvaluationMetrics;
  model_file: string;
  is_active: boolean;
}

export interface TrainingJobStatus {
  job_id: string;
  status: 'pending' | 'training' | 'completed' | 'failed' | 'cancelled';
  current_epoch: number;
  total_epochs: number;
  progress_percent: number;
  latest_train_loss?: number | null;
  latest_val_loss?: number | null;
  latest_train_accuracy?: number | null;
  latest_val_accuracy?: number | null;
  metrics_history: TrainingMetricItem[];
  logs: string[];
  created_model_id?: string | null;
  error?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface PredictionResponse {
  gesture_id?: string | null;
  gesture_name: string;
  confidence: number;
  is_recognized: boolean;
  all_probabilities: Record<string, number>;
  inference_latency_ms: number;
  model_id?: string | null;
  threshold: number;
}

export interface ClassifierStatusResponse {
  is_model_loaded: boolean;
  active_model_id?: string | null;
  active_model_name?: string | null;
  classes: { id: string; name: string }[];
  confidence_threshold: number;
  inference_count: number;
  avg_inference_latency_ms: number;
}
