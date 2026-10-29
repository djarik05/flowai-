import { ApiResponse } from './client';
import { ControllerSettings } from '../../types/settings';

export interface IControllerService {
  getControllerStatus(): Promise<ApiResponse<{ enabled: boolean; paused: boolean; osMouseCaptured: boolean }>>;
  setControllerEnabled(enabled: boolean): Promise<ApiResponse<boolean>>;
  pauseController(): Promise<ApiResponse<boolean>>;
  resumeController(): Promise<ApiResponse<boolean>>;
  emergencyStop(): Promise<ApiResponse<boolean>>;
  updateSettings(settings: Partial<ControllerSettings>): Promise<ApiResponse<ControllerSettings>>;
}
