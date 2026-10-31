import { create } from 'zustand';
import {
  HagridDatasetInfo,
  HagridClassInfo,
  HagridClassMapping,
  PublicJobStatusResponse,
  DatasetSourcesResponse,
  DatasetCombineRequest,
  DatasetCombineResponse,
  CombinedDatasetSummary,
} from '../types/publicDataset';
import { PublicDatasetsApi } from '../services/api/publicDatasets';

interface PublicDatasetStore {
  // Metadata & Info
  hagridInfo: HagridDatasetInfo | null;
  classes: HagridClassInfo[];
  isLoadingInfo: boolean;
  fetchHagridInfo: () => Promise<void>;

  // Mappings
  mappings: Record<string, HagridClassMapping>;
  availableGestures: Array<{ id: string; name: string; type: string }>;
  isLoadingMappings: boolean;
  isSavingMappings: boolean;
  fetchMappings: () => Promise<void>;
  updateMappingEntry: (className: string, update: Partial<HagridClassMapping>) => void;
  saveMappings: () => Promise<boolean>;

  // Download Management
  selectedDownloadClasses: string[];
  includeAnnotationsDownload: boolean;
  activeDownloadJob: PublicJobStatusResponse | null;
  toggleDownloadClass: (className: string) => void;
  selectAllDownloadClasses: () => void;
  clearDownloadClasses: () => void;
  setIncludeAnnotationsDownload: (val: boolean) => void;
  startDownload: () => Promise<string | null>;
  cancelDownload: (jobId: string) => Promise<void>;
  pollDownloadStatus: (jobId: string) => Promise<PublicJobStatusResponse | null>;

  // Ingestion & Import
  selectedImportClasses: string[];
  importSourceType: 'downloaded_archives' | 'local_path';
  localImportPath: string;
  selectedSplits: string[];
  maxSamplesPerClass: number;
  createMissingGestures: boolean;
  activeImportJob: PublicJobStatusResponse | null;
  setImportSourceType: (type: 'downloaded_archives' | 'local_path') => void;
  setLocalImportPath: (path: string) => void;
  toggleImportClass: (className: string) => void;
  selectAllImportClasses: () => void;
  clearImportClasses: () => void;
  toggleSplit: (split: string) => void;
  setMaxSamplesPerClass: (limit: number) => void;
  setCreateMissingGestures: (val: boolean) => void;
  startImport: () => Promise<string | null>;
  cancelImport: (jobId: string) => Promise<void>;
  pollImportStatus: (jobId: string) => Promise<PublicJobStatusResponse | null>;

  // Dataset Combiner & Sources
  sources: DatasetSourcesResponse | null;
  combinedDatasets: CombinedDatasetSummary[];
  lastCombineResult: DatasetCombineResponse | null;
  isLoadingSources: boolean;
  isCombining: boolean;
  fetchSources: () => Promise<void>;
  fetchCombinedDatasets: () => Promise<void>;
  combineDatasets: (req: DatasetCombineRequest) => Promise<DatasetCombineResponse | null>;
}

