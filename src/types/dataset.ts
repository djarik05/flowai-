// Dataset and Live Collection type definitions for GestureFlow AI Phase 3

export interface LandmarkCoord {
  x: number;
  y: number;
  z: number;
}

export interface DatasetSample {
  sample_id: string;
  gesture_id: string;
  gesture_name: string;
  timestamp: string;
  handedness: string;
  confidence: number;
  landmarks: LandmarkCoord[];
  session_id: string;
}

export interface DatasetSampleSummary {
  sample_id: string;
  gesture_id: string;
  gesture_name: string;
  timestamp: string;
  handedness: string;
  confidence: number;
  session_id: string;
}

export interface SampleListResponse {
  samples: DatasetSampleSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface DatasetStats {
  total_samples: number;
  total_gestures: number;
  gestures_with_insufficient_samples: number;
  latest_session_id: string | null;
  completion_percentage: number;
  gesture_counts: Record<string, number>;
  samples_per_gesture?: Record<string, number>;
  insufficient_gestures: string[];
  insufficient_sample_gestures?: string[];
}

export type CollectionState =
  | 'idle'
  | 'starting'
  | 'collecting'
  | 'paused'
  | 'stopping'
  | 'completed'
  | 'cancelled'
  | 'error';

export interface CollectionStatus {
  state: CollectionState;
  status?: string;
  session_id: string | null;
  gesture_id: string | null;
  gesture_name: string | null;
  target_samples: number;
  collected_samples: number;
  progress_pct: number;
  progress_percent?: number;
  hand_detected?: boolean;
  handedness?: string;
  fps: number;
  last_error: string | null;
}

export interface ValidationIssue {
  sample_id: string;
  gesture_id: string;
  issue_type: string;
  detail: string;
  severity: 'error' | 'warning';
}

export interface ValidationReport {
  is_valid: boolean;
  total_checked: number;
  issues_count: number;
  issues: ValidationIssue[];
  checked_at: string;
}
