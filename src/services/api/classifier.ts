// API Client for Phase 4 Static Gesture Classifier & Model Registry

import {
  ClassifierStatusResponse,
  DatasetReadinessReport,
  ModelMetadata,
  PredictionResponse,
  TrainingConfigRequest,
  TrainingJobStatus,
} from '../../types/classifier';
import { API_BASE_URL } from './client';

const BASE_URL = API_BASE_URL;

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const json = await res.json();
      if (json && (json.detail || json.message)) {
        errorDetail = json.detail || json.message;
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const ClassifierApi = {
  // Classifier Status
  async getStatus(): Promise<ClassifierStatusResponse> {
    const res = await fetch(`${BASE_URL}/classifier/status`, { mode: 'cors' });
    return handleResponse<ClassifierStatusResponse>(res);
  },

  // Dataset Readiness
  async getDatasetReadiness(minSamples: number = 5): Promise<DatasetReadinessReport> {
    const res = await fetch(`${BASE_URL}/classifier/dataset-readiness?min_samples=${minSamples}`, {
      mode: 'cors',
    });
    return handleResponse<DatasetReadinessReport>(res);
  },

  // Start Training
  async startTraining(config: TrainingConfigRequest): Promise<TrainingJobStatus> {
    const res = await fetch(`${BASE_URL}/classifier/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
      mode: 'cors',
    });
    return handleResponse<TrainingJobStatus>(res);
  },

  // Poll Training Job
  async getTrainingJob(jobId: string): Promise<TrainingJobStatus> {
    const res = await fetch(`${BASE_URL}/classifier/train/${jobId}`, { mode: 'cors' });
    return handleResponse<TrainingJobStatus>(res);
  },

  // Real-time Prediction
  async predictGesture(
    landmarks: number[][],
    handedness: string = 'Right',
    confidenceThreshold?: number
  ): Promise<PredictionResponse> {
    const res = await fetch(`${BASE_URL}/classifier/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        landmarks,
        handedness,
        confidence_threshold: confidenceThreshold,
      }),
      mode: 'cors',
    });
    return handleResponse<PredictionResponse>(res);
  },

  // Seed Demo Samples for registered gestures
  async seedDemoSamples(samplesPerGesture: number = 15): Promise<{
    success: boolean;
    message: string;
    seeded: Record<string, number>;
  }> {
    const res = await fetch(
      `${BASE_URL}/classifier/seed-samples?samples_per_gesture=${samplesPerGesture}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors',
      }
    );
    return handleResponse<{
      success: boolean;
      message: string;
      seeded: Record<string, number>;
    }>(res);
  },

  // Models Registry
  async listModels(): Promise<ModelMetadata[]> {
    const res = await fetch(`${BASE_URL}/models`, { mode: 'cors' });
    return handleResponse<ModelMetadata[]>(res);
  },

  // Active Model
  async getActiveModel(): Promise<ModelMetadata | null> {
    const res = await fetch(`${BASE_URL}/models/active`, { mode: 'cors' });
    return handleResponse<ModelMetadata | null>(res);
  },

  // Model Details
  async getModelDetails(modelId: string): Promise<ModelMetadata> {
    const res = await fetch(`${BASE_URL}/models/${modelId}`, { mode: 'cors' });
    return handleResponse<ModelMetadata>(res);
  },

  // Compare Models
  async compareModels(modelA: string, modelB: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/models/compare?model_a=${modelA}&model_b=${modelB}`, {
      mode: 'cors',
    });
    return handleResponse<any>(res);
  },

  // Activate Model
  async activateModel(modelId: string): Promise<{ success: boolean; message: string; model_id: string }> {
    const res = await fetch(`${BASE_URL}/models/${modelId}/activate`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; message: string; model_id: string }>(res);
  },

  // Deactivate Model
  async deactivateModel(modelId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/models/${modelId}/deactivate`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  // Delete Model
  async deleteModel(modelId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/models/${modelId}`, {
      method: 'DELETE',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },
};
