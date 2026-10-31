// Type definitions for Public Datasets (HaGRIDv2) in GestureFlow AI

export interface HagridClassInfo {
  name: string;
  size_gb: number;
  sample_count_approx: number;
  description: string;
  is_two_handed: boolean;
  download_url: string;
  suggested_gesture_id: string | null;
  suggested_gesture_name: string | null;
}

export interface HagridDatasetInfo {
  name: string;
  full_name: string;
  version: string;
  total_classes: number;
  total_samples: number;
  total_size_tb: number;
  license: string;
  license_url: string;
  repository_url: string;
  paper_title: string;
  paper_url: string;
  authors: string[];
  citation: string;
  annotations_download_url: string;
  classes: HagridClassInfo[];
  downloaded_classes: string[];
  annotations_downloaded: boolean;
  imported_sample_counts: Record<string, number>;
}

export interface HagridClassMapping {
  hagrid_class: string;
  target_gesture_id: string | null;
  target_gesture_name: string | null;
  action: 'map' | 'skip' | 'create_new';
  confidence_threshold: number;
}

export interface HagridClassMappingsResponse {
  mappings: Record<string, HagridClassMapping>;
  available_gestures: Array<{ id: string; name: string; type: string }>;
}

export interface PublicJobStatusResponse {
  job_id: string;
  job_type: 'download' | 'import';
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'error';
  progress_percent: number;
  message: string;
  details: {
    download_annotations?: boolean;
    targets?: string[];
    downloaded_bytes?: number;
    total_bytes?: number;
    speed_mbps?: number;
    current_file?: string | null;
    disk_warning?: string | null;
    samples_imported?: number;
    class_distribution?: Record<string, number>;
    source_type?: string;
    splits?: string[];
  };
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface DatasetSourcesResponse {
  total_samples: number;
  custom_samples_count: number;
  hagrid_samples_count: number;
  coordinate_formats: Record<string, number>;
  gesture_breakdown: Record<string, { custom: number; hagrid: number }>;
}

export interface DatasetCombineRequest {
  name: string;
  include_custom: boolean;
  include_hagrid: boolean;
  selected_gestures?: string[];
  compatibility_mode: '2d_projection' | '2d_only' | '3d_only';
  train_ratio: number;
  val_ratio: number;
  test_ratio: number;
  preserve_subject_splits: boolean;
}

export interface DatasetCombineResponse {
  combined_id: string;
  name: string;
  total_samples: number;
  train_samples: number;
  val_samples: number;
  test_samples: number;
  unique_subjects: number;
  coordinate_format: string;
  landmark_dimension: number;
  classes_included: string[];
  sample_counts_by_class: Record<string, number>;
  export_csv_filename: string;
  export_json_filename: string;
  created_at: string;
}

export interface CombinedDatasetSummary {
  combined_id: string;
  name: string;
  total_samples: number;
  splits_count: Record<string, number>;
  coordinate_format: string;
  classes: string[];
  created_at: string;
}
