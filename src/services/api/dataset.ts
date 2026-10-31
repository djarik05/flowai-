// Real HTTP Dataset & Live Collection API client for GestureFlow AI Phase 6A

import {
  DatasetStats,
  SampleListResponse,
  DatasetSample,
  ValidationReport,
  CollectionStatus as DatasetCollectionStatus,
} from '../../types/dataset';
import {
  MouseSettings,
  MouseSettingsUpdateRequest,
  MouseStatusResponse,
  CursorPointRequest,
} from '../../types/mouse';

const BASE_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000/api/v1';

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

export const DatasetApi = {
  // Stats
  async getStats(): Promise<DatasetStats> {
    const res = await fetch(`${BASE_URL}/dataset/stats`, { mode: 'cors' });
    return handleResponse<DatasetStats>(res);
  },

  // Samples
  async getSamples(params?: {
    gesture_id?: string;
    session_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<SampleListResponse> {
    const query = new URLSearchParams();
    if (params?.gesture_id) query.set('gesture_id', params.gesture_id);
    if (params?.session_id) query.set('session_id', params.session_id);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset !== undefined) query.set('offset', params.offset.toString());

    const url = `${BASE_URL}/dataset/samples${query.toString() ? '?' + query.toString() : ''}`;
    const res = await fetch(url, { mode: 'cors' });
    return handleResponse<SampleListResponse>(res);
  },

  async getSample(sampleId: string): Promise<DatasetSample> {
    const res = await fetch(`${BASE_URL}/dataset/samples/${encodeURIComponent(sampleId)}`, {
      mode: 'cors',
    });
    return handleResponse<DatasetSample>(res);
  },

  async deleteSample(sampleId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/dataset/samples/${encodeURIComponent(sampleId)}`, {
      method: 'DELETE',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  async deleteSession(sessionId: string): Promise<{ success: boolean; deleted_samples: number; message: string }> {
    const res = await fetch(`${BASE_URL}/dataset/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; deleted_samples: number; message: string }>(res);
  },

  // Validation
  async validateDataset(): Promise<ValidationReport> {
    const res = await fetch(`${BASE_URL}/dataset/validate`, { mode: 'cors' });
    return handleResponse<ValidationReport>(res);
  },

  // Export URLs
  getExportCsvUrl(): string {
    return `${BASE_URL}/dataset/export/csv`;
  },

  getExportJsonUrl(): string {
    return `${BASE_URL}/dataset/export/json`;
  },

  async downloadExport(format: 'csv' | 'json'): Promise<void> {
    const url = format === 'csv' ? this.getExportCsvUrl() : this.getExportJsonUrl();
    const res = await fetch(url, { mode: 'cors' });
    if (!res.ok) throw new Error(`Export download failed with status ${res.status}`);
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `gestureflow_dataset_${new Date().toISOString().slice(0, 10)}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },

  // Live Collection Lifecycle
  async startCollection(
    gestureId: string,
    targetSamples: number = 50,
    sampleIntervalMs: number = 80
  ): Promise<DatasetCollectionStatus> {
    const res = await fetch(`${BASE_URL}/collection/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gesture_id: gestureId,
        target_samples: targetSamples,
        sample_interval_ms: sampleIntervalMs,
      }),
      mode: 'cors',
    });
    return handleResponse<DatasetCollectionStatus>(res);
  },

  async pauseCollection(): Promise<DatasetCollectionStatus> {
    const res = await fetch(`${BASE_URL}/collection/pause`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<DatasetCollectionStatus>(res);
  },

  async resumeCollection(): Promise<DatasetCollectionStatus> {
    const res = await fetch(`${BASE_URL}/collection/resume`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<DatasetCollectionStatus>(res);
  },

  async stopCollection(): Promise<DatasetCollectionStatus> {
    const res = await fetch(`${BASE_URL}/collection/stop`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<DatasetCollectionStatus>(res);
  },

  async getCollectionStatus(): Promise<DatasetCollectionStatus> {
    const res = await fetch(`${BASE_URL}/collection/status`, { mode: 'cors' });
    return handleResponse<DatasetCollectionStatus>(res);
  },

  // Mouse Control
  async feedCursorPoint(x: number, y: number, timestamp?: number): Promise<{ success: boolean; enabled: boolean }> {
    const request = { x, y, timestamp };
    const res = await fetch(`${BASE_URL}/mouse/cursor-point`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; enabled: boolean }>(res);
  },
};