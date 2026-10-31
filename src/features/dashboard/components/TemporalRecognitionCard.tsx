import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  Zap,
  RotateCcw,
  Sparkles,
  Layers,
  Circle,
  Radio,
} from 'lucide-react';
import { useTemporalStore } from '../../../store/temporalStore';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export const TemporalRecognitionCard: React.FC = () => {
  const {
    engineStatus,
    latestEvent,
    recentEvents,
    rightTelemetry,
    isPolling,
    startPolling,
    stopPolling,
    resetEngine,
  } = useTemporalStore();

  useEffect(() => {
    startPolling(250);
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  const telem = rightTelemetry;
  const state = telem?.state || 'IDLE';
  const speed = telem?.velocity?.speed || 0.0;
  const direction = telem?.direction || 'none';
  const linearity = telem?.linearity || 1.0;
  const durationMs = telem?.duration_ms || 0.0;

  const renderDirectionIcon = () => {
    switch (direction) {
      case 'left':
        return <ArrowLeft className="w-5 h-5 text-[#00E5FF] animate-pulse" />;
      case 'right':
        return <ArrowRight className="w-5 h-5 text-[#00E5FF] animate-pulse" />;
      case 'up':
        return <ArrowUp className="w-5 h-5 text-[#00E5FF] animate-pulse" />;
      case 'down':
        return <ArrowDown className="w-5 h-5 text-[#00E5FF] animate-pulse" />;
      default:
        return <Radio className="w-5 h-5 text-[#91A4B8]" />;
    }
  };

  const getBadgeVariant = () => {
    switch (state) {
      case 'RECOGNIZED':
        return 'green';
      case 'TRACKING':
        return 'cyan';
      case 'CANDIDATE':
        return 'blue';
      case 'COOLDOWN':
        return 'warning';
      default:
        return 'muted';
    }
  };

  return (
    <Card variant="glow" className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/90 backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[rgba(148,180,210,0.12)]">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#48DDF5]" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
            Phase 5: Temporal Gesture Engine
          </h3>
          <Badge variant={getBadgeVariant()}>{state}</Badge>
        </div>

        <button
          onClick={() => resetEngine()}
          className="text-[#91A4B8] hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
          title="Reset Movement Engine"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Dynamic Gesture Display */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 p-4 rounded-xl bg-[#111928]/80 border border-[rgba(148,180,210,0.1)]">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-[#00E5FF]/10 border border-[#00E5FF]/30 flex items-center justify-center">
            {renderDirectionIcon()}
          </div>

          <div>
            <div className="text-[11px] font-mono text-[#91A4B8] uppercase">
              Current Motion &bull; Direction: <span className="text-[#00E5FF] font-semibold">{direction.toUpperCase()}</span>
            </div>
            <div className="text-xl font-extrabold text-white flex items-center gap-2 mt-0.5">
              <span>{latestEvent ? latestEvent.gesture_name : state === 'TRACKING' ? 'Tracking Trajectory...' : 'Hand Steady'}</span>
              {latestEvent && (
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30">
                  {latestEvent.gesture_id}
                </span>
              )}
            </div>
            <div className="text-[11px] text-[#91A4B8] mt-0.5">
              {latestEvent
                ? `Triggered in ${latestEvent.duration_ms} ms • Velocity: ${latestEvent.velocity} u/s`
                : 'Recognizes Swipes (L/R/U/D), Wave, and Circle across consecutive frames.'}
            </div>
          </div>
        </div>

        {/* Confidence or Speed Gauge */}
        <div className="sm:text-right min-w-[130px]">
          <div className="text-xs text-[#91A4B8] mb-1 font-mono">
            {latestEvent ? 'Confidence' : 'Velocity'}
          </div>
          <div className="text-xl font-bold font-mono text-[#00E5FF]">
            {latestEvent ? `${Math.round(latestEvent.confidence * 100)}%` : `${speed.toFixed(2)} u/s`}
          </div>
          <div className="w-full bg-[#090E17] h-1.5 rounded-full mt-1.5 overflow-hidden border border-white/10">
            <motion.div
              className="h-full bg-gradient-to-r from-[#00E5FF] to-[#10B981]"
              animate={{
                width: `${Math.min(100, Math.round((latestEvent ? latestEvent.confidence : speed / 1.5) * 100))}%`,
              }}
              transition={{ ease: 'easeOut', duration: 0.2 }}
            />
          </div>
        </div>
      </div>

      {/* Real-time Kinematics Grid */}
      <div className="grid grid-cols-3 gap-2.5 mb-4">
        <div className="p-2.5 rounded-xl bg-[#090E17] border border-[rgba(148,180,210,0.08)]">
          <span className="text-[10px] text-[#91A4B8] uppercase block">Instant Speed</span>
          <span className="text-sm font-mono font-bold text-white">
            {speed.toFixed(2)} <span className="text-[10px] text-[#6B7280]">u/s</span>
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[#090E17] border border-[rgba(148,180,210,0.08)]">
          <span className="text-[10px] text-[#91A4B8] uppercase block">Linearity</span>
          <span className="text-sm font-mono font-bold text-[#00E5FF]">
            {(linearity * 100).toFixed(0)}%
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[#090E17] border border-[rgba(148,180,210,0.08)]">
          <span className="text-[10px] text-[#91A4B8] uppercase block">Buffer Time</span>
          <span className="text-sm font-mono font-bold text-white">
            {durationMs.toFixed(0)} <span className="text-[10px] text-[#6B7280]">ms</span>
          </span>
        </div>
      </div>

      {/* Live Dynamic Event History Stream */}
      <div className="mt-3 pt-3 border-t border-[rgba(148,180,210,0.12)]">
        <div className="flex items-center justify-between text-xs text-[#91A4B8] mb-2 font-mono">
          <span className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-[#00E5FF]" />
            Recent Temporal Events ({recentEvents.length})
          </span>
          <span className="text-[10px] text-[#6B7280]">Latest on top</span>
        </div>

        <div className="space-y-1.5 max-h-32 overflow-y-auto font-mono text-xs pr-1">
          {recentEvents.length === 0 ? (
            <div className="text-[11px] text-[#6B7280] py-2 text-center">
              No dynamic gestures triggered yet. Perform a quick swipe or wave in front of the camera.
            </div>
          ) : (
            [...recentEvents].reverse().slice(0, 4).map((ev) => (
              <div
                key={ev.event_id}
                className="flex items-center justify-between p-2 rounded-lg bg-[#090E17] border border-[rgba(148,180,210,0.08)] text-[11px]"
              >
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#00E5FF]">{ev.gesture_id}</span>
                  <span className="text-white">{ev.gesture_name}</span>
                </div>
                <div className="flex items-center gap-2 text-[#91A4B8]">
                  <span className="text-[#10B981] font-semibold">{Math.round(ev.confidence * 100)}%</span>
                  <span>&bull;</span>
                  <span>{ev.duration_ms}ms</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  );
};
