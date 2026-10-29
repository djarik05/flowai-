import { create } from 'zustand';
import { ActivityEvent, EventCategory, EventStatus } from '../types/events';
import { INITIAL_ACTIVITY_LOGS } from '../services/demo/sampleData';

interface ActivityStore {
  logs: ActivityEvent[];
  filterCategory: EventCategory | 'all';
  searchQuery: string;
  filterStatus: EventStatus | 'all';
  
  addLog: (event: Omit<ActivityEvent, 'id' | 'timestamp'>) => void;
  setCategoryFilter: (category: EventCategory | 'all') => void;
  setSearchQuery: (query: string) => void;
  setStatusFilter: (status: EventStatus | 'all') => void;
  clearLogs: () => void;
  exportLogsAsJson: () => void;
}

export const useActivityStore = create<ActivityStore>((set, get) => ({
  logs: [...INITIAL_ACTIVITY_LOGS],
  filterCategory: 'all',
  searchQuery: '',
  filterStatus: 'all',

  addLog: (eventData) => {
    const newLog: ActivityEvent = {
      ...eventData,
      id: `log-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toLocaleTimeString(),
    };
    // Keep max 150 events
    const updated = [newLog, ...get().logs].slice(0, 150);
    set({ logs: updated });
  },

  setCategoryFilter: (category) => set({ filterCategory: category }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setStatusFilter: (status) => set({ filterStatus: status }),

  clearLogs: () => set({ logs: [] }),

  exportLogsAsJson: () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(get().logs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `gestureflow_activity_logs_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  },
}));
