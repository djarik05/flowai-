import { ApiResponse } from '../api/client';
import { IHealthService, HealthStatus } from '../api/health';
import { IGestureService } from '../api/gestures';
import { ITrainingService } from '../api/training';
import { IControllerService } from '../api/controller';
import { GestureDefinition, DetectedGesture } from '../../types/gesture';
import { SAMPLE_GESTURES, SAMPLE_DATASET } from './sampleData';
import { DatasetInfo, TrainingConfig, TrainingState } from '../../types/training';
import { ControllerSettings } from '../../types/settings';

class DemoHealthService implements IHealthService {
  async checkHealth(): Promise<ApiResponse<HealthStatus>> {
    return {
      status: 200,
      simulated: true,
      data: {
        status: 'ok',
        backendVersion: 'v0.0.0-frontend-mock',
        pythonRuntime: 'None (Simulation Only)',
        cameraAvailable: false,
        modelLoaded: false,
        osControllerHooked: false,
      },
    };
  }

  async getCameraStatus() {
    return {
      status: 200,
      simulated: true,
      data: {
        active: false,
        fps: 30,
        device: 'Virtual Canvas Stream (Simulated)',
      },
    };
  }
}

class DemoGestureService implements IGestureService {
  private gestures: GestureDefinition[] = [...SAMPLE_GESTURES];

  async getGestures(): Promise<ApiResponse<GestureDefinition[]>> {
    return {
      status: 200,
      simulated: true,
      data: [...this.gestures],
    };
  }

  async createGesture(gesture: Omit<GestureDefinition, 'id' | 'isDefault'>): Promise<ApiResponse<GestureDefinition>> {
    const newGesture: GestureDefinition = {
      ...gesture,
      id: `custom_${Date.now()}`,
      isDefault: false,
    };
    this.gestures.push(newGesture);
    return {
      status: 201,
      simulated: true,
      data: newGesture,
    };
  }

  async updateGesture(id: string, updates: Partial<GestureDefinition>): Promise<ApiResponse<GestureDefinition>> {
    const idx = this.gestures.findIndex((g) => g.id === id);
    if (idx === -1) throw new Error('Gesture not found');
    this.gestures[idx] = { ...this.gestures[idx], ...updates };
    return {
      status: 200,
      simulated: true,
      data: this.gestures[idx],
    };
  }

  async deleteGesture(id: string): Promise<ApiResponse<boolean>> {
    this.gestures = this.gestures.filter((g) => g.id !== id);
    return {
      status: 200,
      simulated: true,
      data: true,
    };
  }

  async getLatestDetection(): Promise<ApiResponse<DetectedGesture | null>> {
    const active = this.gestures.filter((g) => g.enabled);
    if (active.length === 0) {
      return { status: 200, simulated: true, data: null };
    }
    const random = active[Math.floor(Math.random() * active.length)];
    return {
      status: 200,
      simulated: true,
      data: {
        gestureId: random.id,
        name: random.name,
        confidence: Math.round((0.82 + Math.random() * 0.16) * 100) / 100,
        timestamp: Date.now(),
        action: random.action,
      },
    };
  }
}

class DemoTrainingService implements ITrainingService {
  async getDatasetInfo(): Promise<ApiResponse<DatasetInfo>> {
    return {
      status: 200,
      simulated: true,
      data: SAMPLE_DATASET,
    };
  }

  async startTraining(config: TrainingConfig): Promise<ApiResponse<{ taskId: string }>> {
    return {
      status: 200,
      simulated: true,
      message: 'Simulated training pipeline initialized',
      data: { taskId: `task_${Date.now()}` },
    };
  }

  async stopTraining(): Promise<ApiResponse<boolean>> {
    return {
      status: 200,
      simulated: true,
      data: true,
    };
  }

  async getTrainingState(): Promise<ApiResponse<TrainingState>> {
    return {
      status: 200,
      simulated: true,
      data: {
        status: 'idle',
        config: {
          modelType: 'mlp_landmark',
          trainSplit: 0.7,
          valSplit: 0.15,
          testSplit: 0.15,
          epochs: 50,
          batchSize: 32,
          learningRate: 0.001,
          sequenceLength: 30,
        },
        currentEpoch: 0,
        totalEpochs: 50,
        metrics: [],
        startTime: null,
        endTime: null,
        error: null,
      },
    };
  }
}

class DemoControllerService implements IControllerService {
  private enabled = false;
  private paused = false;

  async getControllerStatus() {
    return {
      status: 200,
      simulated: true,
      data: {
        enabled: this.enabled,
        paused: this.paused,
        osMouseCaptured: false,
      },
    };
  }

  async setControllerEnabled(enabled: boolean) {
    this.enabled = enabled;
    return { status: 200, simulated: true, data: this.enabled };
  }

  async pauseController() {
    this.paused = true;
    return { status: 200, simulated: true, data: true };
  }

  async resumeController() {
    this.paused = false;
    return { status: 200, simulated: true, data: true };
  }

  async emergencyStop() {
    this.enabled = false;
    this.paused = true;
    return { status: 200, simulated: true, data: true };
  }

  async updateSettings(settings: Partial<ControllerSettings>) {
    return {
      status: 200,
      simulated: true,
      data: settings as ControllerSettings,
    };
  }
}

export const demoAdapter = {
  health: new DemoHealthService(),
  gestures: new DemoGestureService(),
  training: new DemoTrainingService(),
  controller: new DemoControllerService(),
};
