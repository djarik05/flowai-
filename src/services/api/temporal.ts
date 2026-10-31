// API Client for Phase 5 Temporal Gesture Recognition & Sequences

import {
  TemporalCollectionStatus,
  TemporalEngineStatusResponse,
  TemporalGestureDefinition,
  TemporalGestureEvent,
} from '../../types/temporal';
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

export const TemporalApi = {
  // Engine status
  async getStatus(): Promise<TemporalEngineStatusResponse> {
    const res = await fetch(`${BASE_URL}/temporal/status`, { mode: 'cors' });
    return handleResponse<TemporalEngineStatusResponse>(res);
  },

  // Gesture Catalog
  async getGestures(): Promise<TemporalGestureDefinition[]> {
    const res = await fetch(`${BASE_URL}/temporal/gestures`, { mode: 'cors' });
    return handleResponse<TemporalGestureDefinition[]>(res);
  },

  // Event history
  async getEvents(limit: number = 20): Promise<TemporalGestureEvent[]> {
    const res = await fetch(`${BASE_URL}/temporal/events?limit=${limit}`, { mode: 'cors' });
    return handleResponse<TemporalGestureEvent[]>(res);
  },

  // Reset Engine
  async resetEngine(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/temporal/reset`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  // Dataset Sequence Recording
  async startCollection(
    gestureId: string,
    sessionId?: string,
    targetSequences: number = 10
  ): Promise<TemporalCollectionStatus> {
    const params = new URLSearchParams({
      gesture_id: gestureId,
      target_sequences: targetSequences.toString(),
    });
    if (sessionId) params.append('session_id', sessionId);

    const res = await fetch(`${BASE_URL}/temporal/dataset/start?${params.toString()}`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<TemporalCollectionStatus>(res);
  },

  async commitSequence(): Promise<any> {
    const res = await fetch(`${BASE_URL}/temporal/dataset/commit`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<any>(res);
  },

  async stopCollection(): Promise<TemporalCollectionStatus> {
    const res = await fetch(`${BASE_URL}/temporal/dataset/stop`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<TemporalCollectionStatus>(res);
  },

  async getDatasetStats(): Promise<any> {
    const res = await fetch(`${BASE_URL}/temporal/dataset/stats`, { mode: 'cors' });
    return handleResponse<any>(res);
  },
};
