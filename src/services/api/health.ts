import { ApiResponse } from './client';

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'offline';
  backendVersion: string;
  pythonRuntime: string;
  cameraAvailable: boolean;
  modelLoaded: boolean;
  osControllerHooked: boolean;
}

export interface IHealthService {
  checkHealth(): Promise<ApiResponse<HealthStatus>>;
  getCameraStatus(): Promise<ApiResponse<{ active: boolean; fps: number; device: string }>>;
}
