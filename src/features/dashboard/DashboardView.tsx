import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Camera,
  Activity,
  Cpu,
  MousePointer,
  Shield,
  Play,
  Pause,
  ArrowRight,
  Sliders,
  CheckCircle2,
  Clock,
  Sparkles,
  Zap,
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { useSettingsStore } from '../../store/settingsStore';
import { useGestureStore } from '../../store/gestureStore';
import { useActivityStore } from '../../store/activityStore';
import { HandTrackingVisualizer } from '../../components/visuals/HandTrackingVisualizer';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';

export const DashboardView: React.FC = () => {
  const { setCurrentView, trackingStatus, setDetectedGesture, isDemoCycling, toggleDemoCycling } =
    useAppStore();
  const { settings, updateController } = useSettingsStore();
  const { gestures } = useGestureStore();
  const { logs } = useActivityStore();

  const [activeMode, setActiveMode] = useState<'air_mouse' | 'presentation' | 'media' | 'custom'>(
    'air_mouse'
  );

  // Demo simulator gesture cycling
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
  }, [isDemoCycling, gestures]);

  const recentLogs = logs.slice(0, 5);

  return (
    <div className="w-full flex flex-col gap-6 select-none">
      {/* Top Banner / Mode Selector Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass rounded-2xl p-4 border border-[rgba(148,180,210,0.16)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-base font-bold text-white">Central Gesture Workspace</h2>
            <Badge variant="cyan" dot>
              Interactive Demo
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            Simulated 21-point tracking matrix & live air controller dispatch engine.
          </p>
        </div>

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

      {/* Primary Workspace Grid: Large visual workspace on left, Telemetry & Status on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LARGE PRIMARY WORKSPACE: Main Tracking Preview (Col 8) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <Card variant="glass-strong" className="p-6 relative overflow-hidden">
            {/* Top Bar of Main Viewport */}
            <div className="flex items-center justify-between pb-4 border-b border-[rgba(148,180,210,0.12)]">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#42F5A5] animate-ping" />
                <span className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  Virtual Camera Canvas #0
                </span>
                <Badge variant="muted">Canvas Simulation Only</Badge>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1 text-xs font-mono text-[#48DDF5]">
                  <Activity className="w-3.5 h-3.5" />
                  <span>30.0 FPS</span>
                </div>

                {/* Demo Cycling Toggle */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleDemoCycling}
                  icon={isDemoCycling ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  className="text-xs"
                >
                  {isDemoCycling ? 'Pause Demo Cycling' : 'Cycle Gestures'}
                </Button>
              </div>
            </div>

            {/* Central Animated Hand Mesh Viewport */}
            <div className="min-h-[420px] w-full flex items-center justify-center relative my-2">
              <HandTrackingVisualizer
                showDiagnostics={false}
                activeGestureName={trackingStatus.currentGesture?.name}
                isSimulated={true}
              />

              {/* Floating Live Telemetry HUD Overlays */}
              <div className="absolute top-4 left-4 bg-[rgba(11,18,32,0.85)] border border-[rgba(148,180,210,0.18)] rounded-xl p-3 backdrop-blur-md text-xs font-mono">
                <div className="text-[10px] text-[#91A4B8] uppercase">Target Coordinates</div>
                <div className="text-[#48DDF5] font-bold text-sm">X: 0.482 | Y: 0.315</div>
                <div className="text-[10px] text-[#42F5A5] mt-0.5">Tracking Confidence: 96.4%</div>
              </div>

              <div className="absolute top-4 right-4 bg-[rgba(11,18,32,0.85)] border border-[rgba(148,180,210,0.18)] rounded-xl p-3 backdrop-blur-md text-xs font-mono text-right">
                <div className="text-[10px] text-[#91A4B8] uppercase">Simulated Pipeline</div>
                <div className="text-[#F1F5F9] font-bold">MediaPipe Hands v0.10</div>
                <div className="text-[10px] text-[#91A4B8] mt-0.5">Latency: ~11ms</div>
              </div>
            </div>

            {/* Bottom Bar: Quick Controller Toggle */}
            <div className="pt-4 border-t border-[rgba(148,180,210,0.12)] flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Button
                  variant={settings.controller.enabled ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => updateController({ enabled: !settings.controller.enabled })}
                  icon={<Zap className="w-4 h-4" />}
                >
                  {settings.controller.enabled ? 'Disable Air Controller' : 'Enable Air Controller'}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentView('live-control')}
                  icon={<Sliders className="w-4 h-4" />}
                >
                  Tune Sensitivity
                </Button>
              </div>

              <p className="text-[11px] text-[#91A4B8]">
                {settings.controller.enabled
                  ? 'Simulated cursor transforms actively updating frontend state.'
                  : 'Controller in standby mode. Cursor movement paused.'}
              </p>
            </div>
          </Card>

          {/* Quick Gesture Shortcuts Overview Panel */}
          <Card variant="glass" className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#48DDF5]" />
                <h3 className="text-sm font-bold text-white">Active Gesture Mappings</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentView('gesture-manager')}
                icon={<ArrowRight className="w-3.5 h-3.5" />}
                iconPosition="right"
                className="text-xs"
              >
                Manage All ({gestures.length})
              </Button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {gestures.slice(0, 4).map((gesture) => (
                <div
                  key={gesture.id}
                  className={`p-3 rounded-xl border transition-all ${
                    trackingStatus.currentGesture?.gestureId === gesture.id
                      ? 'bg-[rgba(72,221,245,0.12)] border-[#48DDF5] shadow-[0_0_16px_rgba(72,221,245,0.2)]'
                      : 'bg-[rgba(11,18,32,0.6)] border-[rgba(148,180,210,0.12)]'
                  }`}
                >
                  <div className="text-[10px] text-[#91A4B8] font-mono uppercase truncate">
                    {gesture.type}
                  </div>
                  <div className="text-xs font-bold text-white truncate mt-0.5">{gesture.name}</div>
                  <div className="text-[11px] text-[#42F5A5] mt-1 truncate">
                    ➔ {gesture.action.replace('_', ' ')}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* SIDE PANELS (Col 4): Detected Gesture, System Status & Recent Activity */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          {/* DETECTED GESTURE PANEL */}
          <Card variant="glow" className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#91A4B8] flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#48DDF5] animate-ping" />
                Detected Gesture
              </span>
              <Badge variant="green">Live Demo Stream</Badge>
            </div>

            <div className="my-2">
              <div className="text-2xl font-black text-white tracking-tight flex items-center justify-between">
                <span>{trackingStatus.currentGesture?.name || 'Searching...'}</span>
              </div>
              <div className="text-xs text-[#91A4B8] mt-1">
                Bound Action:{' '}
                <span className="text-[#48DDF5] font-mono font-semibold">
                  {trackingStatus.currentGesture?.action.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            {/* Confidence Gauge Bar */}
            <div className="mt-4 pt-3 border-t border-[rgba(148,180,210,0.12)]">
              <div className="flex justify-between items-center text-xs mb-1.5 font-mono">
                <span className="text-[#91A4B8]">Confidence</span>
                <span className="text-[#42F5A5] font-bold">
                  {Math.round((trackingStatus.currentGesture?.confidence || 0.94) * 100)}%
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-[#0B1220] overflow-hidden border border-[rgba(148,180,210,0.1)]">
                <motion.div
                  className="h-full bg-gradient-to-r from-[#48DDF5] to-[#42F5A5] rounded-full"
                  animate={{
                    width: `${Math.round((trackingStatus.currentGesture?.confidence || 0.94) * 100)}%`,
                  }}
                  transition={{ ease: 'easeOut', duration: 0.3 }}
                />
              </div>
            </div>

            {/* Last Recognized Gesture item */}
            <div className="mt-4 text-[11px] text-[#91A4B8] flex justify-between items-center bg-[rgba(11,18,32,0.6)] px-3 py-2 rounded-xl border border-[rgba(148,180,210,0.1)]">
              <span>Last Recognized:</span>
              <span className="text-white font-medium">
                {trackingStatus.lastGesture?.name || 'Two Fingers (Victory)'}
              </span>
            </div>
          </Card>

          {/* SYSTEM STATUS PANEL */}
          <Card variant="glass" className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#91A4B8]">
                System Subsystems
              </h3>
              <Badge variant="cyan">Frontend Demo Mode</Badge>
            </div>

            <div className="space-y-3">
              {[
                {
                  label: 'Webcam Device',
                  status: 'Simulated Stream',
                  state: 'demo',
                  icon: Camera,
                },
                {
                  label: 'Hand Tracking',
                  status: '21 Points Active (Simulated)',
                  state: 'demo',
                  icon: Activity,
                },
                {
                  label: 'Custom AI Model',
                  status: 'MLP Landmark Weights Ready',
                  state: 'demo',
                  icon: Cpu,
                },
                {
                  label: 'OS Controller',
                  status: settings.controller.enabled ? 'Enabled (Simulated)' : 'Standby',
                  state: settings.controller.enabled ? 'active' : 'standby',
                  icon: MousePointer,
                },
                {
                  label: 'Input Permissions',
                  status: 'Mock Permission Granted',
                  state: 'demo',
                  icon: Shield,
                },
              ].map((subsystem) => {
                const Icon = subsystem.icon;
                return (
                  <div
                    key={subsystem.label}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] text-xs"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="p-1 rounded bg-[rgba(72,221,245,0.08)] text-[#48DDF5]">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-[#F1F5F9] font-medium">{subsystem.label}</span>
                    </div>

                    <span className="text-[11px] text-[#42F5A5] font-mono">{subsystem.status}</span>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 pt-3 border-t border-[rgba(148,180,210,0.1)] text-[10px] text-[#61758B] leading-relaxed">
              * Actual OS-level mouse hook & hardware camera drivers will be attached by the
              Python FastAPI backend.
            </div>
          </Card>

          {/* RIGHT-SIDE ACTIVITY SUMMARY PANEL */}
          <Card variant="glass" className="p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#91A4B8]">
                Recent Events
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentView('activity-logs')}
                className="text-[11px] p-0 h-auto"
              >
                View All
              </Button>
            </div>

            <div className="space-y-2">
              {recentLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-2.5 text-[11px] p-2 rounded-lg bg-[rgba(11,18,32,0.5)] border border-[rgba(148,180,210,0.08)]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#48DDF5] mt-1 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[#F1F5F9] truncate">{log.description}</p>
                    <span className="text-[10px] text-[#61758B] font-mono">{log.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
