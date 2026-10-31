// Real HTTP Gestures API client for GestureFlow AI Phase 3

import { GestureDefinition, DetectedGesture } from '../../types/gesture';
import { ApiResponse, API_BASE_URL } from './client';

export interface IGestureService {
  getGestures(): Promise<ApiResponse<GestureDefinition[]>>;
  createGesture(gesture: Omit<GestureDefinition, 'id' | 'isDefault'>): Promise<ApiResponse<GestureDefinition>>;
  updateGesture(id: string, gesture: Partial<GestureDefinition>): Promise<ApiResponse<GestureDefinition>>;
  deleteGesture(id: string): Promise<ApiResponse<boolean>>;
  getLatestDetection(): Promise<ApiResponse<DetectedGesture | null>>;
}

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

export interface BackendGesture {
  id: string;
  name: string;
  description: string;
  type: 'static' | 'temporal';
  action: string;
  confidence_threshold: number;
  is_default: boolean;
  icon: string;
  custom_shortcut?: string | null;
  sample_count: number;
  created_at: string;
  updated_at: string;
}

export function mapBackendGestureToFrontend(bg: BackendGesture): GestureDefinition {
  return {
    id: bg.id,
    name: bg.name,
    description: bg.description,
    type: bg.type,
    action: bg.action as any,
    confidenceThreshold: bg.confidence_threshold,
    isDefault: bg.is_default,
    icon: bg.icon,
    customShortcut: bg.custom_shortcut || undefined,
    sampleCount: bg.sample_count,
    sample_count: bg.sample_count,
    enabled: true,
    created_at: bg.created_at,
    updated_at: bg.updated_at,
  };
}

export const GesturesApi = {
  async listGestures(): Promise<GestureDefinition[]> {
    const res = await fetch(`${BASE_URL}/gestures`, { mode: 'cors' });
    const data = await handleResponse<{ gestures: BackendGesture[]; total: number }>(res);
    return (data.gestures || []).map(mapBackendGestureToFrontend);
  },

  async createGesture(gesture: {
    id?: string;
    name: string;
    description?: string;
    type?: 'static' | 'temporal';
    action?: string;
    confidence_threshold?: number;
    icon?: string;
    custom_shortcut?: string;
    is_default?: boolean;
  }): Promise<GestureDefinition> {
    const res = await fetch(`${BASE_URL}/gestures`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gesture),
      mode: 'cors',
    });
    const created = await handleResponse<BackendGesture>(res);
    return mapBackendGestureToFrontend(created);
  },

  async getGesture(id: string): Promise<GestureDefinition> {
    const res = await fetch(`${BASE_URL}/gestures/${encodeURIComponent(id)}`, { mode: 'cors' });
    const data = await handleResponse<BackendGesture>(res);
    return mapBackendGestureToFrontend(data);
  },

  async updateGesture(
    id: string,
    updates: {
      name?: string;
      description?: string;
      type?: 'static' | 'temporal';
      action?: string;
      confidence_threshold?: number;
      icon?: string;
      custom_shortcut?: string;
    }
  ): Promise<GestureDefinition> {
    const res = await fetch(`${BASE_URL}/gestures/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
      mode: 'cors',
    });
    const updated = await handleResponse<BackendGesture>(res);
    return mapBackendGestureToFrontend(updated);
  },

  async deleteGesture(id: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/gestures/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      mode: 'cors',
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },
};
