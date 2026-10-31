import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Play,
  Pause,
  Sparkles,
  Activity,
  CheckCircle2,
  Clock,
  Radio,
  Zap,
  Eye,
  EyeOff,
  ShieldCheck,
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { useSettingsStore } from '../../store/settingsStore';
import { useGestureStore } from '../../store/gestureStore';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { MouseControlCard } from './components/MouseControlCard';

const CameraSection = React.lazy(() =>
  import('../../components/camera/CameraSection').then((m) => ({ default: m.CameraSection }))
);

const CameraLoadingFallback: React.FC = () => (
  <div className="w-full h-[480px] rounded-2xl glass border border-[rgba(148,180,210,0.16)] flex flex-col items-center justify-center gap-3">
    <div className="relative w-8 h-8 flex items-center justify-center">
      <div className="absolute inset-0 rounded-full border-2 border-[rgba(72,221,245,0.15)] border-t-[#48DDF5] animate-spin" />
    </div>
    <span className="text-xs text-[#91A4B8] font-mono">Initializing Camera Workspace...</span>
  </div>
);

export const DashboardView: React.FC = () => {
  const { setCurrentView, trackingStatus, setDetectedGesture, isDemoCycling, toggleDemoCycling } =
    useAppStore();
  const { settings, updateController } = useSettingsStore();
  const { gestures } = useGestureStore();

  const [activeMode, setActiveMode] = useState<'air_mouse' | 'presentation' | 'media' | 'custom'>(
    'air_mouse'
  );

  // Demo simulator gesture cycling (strictly opt-in)
  useEffect(() => {
    if (!isDemoCycling) return;

    const enabledGestures = gestures.filter((g) => g.enabled);
    if (enabledGestures.length === 0) return;

    let index = 0;
    const interval = setInterval(() => {
      index = (index + 1) % enabledGestures.length;
      const current = enabledGestures[index];
      const simulatedConfidence = Number((0.84 + Math.random() * 0.14).toFixed(2));

      setDetectedGesture({
        gestureId: current.id,
        name: current.name,
        confidence: simulatedConfidence,
        timestamp: Date.now(),
        action: current.action,
      });
    }, 2800);

    return () => clearInterval(interval);
  }, [isDemoCycling, gestures, setDetectedGesture]);

  return (
    <div className="w-full flex flex-col gap-6 select-none">
      {/* Top Banner / Mode Selector Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass rounded-2xl p-4 border border-[rgba(148,180,210,0.16)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-base font-bold text-white">Central Gesture Workspace</h2>
            <Badge variant={isDemoCycling ? "purple" : "green"} dot>
              {isDemoCycling ? "Simulated Demo" : "Live Camera AI"}
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            {isDemoCycling
              ? "Running simulated demo stream. Click 'Stop Demo' to switch to live webcam."
              : "Live MediaPipe hand tracking & real-time gesture recognition engine."}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Button
            size="sm"
            variant={isDemoCycling ? "danger" : "outline"}
            onClick={toggleDemoCycling}
            className="text-xs font-mono"
          >
            {isDemoCycling ? "Stop Demo" : "Simulate Demo"}
          </Button>

          {/* Control Mode Pills */}
          <div className="flex items-center gap-1.5 bg-[rgba(11,18,32,0.8)] p-1 rounded-xl border border-[rgba(148,180,210,0.12)]">
            {[
              { id: 'air_mouse', label: 'Air Mouse' },
              { id: 'presentation', label: 'Presentation' },
              { id: 'media', label: 'Media' },
              { id: 'custom', label: 'Custom' },
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => setActiveMode(mode.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  activeMode === mode.id
                    ? 'bg-gradient-to-r from-[#48DDF5] to-[#42F5A5] text-[#070B12] font-semibold shadow-[0_0_12px_rgba(72,221,245,0.25)]'
                    : 'text-[#91A4B8] hover:text-white'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Primary Workspace Grid: Main Tracking Camera on Left, Resized Detected Gesture on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* LARGE PRIMARY WORKSPACE: Main Tracking Preview (Col 8) */}
        <div className="lg:col-span-8 flex flex-col">
          <React.Suspense fallback={<CameraLoadingFallback />}>
            <CameraSection />
          </React.Suspense>
        </div>

        {/* RESIZED DETECTED GESTURE WORKSPACE (Col 4) */}
        <div className="lg:col-span-4 flex flex-col">
          <Card variant="glow" className="p-6 flex flex-col justify-between h-full min-h-[480px] border-[rgba(72,221,245,0.25)] bg-[rgba(7,11,18,0.75)] shadow-2xl relative overflow-hidden">
            {/* Ambient Background Radial Glow */}
            <div
              className={`absolute -top-24 -right-24 w-64 h-64 rounded-full blur-3xl pointer-events-none transition-colors duration-500 ${
                trackingStatus.currentGesture
                  ? 'bg-[rgba(66,245,165,0.12)]'
                  : trackingStatus.handDetected
                  ? 'bg-[rgba(72,221,245,0.12)]'
                  : 'bg-[rgba(148,180,210,0.04)]'
              }`}
            />

            {/* Top Bar: Title & Status Badge */}
            <div className="flex items-center justify-between pb-4 border-b border-[rgba(148,180,210,0.1)] relative z-10">
              <div className="flex items-center gap-2.5">
                <div
                  className={`p-2 rounded-xl border transition-colors ${
                    trackingStatus.currentGesture
                      ? 'bg-[rgba(66,245,165,0.15)] border-[#42F5A5]/40 text-[#42F5A5]'
                      : trackingStatus.handDetected
                      ? 'bg-[rgba(72,221,245,0.15)] border-[#48DDF5]/40 text-[#48DDF5]'
                      : 'bg-[rgba(11,18,32,0.6)] border-[rgba(148,180,210,0.12)] text-[#91A4B8]'
                  }`}
                >
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                    Detected Gesture
                    <span className="w-1.5 h-1.5 rounded-full bg-[#48DDF5]" />
                  </h3>
                  <p className="text-[10px] text-[#91A4B8]">
                    Real-time MediaPipe Hand Classifier
                  </p>
                </div>
              </div>

              {isDemoCycling ? (
                <Badge variant="purple">Simulated Demo</Badge>
              ) : trackingStatus.currentGesture ? (
                <Badge variant="green" dot>Gesture Recognized</Badge>
              ) : trackingStatus.handDetected ? (
                <Badge variant="cyan" dot>Hand Detected</Badge>
              ) : (
                <Badge variant="muted">Awaiting Hand</Badge>
              )}
            </div>

            {/* Hero Section: Large Icon + Gesture Name + Bound Action */}
            <div className="my-6 flex flex-col items-center text-center gap-4 relative z-10">
              {/* Large Animated Pose Icon Container */}
              <div
                className={`w-24 h-24 rounded-2xl flex items-center justify-center border transition-all duration-300 ${
                  trackingStatus.currentGesture
                    ? 'bg-[rgba(66,245,165,0.12)] border-[#42F5A5]/60 shadow-[0_0_24px_rgba(66,245,165,0.3)] ring-2 ring-[#42F5A5]/30'
                    : trackingStatus.handDetected
                    ? 'bg-[rgba(72,221,245,0.1)] border-[#48DDF5]/50 shadow-[0_0_20px_rgba(72,221,245,0.25)]'
                    : 'bg-[rgba(11,18,32,0.6)] border-[rgba(148,180,210,0.12)] text-[#61758B]'
                }`}
              >
                {trackingStatus.currentGesture ? (
                  <Sparkles className="w-12 h-12 text-[#42F5A5] animate-pulse" />
                ) : trackingStatus.handDetected ? (
                  <Radio className="w-10 h-10 text-[#48DDF5] animate-spin" />
                ) : (
                  <EyeOff className="w-10 h-10 text-[#61758B]" />
                )}
              </div>

              {/* Big Bold Recognized Gesture Name */}
              <div className="flex flex-col items-center gap-1">
                <span className="text-3xl font-black text-white tracking-tight">
                  {trackingStatus.currentGesture?.name
                    ? trackingStatus.currentGesture.name
                    : trackingStatus.handDetected
                    ? 'Analyzing Hand Pose...'
                    : 'Searching for hand...'}
                </span>
                <span className="text-xs text-[#91A4B8] max-w-xs">
                  {trackingStatus.currentGesture
                    ? 'Live hand pose matched with trained gesture library'
                    : trackingStatus.handDetected
                    ? 'Hand in camera frame. Hold pose steady to confirm'
                    : 'Place your hand in front of the camera to begin'}
                </span>
              </div>

              {/* Prominent Action Banner */}
              <div className="w-full max-w-sm px-4 py-2.5 rounded-xl bg-[rgba(11,18,32,0.7)] border border-[rgba(148,180,210,0.14)] flex items-center justify-between">
                <span className="text-xs text-[#91A4B8] flex items-center gap-1.5 font-medium">
                  <Zap className="w-3.5 h-3.5 text-[#48DDF5]" />
                  Bound Action
                </span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[rgba(72,221,245,0.1)] text-[#48DDF5] border border-[rgba(72,221,245,0.2)]">
                  {trackingStatus.currentGesture?.action
                    ? trackingStatus.currentGesture.action.replace('_', ' ').toUpperCase()
                    : 'NO ACTION ASSIGNED'}
                </span>
              </div>
            </div>

            {/* Bottom Section: Confidence Gauge & Detailed Telemetry Tiles */}
            <div className="flex flex-col gap-4 relative z-10">
              {/* Confidence Gauge Bar */}
              <div className="p-3 rounded-xl bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-2">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-[#91A4B8] flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#42F5A5]" />
                    Recognition Confidence
                  </span>
                  <span
                    className={`font-bold text-sm ${
                      trackingStatus.currentGesture
                        ? 'text-[#42F5A5]'
                        : trackingStatus.handDetected
                        ? 'text-[#48DDF5]'
                        : 'text-[#61758B]'
                    }`}
                  >
                    {trackingStatus.currentGesture
                      ? `${Math.round(trackingStatus.currentGesture.confidence * 100)}%`
                      : trackingStatus.handDetected
                      ? 'Analyzing...'
                      : '0%'}
                  </span>
                </div>

                <div className="w-full h-2.5 rounded-full bg-[#0B1220] overflow-hidden border border-[rgba(148,180,210,0.12)] p-0.5">
                  <motion.div
                    className={`h-full rounded-full ${
                      trackingStatus.currentGesture
                        ? 'bg-gradient-to-r from-[#48DDF5] to-[#42F5A5]'
                        : trackingStatus.handDetected
                        ? 'bg-[#48DDF5]/50'
                        : 'bg-[#61758B]/30'
                    }`}
                    animate={{
                      width: trackingStatus.currentGesture
                        ? `${Math.round(trackingStatus.currentGesture.confidence * 100)}%`
                        : trackingStatus.handDetected
                        ? '45%'
                        : '0%',
                    }}
                    transition={{ ease: 'easeOut', duration: 0.3 }}
                  />
                </div>
              </div>

              {/* Telemetry Tiles: 2 Columns */}
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2.5 rounded-lg bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
                  <span className="text-[#91A4B8] text-[10px] uppercase">Tracking Status</span>
                  <span className={`font-semibold flex items-center gap-1 ${trackingStatus.handDetected ? 'text-[#42F5A5]' : 'text-[#91A4B8]'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${trackingStatus.handDetected ? 'bg-[#42F5A5]' : 'bg-[#61758B]'}`} />
                    {trackingStatus.handDetected ? 'Hand Locked (21 pts)' : 'Awaiting Presence'}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
                  <span className="text-[#91A4B8] text-[10px] uppercase">Last Recognized</span>
                  <span className="text-white font-semibold truncate flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-[#42F5A5] shrink-0" />
                    {trackingStatus.lastGesture?.name || 'None'}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* DESKTOP MOUSE CONTROL & GESTURE CLICKS (FULL WIDTH) */}
      <MouseControlCard />
    </div>
  );
};
