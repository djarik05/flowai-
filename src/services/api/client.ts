// API Client configuration & interface definitions for future Python FastAPI backend

// Centralized API configuration for GestureFlow AI
const defaultBaseUrl =
  typeof window !== 'undefined'
    ? '/api/v1'
    : 'http://127.0.0.1:8000/api/v1';

export const API_BASE_URL: string =
  import.meta.env.VITE_BACKEND_API_URL || defaultBaseUrl;

export const BACKEND_SERVER_URL: string =
  API_BASE_URL.startsWith('/')
    ? (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000')
    : API_BASE_URL.replace(/\/api\/v1\/?$/, '');

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  isBackendConnected: boolean;
}

export const API_CONFIG: ApiConfig = {
  baseUrl: API_BASE_URL,
  timeout: 5000,
  isBackendConnected: false,
};

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
  simulated: boolean;
}
