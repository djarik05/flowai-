import React, { useMemo } from 'react';
import {
  ScrollText,
  Search,
  Filter,
  Download,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Info,
  AlertTriangle,
  Camera,
  Activity,
  Cpu,
  MousePointer,
  Settings,
  Sparkles,
} from 'lucide-react';
import { useActivityStore } from '../../store/activityStore';
import { EventCategory, EventStatus } from '../../types/events';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge, BadgeVariant } from '../../components/ui/Badge';

const CATEGORY_ICONS: Record<EventCategory, React.ComponentType<{ className?: string }>> = {
  application: Sparkles,
  camera: Camera,
  gesture: Activity,
  controller: MousePointer,
  model: Cpu,
  settings: Settings,
};

const STATUS_VARIANTS: Record<EventStatus, BadgeVariant> = {
  info: 'cyan',
  success: 'green',
  warning: 'warning',
  error: 'error',
};

export const ActivityLogsView: React.FC = () => {
  const {
    logs,
    filterCategory,
    searchQuery,
    filterStatus,
    setCategoryFilter,
    setSearchQuery,
    setStatusFilter,
    clearLogs,
    exportLogsAsJson,
  } = useActivityStore();

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (filterCategory !== 'all' && log.category !== filterCategory) return false;
      if (filterStatus !== 'all' && log.status !== filterStatus) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          log.description.toLowerCase().includes(q) ||
          log.category.toLowerCase().includes(q) ||
          (log.details && JSON.stringify(log.details).toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [logs, filterCategory, filterStatus, searchQuery]);

  return (
    <div className="w-full flex flex-col gap-6 select-none">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass rounded-2xl p-5 border border-[rgba(148,180,210,0.18)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ScrollText className="w-5 h-5 text-[#48DDF5]" />
            <h2 className="text-lg font-bold text-white">System Activity Journal</h2>
            <Badge variant="cyan">Simulated Log Stream</Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            Audit trail of vision pipeline events, gesture triggers, controller changes, and warnings.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={exportLogsAsJson}
            icon={<Download className="w-3.5 h-3.5" />}
          >
            Export JSON
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={clearLogs}
            icon={<Trash2 className="w-3.5 h-3.5 text-[#FF647C]" />}
          >
            Clear
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card variant="glass" className="p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-[#91A4B8] absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search events, gestures, payloads..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.18)] rounded-xl pl-9 pr-3.5 py-2 text-xs text-[#F1F5F9] focus:outline-none focus:border-[#48DDF5]"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto scrollbar-none py-1">
          {(['all', 'application', 'camera', 'gesture', 'controller', 'model', 'settings'] as const).map(
            (cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all capitalize whitespace-nowrap cursor-pointer ${
                  filterCategory === cat
                    ? 'bg-[rgba(72,221,245,0.15)] text-[#48DDF5] border border-[rgba(72,221,245,0.3)]'
                    : 'text-[#91A4B8] hover:text-white border border-transparent'
                }`}
              >
                {cat}
              </button>
            )
          )}
        </div>
      </Card>

      {/* Logs Table / List Card */}
      <Card variant="glass-strong" className="p-6">
        <div className="flex items-center justify-between pb-3 border-b border-[rgba(148,180,210,0.12)] mb-4 text-xs text-[#91A4B8]">
          <span>Displaying {filteredLogs.length} events</span>
          <span>Max Ring Buffer: 150 events</span>
        </div>

        {filteredLogs.length === 0 ? (
          <div className="py-12 text-center text-xs text-[#61758B]">
            No activity logs match the selected search query or category filter.
          </div>
        ) : (
          <div className="space-y-2">
            {filteredLogs.map((log) => {
              const Icon = CATEGORY_ICONS[log.category] || Activity;

              return (
                <div
                  key={log.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] gap-3 hover:border-[rgba(72,221,245,0.25)] transition-colors"
                >
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="p-2 rounded-lg bg-[rgba(18,29,45,0.8)] border border-[rgba(148,180,210,0.15)] text-[#48DDF5] shrink-0 mt-0.5 sm:mt-0">
                      <Icon className="w-4 h-4" />
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[11px] font-mono text-[#91A4B8]">{log.timestamp}</span>
                        <Badge variant={STATUS_VARIANTS[log.status]} className="text-[10px] uppercase">
                          {log.category}
                        </Badge>
                      </div>
                      <p className="text-xs text-[#F1F5F9] font-medium">{log.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    {log.details && (
                      <span className="text-[10px] font-mono text-[#91A4B8] bg-[rgba(7,11,18,0.7)] px-2 py-0.5 rounded border border-[rgba(148,180,210,0.1)] max-w-[200px] truncate">
                        {typeof log.details === 'string' ? log.details : JSON.stringify(log.details)}
                      </span>
                    )}
                    <Badge variant={STATUS_VARIANTS[log.status]} dot>
                      {log.status}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};
