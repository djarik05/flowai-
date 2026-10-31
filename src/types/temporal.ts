// TypeScript definitions for Phase 5 Temporal Gesture Recognition

export type StateMachineState = 'IDLE' | 'CANDIDATE' | 'TRACKING' | 'RECOGNIZED' | 'COOLDOWN';

export interface TemporalGestureDefinition {
  id: string;
  name: string;
  description: string;
  expected_motion: string;
  is_experimental: boolean;
  min_duration_ms: number;
  max_duration_ms: number;
  cooldown_ms: number;
}

export interface TemporalGestureEvent {
  event_id: string;
  event_type: string;
  gesture_id: string;
  gesture_name: string;
  confidence: number;
  status: 'recognized' | 'candidate' | 'completed';
  timestamp: number;
  handedness: string;
  duration_ms: number;
  velocity: number;
  direction: string;
  displacement: {
    dx: number;
    dy: number;
    dz: number;
  };
}

export interface MovementTelemetry {
  hand_id: number;
  handedness: string;
  state: StateMachineState;
  current_position: {
    x: number;
    y: number;
    z: number;
  };
  velocity: {
    vx: number;
    vy: number;
    vz: number;
    speed: number;
  };
  direction: string;
  linearity: number;
  path_length: number;
  buffer_size: number;
  duration_ms: number;
}

export interface TemporalEngineStatusResponse {
  is_active: boolean;
  hands_tracked: number;
  active_gestures_count: number;
  total_events_recognized: number;
  recent_events: TemporalGestureEvent[];
  movement_telemetry: Record<string, MovementTelemetry>;
  avg_processing_latency_ms: number;
}

export interface TemporalCollectionStatus {
  is_collecting: boolean;
  gesture_id?: string | null;
  session_id?: string | null;
  target_sequences: number;
  collected_sequences: number;
  current_sequence_frames: number;
}
