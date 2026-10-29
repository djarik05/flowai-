// Initialization step types

export type StepState = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface InitStep {
  id: string;
  label: string;
  state: StepState;
  durationMs: number;
  description?: string;
  errorMessage?: string;
}

export type InitOverallStatus = 'idle' | 'initializing' | 'completed' | 'failed' | 'cancelled';

export interface InitState {
  status: InitOverallStatus;
  progressPercent: number;
  currentStepIndex: number;
  steps: InitStep[];
  autoStartOnComplete: boolean;
  canCancel: boolean;
  statusMessage: string;
}

export const DEFAULT_INIT_STEPS: InitStep[] = [
  { id: 'prep_app', label: 'Preparing Application', state: 'pending', durationMs: 800, description: 'Loading core runtime & UI state' },
  { id: 'init_camera', label: 'Initializing Camera Module', state: 'pending', durationMs: 1200, description: 'Checking camera interfaces (Simulated)' },
  { id: 'load_tracking', label: 'Loading Hand Tracking', state: 'pending', durationMs: 1400, description: 'Preparing 21-point landmark mesh pipeline' },
  { id: 'load_model', label: 'Loading AI Model', state: 'pending', durationMs: 1500, description: 'Caching neural pose classifier weights' },
  { id: 'setup_controls', label: 'Setting Up Controls', state: 'pending', durationMs: 900, description: 'Registering air mouse coordinate transforms' },
  { id: 'apply_settings', label: 'Applying Your Settings', state: 'pending', durationMs: 700, description: 'Loading persisted user sensitivity profile' },
  { id: 'ready', label: 'Ready to Start', state: 'pending', durationMs: 400, description: 'GestureFlow AI frontend ready' },
];
