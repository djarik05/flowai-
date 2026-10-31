// API Client for Public Datasets (HaGRIDv2) and Dataset Combiner in GestureFlow AI

import {
  HagridDatasetInfo,
  HagridClassInfo,
  HagridClassMappingsResponse,
  HagridClassMapping,
  PublicJobStatusResponse,
  DatasetSourcesResponse,
  DatasetCombineRequest,
  DatasetCombineResponse,
  CombinedDatasetSummary,
} from '../../types/publicDataset';
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

export const PublicDatasetsApi = {
  // Catalog & Overview
  async getCatalog(): Promise<{ datasets: Array<{ id: string; name: string; version: string; status: string }> }> {
    const res = await fetch(`${BASE_URL}/public-datasets`, { mode: 'cors' });
    return handleResponse(res);
  },

  async getHagridInfo(): Promise<HagridDatasetInfo> {
    const res = await fetch(`${BASE_URL}/public-datasets/hagrid`, { mode: 'cors' });
    return handleResponse<HagridDatasetInfo>(res);
  },

  async getHagridClasses(): Promise<{ classes: HagridClassInfo[]; total: number }> {
    const res = await fetch(`${BASE_URL}/public-datasets/hagrid/classes`, { mode: 'cors' });
    return handleResponse<{ classes: HagridClassInfo[]; total: number }>(res);
  },

  // Class Mappings
  async getHagridMappings(): Promise<HagridClassMappingsResponse> {
    const res = await fetch(`${BASE_URL}/public-datasets/hagrid/mappings`, { mode: 'cors' });
    return handleResponse<HagridClassMappingsResponse>(res);
  },

  async updateHagridMappings(mappings: Record<string, HagridClassMapping>): Promise<{ success: boolean; updated_count: number; message: string }> {
    const res = await fetch(`${BASE_URL}/public-datasets/hagrid/mappings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mappings }),
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; updated_count: number; message: string }>(res);
  },

  // Selective Downloads
  async startDownload(request: {
    download_annotations?: boolean;
    classes?: string[];
  }): Promise<{ job_id: string; message: string; status: string }> {
    const res = await fetch(`${BASE_URL}/public-datasets/hagrid/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      mode: 'cors',
    });
    return handleResponse<{ job_id: string; message: string; status: string }>(res);
  },

  async getDownloadStatus(jobId: string): Promise<PublicJobStatusResponse> {
    const res = await fetch(`${BASE_URL}/public-datasets/download/${encodeURIComponent(jobId)}`, { mode: 'cors' });
    return handleResponse<PublicJobStatusResponse>(res);
  },

  async cancelDownload(jobId: string): Promise<{ job_id: string; message: string; status: string }> {
    const res = await fetch(`${BASE_URL}/public-datasets/download/${encodeURIComponent(jobId)}/cancel`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<{ job_id: string; message: string; status: string }>(res);
  },

  // Ingestion & Parsing
  async startImport(request: {
    source_type?: 'downloaded_archives' | 'local_path';
    local_path?: string;
    splits?: string[];
    classes?: string[];
    max_samples_per_class?: number;
    create_missing_gestures?: boolean;
  }): Promise<{ job_id: string; message: string; status: string }> {
    const res = await fetch(`${BASE_URL}/public-datasets/hagrid/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      mode: 'cors',
    });
    return handleResponse<{ job_id: string; message: string; status: string }>(res);
  },

  async getImportStatus(jobId: string): Promise<PublicJobStatusResponse> {
    const res = await fetch(`${BASE_URL}/public-datasets/import/${encodeURIComponent(jobId)}`, { mode: 'cors' });
    return handleResponse<PublicJobStatusResponse>(res);
  },

  async cancelImport(jobId: string): Promise<{ job_id: string; message: string; status: string }> {
    const res = await fetch(`${BASE_URL}/public-datasets/import/${encodeURIComponent(jobId)}/cancel`, {
      method: 'POST',
      mode: 'cors',
    });
    return handleResponse<{ job_id: string; message: string; status: string }>(res);
  },

  async getValidationReport(jobId: string): Promise<{ report: any }> {
    const res = await fetch(`${BASE_URL}/public-datasets/validation/${encodeURIComponent(jobId)}`, { mode: 'cors' });
    return handleResponse<{ report: any }>(res);
  },

  // Dataset Combiner & Sources
  async getDatasetSources(): Promise<DatasetSourcesResponse> {
    const res = await fetch(`${BASE_URL}/dataset/sources`, { mode: 'cors' });
    return handleResponse<DatasetSourcesResponse>(res);
  },

  async combineDatasets(request: DatasetCombineRequest): Promise<DatasetCombineResponse> {
    const res = await fetch(`${BASE_URL}/dataset/combine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      mode: 'cors',
    });
    return handleResponse<DatasetCombineResponse>(res);
  },

  async getCombinedDatasets(): Promise<{ combined_datasets: CombinedDatasetSummary[]; count: number }> {
    const res = await fetch(`${BASE_URL}/dataset/combined`, { mode: 'cors' });
    return handleResponse<{ combined_datasets: CombinedDatasetSummary[]; count: number }>(res);
  },

  async downloadCombinedExport(combinedId: string, format: 'csv' | 'json'): Promise<void> {
    const url = `${BASE_URL}/dataset/combined/${encodeURIComponent(combinedId)}/export/${format}`;
    const res = await fetch(url, { mode: 'cors' });
    if (!res.ok) throw new Error(`Combined dataset export download failed with status ${res.status}`);
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `combined_${combinedId}_dataset.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },
};
