// Phase 6A: Mouse Movement REST API Client

import { MouseStatus, MouseSettingsUpdate } from '../../types/mouse';
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
    } catch {}
    throw new Error(errorDetail);
  }
  return res.json();
}

let isFeedingInFlight = false;

export const MouseApi = {
  getStatus: async (): Promise<MouseStatus> => {
    const res = await fetch(`${BASE_URL}/mouse/status`, { method: 'GET' });
    return handleResponse<MouseStatus>(res);
  },

  enable: async (): Promise<MouseStatus> => {
    const res = await fetch(`${BASE_URL}/mouse/enable`, { method: 'POST' });
    return handleResponse<MouseStatus>(res);
  },

  disable: async (): Promise<MouseStatus> => {
    const res = await fetch(`${BASE_URL}/mouse/disable`, { method: 'POST' });
    return handleResponse<MouseStatus>(res);
  },

  emergencyStop: async (): Promise<MouseStatus> => {
    const res = await fetch(`${BASE_URL}/mouse/emergency-stop`, { method: 'POST' });
    return handleResponse<MouseStatus>(res);
  },

  updateSettings: async (settings: MouseSettingsUpdate): Promise<MouseStatus> => {
    const res = await fetch(`${BASE_URL}/mouse/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return handleResponse<MouseStatus>(res);
  },

  triggerClick: async (): Promise<{ success: boolean; click_count: number }> => {
    const res = await fetch(`${BASE_URL}/mouse/click`, { method: 'POST' });
    return handleResponse<{ success: boolean; click_count: number }>(res);
  },

  triggerRightClick: async (): Promise<{ success: boolean; right_click_count: number }> => {
    const res = await fetch(`${BASE_URL}/mouse/click-right`, { method: 'POST' });
    return handleResponse<{ success: boolean; right_click_count: number }>(res);
  },

  feedCursorPoint: async (
    x: number,
    y: number,
    timestamp?: number,
    pinchDistance?: number,
    thumbX?: number,
    thumbY?: number,
    rightPinchDistance?: number,
    middleX?: number,
    middleY?: number
  ): Promise<void> => {
    if (isFeedingInFlight) return; // Prevent socket saturation in browser
    isFeedingInFlight = true;
    try {
      await fetch(`${BASE_URL}/mouse/cursor-point`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          x,
          y,
          timestamp: timestamp || Date.now() / 1000,
          pinch_distance: pinchDistance,
          thumb_x: thumbX,
          thumb_y: thumbY,
          right_pinch_distance: rightPinchDistance,
          middle_x: middleX,
          middle_y: middleY,
        }),
      });
    } catch {
      // transient network drop
    } finally {
      isFeedingInFlight = false;
    }
  },
};
