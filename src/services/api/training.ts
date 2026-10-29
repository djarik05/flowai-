import { ApiResponse } from './client';
import { TrainingConfig, TrainingState, DatasetInfo } from '../../types/training';

export interface ITrainingService {
  getDatasetInfo(): Promise<ApiResponse<DatasetInfo>>;
  startTraining(config: TrainingConfig): Promise<ApiResponse<{ taskId: string }>>;
  stopTraining(taskId: string): Promise<ApiResponse<boolean>>;
  getTrainingState(taskId: string): Promise<ApiResponse<TrainingState>>;
}