export const usePublicDatasetStore = create<PublicDatasetStore>((set, get) => ({
  // Metadata & Info
  hagridInfo: null,
  classes: [],
  isLoadingInfo: false,

  fetchHagridInfo: async () => {
    set({ isLoadingInfo: true });
    try {
      const info = await PublicDatasetsApi.getHagridInfo();
      set({ hagridInfo: info, classes: info.classes || [], isLoadingInfo: false });
    } catch (err) {
      console.error('Failed to fetch HaGRID info:', err);
      set({ isLoadingInfo: false });
    }
  },

  // Mappings
  mappings: {},
  availableGestures: [],
  isLoadingMappings: false,
  isSavingMappings: false,

  fetchMappings: async () => {
    set({ isLoadingMappings: true });
    try {
      const res = await PublicDatasetsApi.getHagridMappings();
      set({
        mappings: res.mappings,
        availableGestures: res.available_gestures,
        isLoadingMappings: false,
      });
    } catch (err) {
      console.error('Failed to fetch HaGRID mappings:', err);
      set({ isLoadingMappings: false });
    }
  },

  updateMappingEntry: (className, update) => {
    set((state) => {
      const current = state.mappings[className];
      if (!current) return state;
      return {
        mappings: {
          ...state.mappings,
          [className]: { ...current, ...update },
        },
      };
    });
  },

  saveMappings: async () => {
    set({ isSavingMappings: true });
    try {
      const { mappings } = get();
      await PublicDatasetsApi.updateHagridMappings(mappings);
      set({ isSavingMappings: false });
      return true;
    } catch (err) {
      console.error('Failed to save mappings:', err);
      set({ isSavingMappings: false });
      return false;
    }
  },

  // Download Management
  selectedDownloadClasses: [],
  includeAnnotationsDownload: true,
  activeDownloadJob: null,

  toggleDownloadClass: (className) => {
    set((state) => {
      const exists = state.selectedDownloadClasses.includes(className);
      return {
        selectedDownloadClasses: exists
          ? state.selectedDownloadClasses.filter((c) => c !== className)
          : [...state.selectedDownloadClasses, className],
      };
    });
  },

  selectAllDownloadClasses: () => {
    const { classes } = get();
    set({ selectedDownloadClasses: classes.map((c) => c.name) });
  },

  clearDownloadClasses: () => {
    set({ selectedDownloadClasses: [] });
  },

  setIncludeAnnotationsDownload: (val) => {
    set({ includeAnnotationsDownload: val });
  },

  startDownload: async () => {
    const { selectedDownloadClasses, includeAnnotationsDownload } = get();
    if (selectedDownloadClasses.length === 0 && !includeAnnotationsDownload) {
      return null;
    }
    try {
      const res = await PublicDatasetsApi.startDownload({
        classes: selectedDownloadClasses,
        download_annotations: includeAnnotationsDownload,
      });
      // Set initial job status
      const initialStatus: PublicJobStatusResponse = {
        job_id: res.job_id,
        job_type: 'download',
        status: 'pending',
        progress_percent: 0,
        message: 'Initializing selective download...',
        details: { targets: selectedDownloadClasses, download_annotations: includeAnnotationsDownload },
        started_at: new Date().toISOString(),
        completed_at: null,
        error: null,
      };
      set({ activeDownloadJob: initialStatus });
      return res.job_id;
    } catch (err) {
      console.error('Failed to start download job:', err);
      return null;
    }
  },

  cancelDownload: async (jobId) => {
    try {
      await PublicDatasetsApi.cancelDownload(jobId);
      const current = get().activeDownloadJob;
      if (current && current.job_id === jobId) {
        set({
          activeDownloadJob: {
            ...current,
            status: 'cancelled',
            message: 'Download cancelled by user',
          },
        });
      }
    } catch (err) {
      console.error('Failed to cancel download:', err);
    }
  },

  pollDownloadStatus: async (jobId) => {
    try {
      const status = await PublicDatasetsApi.getDownloadStatus(jobId);
      set({ activeDownloadJob: status });
      if (status.status === 'completed') {
        get().fetchHagridInfo();
      }
      return status;
    } catch (err) {
      console.error('Failed to poll download status:', err);
      return null;
    }
  },

  // Ingestion & Import
  selectedImportClasses: [],
  importSourceType: 'downloaded_archives',
  localImportPath: '',
  selectedSplits: ['train', 'val', 'test'],
  maxSamplesPerClass: 500,
  createMissingGestures: true,
  activeImportJob: null,

  setImportSourceType: (type) => set({ importSourceType: type }),
  setLocalImportPath: (path) => set({ localImportPath: path }),

  toggleImportClass: (className) => {
    set((state) => {
      const exists = state.selectedImportClasses.includes(className);
      return {
        selectedImportClasses: exists
          ? state.selectedImportClasses.filter((c) => c !== className)
          : [...state.selectedImportClasses, className],
      };
    });
  },

  selectAllImportClasses: () => {
    const { classes } = get();
    set({ selectedImportClasses: classes.map((c) => c.name) });
  },

  clearImportClasses: () => {
    set({ selectedImportClasses: [] });
  },

  toggleSplit: (split) => {
    set((state) => {
      const exists = state.selectedSplits.includes(split);
      if (exists && state.selectedSplits.length === 1) return state; // keep at least 1
      return {
        selectedSplits: exists
          ? state.selectedSplits.filter((s) => s !== split)
          : [...state.selectedSplits, split],
      };
    });
  },

  setMaxSamplesPerClass: (limit) => set({ maxSamplesPerClass: limit }),
  setCreateMissingGestures: (val) => set({ createMissingGestures: val }),

  startImport: async () => {
    const {
      importSourceType,
      localImportPath,
      selectedImportClasses,
      selectedSplits,
      maxSamplesPerClass,
      createMissingGestures,
    } = get();

    try {
      const res = await PublicDatasetsApi.startImport({
        source_type: importSourceType,
        local_path: importSourceType === 'local_path' ? localImportPath : undefined,
        classes: selectedImportClasses.length > 0 ? selectedImportClasses : undefined,
        splits: selectedSplits,
        max_samples_per_class: maxSamplesPerClass,
        create_missing_gestures: createMissingGestures,
      });

      const initialStatus: PublicJobStatusResponse = {
        job_id: res.job_id,
        job_type: 'import',
        status: 'pending',
        progress_percent: 0,
        message: 'Initializing annotation import...',
        details: { source_type: importSourceType, splits: selectedSplits },
        started_at: new Date().toISOString(),
        completed_at: null,
        error: null,
      };
      set({ activeImportJob: initialStatus });
      return res.job_id;
    } catch (err) {
      console.error('Failed to start import:', err);
      return null;
    }
  },

  cancelImport: async (jobId) => {
    try {
      await PublicDatasetsApi.cancelImport(jobId);
      const current = get().activeImportJob;
      if (current && current.job_id === jobId) {
        set({
          activeImportJob: {
            ...current,
            status: 'cancelled',
            message: 'Import cancelled by user',
          },
        });
      }
    } catch (err) {
      console.error('Failed to cancel import:', err);
    }
  },

  pollImportStatus: async (jobId) => {
    try {
      const status = await PublicDatasetsApi.getImportStatus(jobId);
      set({ activeImportJob: status });
      if (status.status === 'completed') {
        get().fetchHagridInfo();
        get().fetchSources();
      }
      return status;
    } catch (err) {
      console.error('Failed to poll import status:', err);
      return null;
    }
  },

  // Dataset Combiner & Sources
  sources: null,
  combinedDatasets: [],
  lastCombineResult: null,
  isLoadingSources: false,
  isCombining: false,

  fetchSources: async () => {
    set({ isLoadingSources: true });
    try {
      const sources = await PublicDatasetsApi.getDatasetSources();
      set({ sources, isLoadingSources: false });
    } catch (err) {
      console.error('Failed to fetch dataset sources:', err);
      set({ isLoadingSources: false });
    }
  },

  fetchCombinedDatasets: async () => {
    try {
      const res = await PublicDatasetsApi.getCombinedDatasets();
      set({ combinedDatasets: res.combined_datasets || [] });
    } catch (err) {
      console.error('Failed to fetch combined datasets:', err);
    }
  },

  combineDatasets: async (req) => {
    set({ isCombining: true });
    try {
      const res = await PublicDatasetsApi.combineDatasets(req);
      set({ lastCombineResult: res, isCombining: false });
      get().fetchCombinedDatasets();
      return res;
    } catch (err) {
      console.error('Failed to combine datasets:', err);
      set({ isCombining: false });
      return null;
    }
  },
}));
