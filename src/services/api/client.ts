// API Client configuration & interface definitions for future Python FastAPI backend

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  isBackendConnected: boolean;
}

export const API_CONFIG: ApiConfig = {
  baseUrl: import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000/api/v1',
  timeout: 5000,
  isBackendConnected: false, // Explicitly false for frontend-only demo
};

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
  simulated: boolean;
}
