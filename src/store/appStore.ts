import { create } from 'zustand';
import { InitState, InitStep, DEFAULT_INIT_STEPS } from '../types/initialization';
import { GestureRecognitionStatus, DetectedGesture, RecognitionLifecycleState } from '../types/gesture';

export type AppView =
  | 'initialization'
  | 'dashboard'
  | 'live-control'
  | 'gesture-manager'
  | 'model-training'
  | 'activity-logs'
  | 'settings';

interface AppStore {
  currentView: AppView;
  isUIMinimized: boolean; // Hide interface / background mode simulation
  isDemoCycling: boolean;
  
  // Initialization state
  initState: InitState;
  startInitialization: () => void;
  cancelInitialization: () => void;
  retryInitialization: () => void;
  setAutoStart: (enabled: boolean) => void;
  advanceInitStep: () => void;
  resetInitialization: () => void;
  
  // Navigation
  setCurrentView: (view: AppView) => void;
  setUIMinimized: (minimized: boolean) => void;
  toggleDemoCycling: () => void;
  
  // Tracking status & recognition lifecycle
  trackingStatus: GestureRecognitionStatus;
  setDetectedGesture: (gesture: DetectedGesture | null) => void;
  setFps: (fps: number) => void;
  setHandDetected: (detected: boolean) => void;
  setRecognitionState: (state: RecognitionLifecycleState, message?: string) => void;
}

const LOCAL_STORAGE_AUTO_START_KEY = 'gestureflow_autostart_pref';

export const useAppStore = create<AppStore>((set, get) => {
  const savedAutoStart = localStorage.getItem(LOCAL_STORAGE_AUTO_START_KEY) !== 'false';

  return {
    currentView: 'initialization',
    isUIMinimized: false,
    isDemoCycling: false,

    initState: {
      status: 'idle',
      progressPercent: 0,
      currentStepIndex: 0,
      steps: DEFAULT_INIT_STEPS.map((s) => ({ ...s })),
      autoStartOnComplete: savedAutoStart,
      canCancel: true,
      statusMessage: 'Ready to initialize simulated core modules',
    },

    startInitialization: () => {
      const steps: InitStep[] = DEFAULT_INIT_STEPS.map((s) => ({ ...s, state: 'pending' }));
      steps[0].state = 'in_progress';

      set({
        initState: {
          ...get().initState,
          status: 'initializing',
          progressPercent: 10,
          currentStepIndex: 0,
          steps,
          statusMessage: steps[0].description || 'Preparing...',
        },
      });
    },

    cancelInitialization: () => {
      set({
        initState: {
          ...get().initState,
          status: 'cancelled',
          statusMessage: 'Initialization cancelled by user.',
        },
      });
    },

    retryInitialization: () => {
      get().startInitialization();
    },

    setAutoStart: (enabled: boolean) => {
      localStorage.setItem(LOCAL_STORAGE_AUTO_START_KEY, String(enabled));
      set({
        initState: {
          ...get().initState,
          autoStartOnComplete: enabled,
        },
      });
    },

    advanceInitStep: () => {
      const { initState } = get();
      const currentIdx = initState.currentStepIndex;
      const nextIdx = currentIdx + 1;
      const totalSteps = initState.steps.length;

      const updatedSteps = [...initState.steps];
      updatedSteps[currentIdx].state = 'completed';

      if (nextIdx < totalSteps) {
        updatedSteps[nextIdx].state = 'in_progress';
        const percent = Math.round(((nextIdx + 0.5) / totalSteps) * 100);

        set({
          initState: {
            ...initState,
            currentStepIndex: nextIdx,
            progressPercent: percent,
            steps: updatedSteps,
            statusMessage: updatedSteps[nextIdx].description || 'Configuring...',
          },
        });
      } else {
        // Complete
        set({
          initState: {
            ...initState,
            status: 'completed',
            progressPercent: 100,
            steps: updatedSteps,
            statusMessage: 'All simulated modules ready. Transitioning...',
          },
        });

        if (initState.autoStartOnComplete) {
          setTimeout(() => {
            set({ currentView: 'dashboard' });
          }, 600);
        }
      }
    },

    resetInitialization: () => {
      set({
        initState: {
          status: 'idle',
          progressPercent: 0,
          currentStepIndex: 0,
          steps: DEFAULT_INIT_STEPS.map((s) => ({ ...s, state: 'pending' as const })),
          autoStartOnComplete: get().initState.autoStartOnComplete,
          canCancel: true,
          statusMessage: 'Ready to initialize simulated core modules',
        },
      });
    },

    setCurrentView: (view: AppView) => set({ currentView: view }),
    setUIMinimized: (minimized: boolean) => set({ isUIMinimized: minimized }),
    toggleDemoCycling: () => set((state) => ({ isDemoCycling: !state.isDemoCycling })),

    trackingStatus: {
      isActive: true,
      currentGesture: null,
      lastGesture: null,
      fps: 30,
      handDetected: false,
      landmarkCount: 0,
      recognitionState: 'no_hand',
      stateMessage: 'No hand detected',
    },

    setDetectedGesture: (gesture: DetectedGesture | null) => {
      set((state) => ({
        trackingStatus: {
          ...state.trackingStatus,
          lastGesture: gesture ? gesture : state.trackingStatus.lastGesture,
          currentGesture: gesture,
          recognitionState: gesture ? 'recognized' : (state.trackingStatus.handDetected ? 'unknown' : 'no_hand'),
          stateMessage: gesture ? gesture.name : (state.trackingStatus.handDetected ? 'Hand detected' : 'No hand detected'),
        },
      }));
    },

    setFps: (fps: number) => {
      set((state) => ({
        trackingStatus: { ...state.trackingStatus, fps },
      }));
    },

    setHandDetected: (detected: boolean) => {
      set((state) => ({
        trackingStatus: {
          ...state.trackingStatus,
          handDetected: detected,
          landmarkCount: detected ? 21 : 0,
          recognitionState: detected
            ? (state.trackingStatus.currentGesture ? 'recognized' : 'hand_detected')
            : 'no_hand',
          stateMessage: detected
            ? (state.trackingStatus.currentGesture?.name || 'Hand detected')
            : 'No hand detected',
        },
      }));
    },

    setRecognitionState: (recognitionState: RecognitionLifecycleState, message?: string) => {
      set((state) => ({
        trackingStatus: {
          ...state.trackingStatus,
          recognitionState,
          stateMessage: message || state.trackingStatus.stateMessage,
        },
      }));
    },
  };
});
