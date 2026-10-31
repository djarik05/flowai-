import React from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Database,
  RefreshCw,
  Sparkles,
  HelpCircle,
} from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

export const DatasetReadinessCard: React.FC = () => {
  const {
    readiness,
    isLoadingReadiness,
    isSeeding,
    fetchReadiness,
    seedDemoDataset,
  } = useClassifierStore();

  React.useEffect(() => {
    fetchReadiness();
  }, [fetchReadiness]);

  const isReady = readiness?.is_training_ready ?? false;
  const imbalanceRatio = readiness?.class_imbalance_ratio ?? 0;

  return (
    <Card className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5 pb-4 border-b border-[rgba(148,180,210,0.12)]">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-[#48DDF5]" />
            <h3 className="text-base font-bold text-white tracking-wide">
              Module A: Dataset Readiness Audit
            </h3>
            {readiness && (
              <Badge variant={isReady ? 'green' : 'error'}>
                {isReady ? 'Ready to Train' : 'Training Blocked (< 2 Valid Classes)'}
              </Badge>
            )}
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Validates disk samples, enforces 3D landmark schemas (63-dim), detects missing coordinates, and verifies class balance.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            variant="outline"
            onClick={() => fetchReadiness()}
            disabled={isLoadingReadiness}
            className="text-xs flex items-center gap-1.5 border-[rgba(72,221,245,0.3)] text-[#48DDF5] hover:bg-[#48DDF5]/10"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingReadiness ? 'animate-spin' : ''}`} />
            Refresh Audit
          </Button>

          <Button
            size="sm"
            variant="primary"
            onClick={() => seedDemoDataset()}
            disabled={isSeeding || isLoadingReadiness}
            className="text-xs flex items-center gap-1.5 bg-gradient-to-r from-[#00E5FF] to-[#0091FF] text-black font-semibold shadow-md shadow-[#00E5FF]/20"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin' : ''}`} />
            {isSeeding ? 'Seeding Samples...' : 'Seed Standard Gestures'}
          </Button>
        </div>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Ready Classes
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {readiness?.ready_classes_count ?? 0}
            </span>
            <span className="text-xs text-[#6B7280]">/ {readiness?.total_gestures ?? 0} total</span>
          </div>
          <span className="text-[10px] text-[#00E5FF] mt-0.5 block">Minimum 2 required</span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Valid Samples
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-[#00E5FF]">
              {readiness?.valid_samples ?? 0}
            </span>
            <span className="text-xs text-[#6B7280]">/ {readiness?.total_samples ?? 0} total</span>
          </div>
          <span className="text-[10px] text-[#10B981] mt-0.5 block">
            {readiness?.invalid_samples ? `${readiness.invalid_samples} invalid rejected` : '0 invalid'}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Class Imbalance
          </span>
          <div className="flex items-baseline gap-1.5">
            <span
              className={`text-2xl font-bold font-mono ${
                imbalanceRatio > 5
                  ? 'text-[#EF4444]'
                  : imbalanceRatio > 3
                  ? 'text-[#F59E0B]'
                  : 'text-[#10B981]'
              }`}
            >
              {imbalanceRatio.toFixed(2)} : 1
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">
            {imbalanceRatio > 3 ? 'High imbalance warning' : 'Balanced distribution'}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Min Samples / Class
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold font-mono text-white">
              {readiness?.min_samples_per_class ?? 5}
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Threshold for training</span>
        </div>
      </div>

      {/* Warnings Banner if not ready */}
      {readiness && !isReady && (
        <div className="mb-4 p-3.5 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-[#EF4444] shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-semibold text-[#EF4444] block">Training Blocked:</span>
            <p className="text-[#FCA5A5] mt-0.5">{readiness.summary}</p>
            {readiness.warnings.length > 0 && (
              <ul className="list-disc list-inside mt-1.5 space-y-0.5 text-[#FCA5A5]/90">
                {readiness.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            )}
            <p className="text-[#91A4B8] mt-2">
              Tip: Click <strong className="text-white">"Seed Standard Gestures"</strong> above to generate verified 3D samples for Closed Fist, Thumbs Up, Peace Sign, and Pointing gestures.
            </p>
          </div>
        </div>
      )}

      {/* Gesture Classes Table */}
      <div className="overflow-x-auto rounded-xl border border-[rgba(148,180,210,0.12)] bg-[#090E17]">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-[#111928] text-[#91A4B8] font-semibold border-b border-[rgba(148,180,210,0.12)]">
              <th className="py-2.5 px-3">Gesture ID</th>
              <th className="py-2.5 px-3">Gesture Name</th>
              <th className="py-2.5 px-3">Valid Samples</th>
              <th className="py-2.5 px-3">Schema</th>
              <th className="py-2.5 px-3">Handedness</th>
              <th className="py-2.5 px-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(148,180,210,0.06)]">
            {(!readiness || readiness.classes.length === 0) && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-[#91A4B8]">
                  No registered gestures found on disk.
                </td>
              </tr>
            )}
            {readiness?.classes.map((cls) => {
              const rightCount = cls.handedness_distribution['Right'] || 0;
              const leftCount = cls.handedness_distribution['Left'] || 0;

              return (
                <tr key={cls.gesture_id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-2.5 px-3 font-mono font-medium text-[#00E5FF]">
                    {cls.gesture_id}
                  </td>
                  <td className="py-2.5 px-3 font-medium text-white">{cls.gesture_name}</td>
                  <td className="py-2.5 px-3">
                    <span className="font-mono font-semibold text-white">
                      {cls.valid_sample_count}
                    </span>
                    <span className="text-[#6B7280] ml-1">/ {cls.sample_count}</span>
                    {cls.invalid_sample_count > 0 && (
                      <span className="text-[#EF4444] text-[10px] ml-1.5">
                        ({cls.invalid_sample_count} invalid)
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium ${
                        cls.coordinate_schema === '3D'
                          ? 'bg-[#10B981]/20 text-[#10B981]'
                          : 'bg-[#F59E0B]/20 text-[#F59E0B]'
                      }`}
                    >
                      {cls.coordinate_schema} (63-dim)
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-[#91A4B8] font-mono text-[11px]">
                    R: {rightCount} | L: {leftCount}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    {cls.is_ready ? (
                      <span className="inline-flex items-center gap-1 text-[#10B981] font-medium text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[#F59E0B] font-medium text-[11px]">
                        <AlertTriangle className="w-3.5 h-3.5" /> Needs &gt;= 5
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
