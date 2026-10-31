import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  Camera,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Activity,
  Sliders,
  ChevronRight,
} from 'lucide-react';
import { GestureDefinition } from '../../../types/gesture';
import { useDatasetStore } from '../../../store/datasetStore';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

const CameraSection = React.lazy(() =>
  import('../../../components/camera/CameraSection').then((m) => ({ default: m.CameraSection }))
);

const CameraLoadingFallback: React.FC = () => (
  <div className="w-full h-[480px] rounded-2xl glass border border-[rgba(148,180,210,0.16)] flex flex-col items-center justify-center gap-3">
    <div className="relative w-8 h-8 flex items-center justify-center">
      <div className="absolute inset-0 rounded-full border-2 border-[rgba(72,221,245,0.15)] border-t-[#48DDF5] animate-spin" />
    </div>
    <span className="text-xs text-[#91A4B8] font-mono">Initializing Camera Workspace...</span>
  </div>
);

interface CollectionStudioTabProps {
  gestures: GestureDefinition[];
  selectedGestureId: string;
  onSelectGestureId: (id: string) => void;
  onCollectionComplete?: () => void;
}

export const CollectionStudioTab: React.FC<CollectionStudioTabProps> = ({
  gestures,
  selectedGestureId,
  onSelectGestureId,
  onCollectionComplete,
}) => {
  const {
    collectionStatus,
    startCollection,
    pauseCollection,
    resumeCollection,
    stopCollection,
    pollCollectionStatus,
  } = useDatasetStore();

  const [targetSamples, setTargetSamples] = useState<number>(50);
  const [sampleIntervalMs, setSampleIntervalMs] = useState<number>(80);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const pollIntervalRef = useRef<number | null>(null);

  // Poll collection status while active
  useEffect(() => {
    const isLive =
      collectionStatus.state === 'collecting' || collectionStatus.state === 'paused';

    if (isLive) {
      pollIntervalRef.current = window.setInterval(async () => {
        const latest = await pollCollectionStatus();
        if (latest?.state === 'completed') {
          if (onCollectionComplete) onCollectionComplete();
        }
      }, 400);
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [collectionStatus.state, pollCollectionStatus, onCollectionComplete]);

  const activeGesture = gestures.find((g) => g.id === selectedGestureId) || gestures[0];

  const handleStart = async () => {
    if (!activeGesture) {
      setErrorMessage('Please select a gesture first.');
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await startCollection(activeGesture.id, targetSamples, sampleIntervalMs);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to start collection session');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePause = async () => {
    await pauseCollection();
  };

  const handleResume = async () => {
    await resumeCollection();
  };

  const handleStop = async () => {
    await stopCollection();
  };

  const isCollecting = collectionStatus.state === 'collecting';
  const isPaused = collectionStatus.state === 'paused';
  const isCompleted = collectionStatus.state === 'completed';

  return (
    <div className="flex flex-col gap-6">
      {/* Studio Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.14)]">
        {/* Left: Gesture Selector */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <span className="text-[10px] text-[#91A4B8] uppercase font-mono tracking-wider">
              Target Gesture
            </span>
            <select
              value={selectedGestureId || activeGesture?.id || ''}
              onChange={(e) => onSelectGestureId(e.target.value)}
              disabled={isCollecting || isPaused}
              className="mt-1 px-3 py-1.5 rounded-lg bg-[rgba(18,29,45,0.9)] border border-[rgba(148,180,210,0.25)] text-sm font-bold text-white focus:outline-none focus:border-[#48DDF5] cursor-pointer disabled:opacity-60"
            >
              {gestures.map((g) => (
                <option key={g.id} value={g.id} className="bg-[#0B1220]">
                  {g.name} ({g.id}) - {g.sampleCount ?? g.sample_count ?? 0} samples
                </option>
              ))}
            </select>
          </div>

          {activeGesture && (
            <Badge variant="cyan" className="self-end mb-1">
              {activeGesture.type}
            </Badge>
          )}
        </div>

        {/* Center: Target Samples & Interval Config */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#91A4B8]">Target:</span>
            <div className="flex items-center gap-1">
              {[30, 50, 100, 200].map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => setTargetSamples(count)}
                  disabled={isCollecting || isPaused}
                  className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium transition-all ${
                    targetSamples === count
                      ? 'bg-[#48DDF5] text-[#070B12] font-bold'
                      : 'bg-[rgba(18,29,45,0.7)] text-[#91A4B8] hover:text-white'
                  } disabled:opacity-50`}
                >
                  {count}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#91A4B8]">Interval:</span>
            <select
              value={sampleIntervalMs}
              onChange={(e) => setSampleIntervalMs(Number(e.target.value))}
              disabled={isCollecting || isPaused}
              className="px-2 py-1 rounded-md bg-[rgba(18,29,45,0.9)] border border-[rgba(148,180,210,0.2)] text-xs font-mono text-white focus:outline-none focus:border-[#48DDF5] disabled:opacity-50"
            >
              <option value={50} className="bg-[#0B1220]">50 ms (Fast)</option>
              <option value={80} className="bg-[#0B1220]">80 ms (Recommended)</option>
              <option value={120} className="bg-[#0B1220]">120 ms (Smooth)</option>
              <option value={200} className="bg-[#0B1220]">200 ms (Steady)</option>
            </select>
          </div>
        </div>

        {/* Right: State Badge */}
        <div>
          <Badge
            variant={
              isCollecting
                ? 'green'
                : isPaused
                ? 'warning'
                : isCompleted
                ? 'cyan'
                : 'muted'
            }
            dot
          >
            {isCollecting
              ? 'Collecting...'
              : isPaused
              ? 'Collection Paused'
              : isCompleted
              ? 'Collection Completed'
              : 'Studio Ready'}
          </Badge>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-[rgba(255,100,124,0.12)] border border-[rgba(255,100,124,0.3)] text-xs text-[#FF647C] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-[#FF647C] hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Studio Viewport: Camera Section + Real-Time Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Camera Feed & Real-time Hand Detection (Col 8) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <React.Suspense fallback={<CameraLoadingFallback />}>
            <CameraSection />
          </React.Suspense>
        </div>

        {/* Right: Live Collection Controls & Metrics (Col 4) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Progress Card */}
          <Card variant="glass-strong" className="p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#42F5A5]" />
                Collection Progress
              </h4>
              {collectionStatus.session_id && (
                <span className="text-[10px] font-mono text-[#91A4B8] bg-[rgba(18,29,45,0.8)] px-2 py-0.5 rounded">
                  {collectionStatus.session_id.slice(0, 14)}...
                </span>
              )}
            </div>

            {/* Circular or Bar Progress Indicator */}
            <div className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="text-2xl font-bold text-white">
                  {collectionStatus.collected_samples}{' '}
                  <span className="text-xs text-[#91A4B8] font-normal">
                    / {collectionStatus.target_samples}
                  </span>
                </span>
                <span className="text-sm font-bold text-[#48DDF5]">
                  {collectionStatus.progress_pct.toFixed(0)}%
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-3 rounded-full bg-[rgba(18,29,45,0.9)] overflow-hidden border border-[rgba(148,180,210,0.15)]">
                <div
                  className="h-full bg-gradient-to-r from-[#48DDF5] to-[#42F5A5] transition-all duration-300"
                  style={{ width: `${Math.min(100, collectionStatus.progress_pct)}%` }}
                />
              </div>
            </div>

            {/* Telemetry Metrics */}
            <div className="grid grid-cols-2 gap-2.5 pt-2 border-t border-[rgba(148,180,210,0.1)] text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-[rgba(11,18,32,0.5)] border border-[rgba(148,180,210,0.08)]">
                <span className="text-[10px] text-[#61758B] uppercase block">Inference Rate</span>
                <span className="text-[#48DDF5] font-bold text-sm">
                  {collectionStatus.fps > 0 ? `${collectionStatus.fps.toFixed(1)} FPS` : '--'}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[rgba(11,18,32,0.5)] border border-[rgba(148,180,210,0.08)]">
                <span className="text-[10px] text-[#61758B] uppercase block">Hand Sensor</span>
                <span
                  className={`font-bold text-xs ${
                    collectionStatus.hand_detected
                      ? 'text-[#42F5A5]'
                      : isCollecting
                      ? 'text-[#FFEA00] animate-pulse'
                      : 'text-[#91A4B8]'
                  }`}
                >
                  {collectionStatus.hand_detected
                    ? `${collectionStatus.handedness || 'Hand'} Detected`
                    : isCollecting
                    ? 'No Hand in View'
                    : 'Standby'}
                </span>
              </div>
            </div>

            {/* Hand Presence Feedback Banner */}
            {isCollecting && (
              <div
                className={`p-2.5 rounded-lg border text-[11px] flex items-center gap-2 ${
                  collectionStatus.hand_detected
                    ? 'bg-[rgba(66,245,165,0.08)] border-[#42F5A5]/30 text-[#42F5A5]'
                    : 'bg-[rgba(255,234,0,0.08)] border-[#FFEA00]/30 text-[#FFEA00]'
                }`}
              >
                <div
                  className={`w-2 h-2 rounded-full ${
                    collectionStatus.hand_detected ? 'bg-[#42F5A5]' : 'bg-[#FFEA00] animate-ping'
                  }`}
                />
                <span>
                  {collectionStatus.hand_detected
                    ? `Tracking ${collectionStatus.handedness} hand — recording valid 21-landmark poses.`
                    : 'Hold your hand in front of the camera to begin capturing samples.'}
                </span>
              </div>
            )}

            {/* Backend Collection Error Banner */}
            {collectionStatus.last_error && (
              <div className="p-2.5 rounded-lg bg-[rgba(255,100,124,0.12)] border border-[rgba(255,100,124,0.3)] text-xs text-[#FF647C] flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{collectionStatus.last_error}</span>
              </div>
            )}

            {/* Rule Callout: Discards Invalid Frames */}
            <div className="p-2.5 rounded-lg bg-[rgba(72,221,245,0.06)] border border-[rgba(72,221,245,0.18)] text-[11px] text-[#91A4B8]">
              <span className="text-[#48DDF5] font-semibold block mb-0.5">
                Strict Quality Filter:
              </span>
              Frames with no hand detected are automatically discarded. Only complete 21-landmark poses are saved.
            </div>

            {/* Main Action Buttons */}
            <div className="flex flex-col gap-2 pt-2">
              {!isCollecting && !isPaused && (
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleStart}
                  disabled={isSubmitting}
                  icon={<Play className="w-4 h-4" />}
                  className="w-full justify-center"
                >
                  {isSubmitting ? 'Starting Session...' : 'Start Dataset Recording'}
                </Button>
              )}

              {isCollecting && (
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="secondary"
                    size="md"
                    onClick={handlePause}
                    icon={<Pause className="w-4 h-4" />}
                    className="justify-center"
                  >
                    Pause
                  </Button>
                  <Button
                    variant="danger"
                    size="md"
                    onClick={handleStop}
                    icon={<Square className="w-4 h-4" />}
                    className="justify-center"
                  >
                    Finish
                  </Button>
                </div>
              )}

              {isPaused && (
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleResume}
                    icon={<Play className="w-4 h-4" />}
                    className="justify-center"
                  >
                    Resume
                  </Button>
                  <Button
                    variant="danger"
                    size="md"
                    onClick={handleStop}
                    icon={<Square className="w-4 h-4" />}
                    className="justify-center"
                  >
                    Stop
                  </Button>
                </div>
              )}
            </div>
          </Card>

          {/* Quick Collection Guidelines Card */}
          <Card variant="glass" className="p-4 text-xs">
            <h5 className="font-bold text-white mb-2 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#48DDF5]" />
              Collection Tips for High Accuracy
            </h5>
            <ul className="text-[#91A4B8] space-y-1.5 list-disc list-inside">
              <li>Keep hand steady in center of webcam view.</li>
              <li>Collect 30–100 samples per gesture from slight angles.</li>
              <li>Ensure good room lighting without strong glare.</li>
              <li>Collect for both Left and Right hands if needed.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
};
