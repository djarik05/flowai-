import React, { useEffect } from 'react';
import {
  Database,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Play,
  TrendingUp,
  Clock,
  PieChart,
} from 'lucide-react';
import { useDatasetStore } from '../../../store/datasetStore';
import { GestureDefinition } from '../../../types/gesture';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

interface DatasetOverviewTabProps {
  gestures: GestureDefinition[];
  onSelectForCollection: (gestureId: string) => void;
}

export const DatasetOverviewTab: React.FC<DatasetOverviewTabProps> = ({
  gestures,
  onSelectForCollection,
}) => {
  const { stats, fetchStats, isLoadingStats } = useDatasetStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const totalGestures = stats?.total_gestures ?? gestures.length;
  const totalSamples = stats?.total_samples ?? 0;
  const insufficientCount = stats?.gestures_with_insufficient_samples ?? 0;
  const completionPct = stats?.completion_percentage ?? 0;
  const latestSession = stats?.latest_session_id ?? null;

  return (
    <div className="flex flex-col gap-6">
      {/* Top 4 KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Registered Gestures */}
        <Card variant="glass" className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-[#91A4B8] uppercase font-mono tracking-wider">
              Total Gestures
            </div>
            <div className="text-2xl font-bold text-white mt-1">{totalGestures}</div>
            <div className="text-[11px] text-[#48DDF5] mt-1 flex items-center gap-1 font-mono">
              <Layers className="w-3 h-3" />
              Registered classes
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[rgba(72,221,245,0.12)] border border-[rgba(72,221,245,0.25)] flex items-center justify-center text-[#48DDF5]">
            <Layers className="w-5 h-5" />
          </div>
        </Card>

        {/* Card 2: Total Collected Samples */}
        <Card variant="glass" className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-[#91A4B8] uppercase font-mono tracking-wider">
              Total Samples
            </div>
            <div className="text-2xl font-bold text-white mt-1">{totalSamples}</div>
            <div className="text-[11px] text-[#42F5A5] mt-1 flex items-center gap-1 font-mono">
              <Database className="w-3 h-3" />
              21-landmark poses
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[rgba(66,245,165,0.12)] border border-[rgba(66,245,165,0.25)] flex items-center justify-center text-[#42F5A5]">
            <Database className="w-5 h-5" />
          </div>
        </Card>

        {/* Card 3: Insufficient Samples */}
        <Card variant="glass" className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-[#91A4B8] uppercase font-mono tracking-wider">
              Needs Samples
            </div>
            <div className="text-2xl font-bold text-white mt-1">{insufficientCount}</div>
            <div className="text-[11px] text-[#FFB547] mt-1 flex items-center gap-1 font-mono">
              <AlertTriangle className="w-3 h-3" />
              &lt; 30 samples benchmark
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[rgba(255,181,71,0.12)] border border-[rgba(255,181,71,0.25)] flex items-center justify-center text-[#FFB547]">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </Card>

        {/* Card 4: Dataset Completion */}
        <Card variant="glass" className="p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-[#91A4B8] uppercase font-mono tracking-wider">
              Dataset Readiness
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {completionPct.toFixed(0)}%
            </div>
            <div className="text-[11px] text-[#48DDF5] mt-1 flex items-center gap-1 font-mono">
              <TrendingUp className="w-3 h-3" />
              Ready for training
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-[rgba(72,221,245,0.12)] border border-[rgba(72,221,245,0.25)] flex items-center justify-center text-[#48DDF5]">
            <PieChart className="w-5 h-5" />
          </div>
        </Card>
      </div>

      {/* Latest Session Callout */}
      {latestSession && (
        <div className="p-3.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.14)] flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-2 text-[#91A4B8]">
            <Clock className="w-4 h-4 text-[#48DDF5]" />
            <span>Latest Collection Session:</span>
            <span className="text-white font-bold">{latestSession}</span>
          </div>
          <Badge variant="cyan">
            Persisted
          </Badge>
        </div>
      )}

      {/* Per-Gesture Breakdown Table */}
      <Card variant="glass" className="p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#48DDF5]" />
            Per-Gesture Dataset Distribution
          </h3>
          <span className="text-xs text-[#91A4B8] font-mono">
            Benchmark: 30 samples / gesture
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-[rgba(148,180,210,0.14)] text-[10px] uppercase text-[#91A4B8]">
              <tr>
                <th className="py-2.5 px-3">Gesture ID</th>
                <th className="py-2.5 px-3">Gesture Name</th>
                <th className="py-2.5 px-3">Sample Count</th>
                <th className="py-2.5 px-3 min-w-[160px]">Benchmark Progress</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(148,180,210,0.08)]">
              {gestures.map((gesture) => {
                const count =
                  stats?.gesture_counts?.[gesture.id] ??
                  gesture.sampleCount ??
                  gesture.sample_count ??
                  0;
                const progressPct = Math.min(100, Math.round((count / 30) * 100));
                const isAdequate = count >= 30;

                return (
                  <tr
                    key={gesture.id}
                    className="hover:bg-[rgba(72,221,245,0.03)] transition-colors"
                  >
                    <td className="py-3 px-3 text-[#48DDF5] font-bold">{gesture.id}</td>
                    <td className="py-3 px-3 text-white font-medium">{gesture.name}</td>
                    <td className="py-3 px-3 font-bold">{count}</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-full h-2 rounded-full bg-[rgba(18,29,45,0.8)] overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${
                              isAdequate
                                ? 'bg-[#42F5A5]'
                                : 'bg-gradient-to-r from-[#FFB547] to-[#48DDF5]'
                            }`}
                            style={{ width: `${progressPct}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-[#91A4B8] shrink-0">
                          {progressPct}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <Badge variant={isAdequate ? 'green' : 'warning'}>
                        {isAdequate ? 'Sufficient' : 'Needs Samples'}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onSelectForCollection(gesture.id)}
                        icon={<Play className="w-3 h-3 text-[#42F5A5]" />}
                        className="py-1 px-2.5 text-xs inline-flex"
                      >
                        Collect
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
