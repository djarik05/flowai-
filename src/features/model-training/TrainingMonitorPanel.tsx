import React, { useRef, useEffect } from 'react';
import { Activity, Terminal, CheckCircle2, AlertOctagon, Clock } from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const TrainingMonitorPanel: React.FC = () => {
  const { currentJob, isTraining } = useClassifierStore();
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentJob?.logs]);

  if (!currentJob && !isTraining) {
    return (
      <Card className="p-6 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-5 h-5 text-[#48DDF5]" />
          <h3 className="text-base font-bold text-white tracking-wide">
            Module C: Training Engine Monitor
          </h3>
        </div>
        <div className="py-10 text-center text-[#91A4B8] text-xs">
          No training session active. Configure hyperparameters above and click "Start Neural Training".
        </div>
      </Card>
    );
  }

  const status = currentJob?.status || (isTraining ? 'training' : 'idle');
  const currentEpoch = currentJob?.current_epoch ?? 0;
  const totalEpochs = currentJob?.total_epochs ?? 40;
  const progressPercent = currentJob?.progress_percent ?? 0;
  const history = currentJob?.metrics_history ?? [];

  // SVG Chart points calculation
  const chartW = 380;
  const chartH = 130;

  const maxLoss = Math.max(
    2.0,
    ...history.map((h) => Math.max(h.train_loss || 0, h.val_loss || 0))
  );

  const getLossPoints = (key: 'train_loss' | 'val_loss') => {
    if (history.length === 0) return '';
    return history
      .map((m) => {
        const x = (m.epoch / Math.max(1, totalEpochs)) * chartW;
        const val = m[key] || 0;
        const y = chartH - (Math.min(maxLoss, val) / maxLoss) * (chartH - 20) - 10;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const getAccPoints = (key: 'train_accuracy' | 'val_accuracy') => {
    if (history.length === 0) return '';
    return history
      .map((m) => {
        const x = (m.epoch / Math.max(1, totalEpochs)) * chartW;
        const val = m[key] || 0;
        const y = chartH - (val / 100) * (chartH - 20) - 10;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  };

  return (
    <Card className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[rgba(148,180,210,0.12)]">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[#48DDF5]" />
          <h3 className="text-base font-bold text-white tracking-wide">
            Module C: Training Engine Monitor
          </h3>
          <Badge
            variant={
              status === 'completed'
                ? 'green'
                : status === 'training'
                ? 'cyan'
                : status === 'failed'
                ? 'error'
                : 'muted'
            }
          >
            {status.toUpperCase()}
          </Badge>
        </div>

        <div className="flex items-center gap-3 text-xs text-[#91A4B8]">
          <span className="font-mono">
            Epoch <strong className="text-white">{currentEpoch}</strong> / {totalEpochs}
          </span>
          <span className="font-mono text-[#00E5FF]">{progressPercent.toFixed(1)}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-[#111928] h-2 rounded-full overflow-hidden mb-5 border border-[rgba(148,180,210,0.1)]">
        <div
          className="h-full bg-gradient-to-r from-[#00E5FF] to-[#10B981] transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Real-time Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] text-[#91A4B8] uppercase block mb-1">Train Loss</span>
          <span className="text-xl font-bold font-mono text-[#00E5FF]">
            {currentJob?.latest_train_loss !== undefined && currentJob?.latest_train_loss !== null
              ? currentJob.latest_train_loss.toFixed(4)
              : '---'}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] text-[#91A4B8] uppercase block mb-1">Val Loss</span>
          <span className="text-xl font-bold font-mono text-[#F59E0B]">
            {currentJob?.latest_val_loss !== undefined && currentJob?.latest_val_loss !== null
              ? currentJob.latest_val_loss.toFixed(4)
              : '---'}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] text-[#91A4B8] uppercase block mb-1">Train Accuracy</span>
          <span className="text-xl font-bold font-mono text-[#00E5FF]">
            {currentJob?.latest_train_accuracy !== undefined && currentJob?.latest_train_accuracy !== null
              ? `${currentJob.latest_train_accuracy.toFixed(1)}%`
              : '---'}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] text-[#91A4B8] uppercase block mb-1">Val Accuracy</span>
          <span className="text-xl font-bold font-mono text-[#10B981]">
            {currentJob?.latest_val_accuracy !== undefined && currentJob?.latest_val_accuracy !== null
              ? `${currentJob.latest_val_accuracy.toFixed(1)}%`
              : '---'}
          </span>
        </div>
      </div>

      {/* SVG Charts: Loss and Accuracy */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        {/* Loss Curve */}
        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-white">Cross-Entropy Loss</span>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1 text-[#00E5FF]">
                <span className="w-2 h-2 rounded-full bg-[#00E5FF]" /> Train
              </span>
              <span className="flex items-center gap-1 text-[#F59E0B]">
                <span className="w-2 h-2 rounded-full bg-[#F59E0B]" /> Val
              </span>
            </div>
          </div>
          <div className="w-full h-[140px] flex items-center justify-center bg-[#090E17] rounded-lg p-2 border border-[rgba(148,180,210,0.06)]">
            {history.length > 1 ? (
              <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full h-full overflow-visible">
                <line x1="0" y1={chartH - 10} x2={chartW} y2={chartH - 10} stroke="#374151" strokeDasharray="3,3" />
                <line x1="0" y1="10" x2={chartW} y2="10" stroke="#374151" strokeDasharray="3,3" />
                <polyline fill="none" stroke="#00E5FF" strokeWidth="2" points={getLossPoints('train_loss')} />
                <polyline fill="none" stroke="#F59E0B" strokeWidth="2" points={getLossPoints('val_loss')} />
              </svg>
            ) : (
              <span className="text-[11px] text-[#6B7280]">Accumulating epoch loss data...</span>
            )}
          </div>
        </div>

        {/* Accuracy Curve */}
        <div className="p-3.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-white">Classification Accuracy (%)</span>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1 text-[#00E5FF]">
                <span className="w-2 h-2 rounded-full bg-[#00E5FF]" /> Train
              </span>
              <span className="flex items-center gap-1 text-[#10B981]">
                <span className="w-2 h-2 rounded-full bg-[#10B981]" /> Val
              </span>
            </div>
          </div>
          <div className="w-full h-[140px] flex items-center justify-center bg-[#090E17] rounded-lg p-2 border border-[rgba(148,180,210,0.06)]">
            {history.length > 1 ? (
              <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full h-full overflow-visible">
                <line x1="0" y1={chartH - 10} x2={chartW} y2={chartH - 10} stroke="#374151" strokeDasharray="3,3" />
                <line x1="0" y1="10" x2={chartW} y2="10" stroke="#374151" strokeDasharray="3,3" />
                <polyline fill="none" stroke="#00E5FF" strokeWidth="2" points={getAccPoints('train_accuracy')} />
                <polyline fill="none" stroke="#10B981" strokeWidth="2" points={getAccPoints('val_accuracy')} />
              </svg>
            ) : (
              <span className="text-[11px] text-[#6B7280]">Accumulating epoch accuracy data...</span>
            )}
          </div>
        </div>
      </div>

      {/* Terminal Log Console */}
      <div className="rounded-xl bg-[#090E17] border border-[rgba(148,180,210,0.12)] p-3">
        <div className="flex items-center justify-between mb-2 pb-2 border-b border-[rgba(148,180,210,0.08)]">
          <div className="flex items-center gap-1.5 text-xs text-[#91A4B8]">
            <Terminal className="w-3.5 h-3.5 text-[#00E5FF]" />
            <span className="font-mono">Training Engine Console Output</span>
          </div>
          <span className="text-[10px] text-[#6B7280] font-mono">
            Job ID: {currentJob?.job_id || '---'}
          </span>
        </div>
        <div className="max-h-36 overflow-y-auto font-mono text-[11px] text-[#91A4B8] space-y-1">
          {(!currentJob?.logs || currentJob.logs.length === 0) && (
            <div className="text-[#6B7280]">Awaiting worker log messages...</div>
          )}
          {currentJob?.logs?.map((line, idx) => (
            <div
              key={idx}
              className={`${
                line.includes('Error') || line.includes('Failed')
                  ? 'text-[#EF4444]'
                  : line.includes('completed') || line.includes('Registered')
                  ? 'text-[#10B981]'
                  : 'text-[#D1D5DB]'
              }`}
            >
              {line}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </div>
    </Card>
  );
};
