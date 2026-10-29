// Activity events type definitions

export type EventCategory =
  | 'application'
  | 'camera'
  | 'gesture'
  | 'controller'
  | 'model'
  | 'settings';

export type EventStatus = 'info' | 'success' | 'warning' | 'error';

export interface ActivityEvent {
  id: string;
  timestamp: string; // ISO string or formatted time
  category: EventCategory;
  description: string;
  status: EventStatus;
  details?: Record<string, unknown> | string;
  isSimulated: boolean;
}

export interface ActivityFilter {
  category?: EventCategory | 'all';
  searchQuery?: string;
  status?: EventStatus | 'all';
}
