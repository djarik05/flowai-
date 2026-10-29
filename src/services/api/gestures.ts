import { ApiResponse } from './client';
import { GestureDefinition, DetectedGesture } from '../../types/gesture';

export interface IGestureService {
  getGestures(): Promise<ApiResponse<GestureDefinition[]>>;
  createGesture(gesture: Omit<GestureDefinition, 'id' | 'isDefault'>): Promise<ApiResponse<GestureDefinition>>;
  updateGesture(id: string, gesture: Partial<GestureDefinition>): Promise<ApiResponse<GestureDefinition>>;
  deleteGesture(id: string): Promise<ApiResponse<boolean>>;
  getLatestDetection(): Promise<ApiResponse<DetectedGesture | null>>;
}
