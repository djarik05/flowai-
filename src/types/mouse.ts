// Phase 6A, 6B.1 & 6B.2: Mouse Control, Gesture Left Click & Gesture Right Click Types

export type MouseControlState = 'disabled' | 'active' | 'waiting_for_hand' | 'error';
export type PinchState = 'idle' | 'pinched' | 'cooldown' | 'disabled';

export interface MouseStatus {
  enabled: boolean;
  state: MouseControlState;
  hand_detected: boolean;
  control_point: { x: number; y: number } | null;
  cursor_position: { x: number; y: number };
  screen_size: { width: number; height: number };
  sensitivity: number;
  smoothing_alpha: number;
  active_margin_x: number;
  active_margin_y: number;
  dead_zone: number;
  last_error: string | null;

  // Phase 6B.1 Left Click fields
  left_click_enabled: boolean;
  pinch_distance: number | null;
  pinch_state: PinchState;
  pinch_activation_threshold: number;
  pinch_release_threshold: number;
  click_cooldown_ms: number;
  last_click_time: number | null;
  last_click_position: { x: number; y: number } | null;
  click_count: number;

  // Phase 6B.2 Right Click fields
  right_click_enabled: boolean;
  right_pinch_distance: number | null;
  right_pinch_state: PinchState;
  right_pinch_activation_threshold: number;
  right_pinch_release_threshold: number;
  right_click_cooldown_ms: number;
  last_right_click_time: number | null;
  last_right_click_position: { x: number; y: number } | null;
  right_click_count: number;
}

export interface MouseSettings {
  sensitivity: number;
  smoothing_alpha: number;
  active_margin_x: number;
  active_margin_y: number;
  dead_zone: number;
  tracking_timeout_ms: number;
  left_click_enabled: boolean;
  pinch_activation_threshold: number;
  pinch_release_threshold: number;
  click_cooldown_ms: number;
  right_click_enabled: boolean;
  right_pinch_activation_threshold: number;
  right_pinch_release_threshold: number;
  right_click_cooldown_ms: number;
}

export interface MouseSettingsUpdate {
  sensitivity?: number;
  smoothing_alpha?: number;
  active_margin_x?: number;
  active_margin_y?: number;
  tracking_timeout_ms?: number;
  dead_zone?: number;
  left_click_enabled?: boolean;
  pinch_activation_threshold?: number;
  pinch_release_threshold?: number;
  click_cooldown_ms?: number;
  right_click_enabled?: boolean;
  right_pinch_activation_threshold?: number;
  right_pinch_release_threshold?: number;
  right_click_cooldown_ms?: number;
}

export interface MouseSettingsUpdateRequest extends MouseSettingsUpdate {}

export interface MouseSettingsUpdateResponse extends MouseSettings {}

export interface MouseStatusResponse extends MouseStatus {}

export interface CursorPointRequest {
  x: number;
  y: number;
  timestamp?: number;
  pinch_distance?: number;
  thumb_x?: number;
  thumb_y?: number;
  right_pinch_distance?: number;
  middle_x?: number;
  middle_y?: number;
}

export interface CollectionStatus {
  state: 'idle' | 'collecting' | 'paused' | 'completed' | 'cancelled' | 'error';
  session_id: string | null;
  gesture_id: string | null;
  gesture_name: string | null;
  target_samples: number;
  collected_samples: number;
  progress_percent: number;
  progress_pct: number;
  hand_detected: boolean;
  handedness: string;
  fps: number;
  last_error: string | null;
}