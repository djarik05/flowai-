import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  MousePointer,
  Presentation,
  PlaySquare,
  Sparkles,
  Sliders,
  Shield,
  AlertOctagon,
  Play,
  Pause,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { useSettingsStore } from '../../store/settingsStore';
import { useActivityStore } from '../../store/activityStore';
import { Card } from '../../components/ui/Card';
import { Slider } from '../../components/ui/Slider';
import { Switch } from '../../components/ui/Switch';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

export const LiveControlView: React.FC = () => {
  const { settings, updateController, updateRecognition } = useSettingsStore();
  const { addLog } = useActivityStore();

  const [activeMode, setActiveMode] = useState<'air_mouse' | 'presentation' | 'media' | 'custom'>(
    'air_mouse'
  );
  const [isPaused, setIsPaused] = useState(false);
  const [safetyNotification, setSafetyNotification] = useState<string | null>(null);

  const showNotice = (msg: string) => {
    setSafetyNotification(msg);
    setTimeout(() => setSafetyNotification(null), 3000);
  };

  const handleToggleController = (enabled: boolean) => {
    updateController({ enabled });
    addLog({
      category: 'controller',
      description: `Controller ${enabled ? 'Enabled' : 'Disabled'} by user toggle`,
      status: enabled ? 'success' : 'warning',
      isSimulated: true,
    });
    showNotice(enabled ? 'Air Controller Activated (Simulated)' : 'Air Controller Deactivated');
  };

  const handlePauseResume = () => {
    const nextPaused = !isPaused;
    setIsPaused(nextPaused);
    addLog({
      category: 'controller',
      description: `Controller ${nextPaused ? 'Paused' : 'Resumed'}`,
      status: 'info',
      isSimulated: true,
    });
    showNotice(nextPaused ? 'Controls Temporarily Paused' : 'Controls Resumed');
  };

  const handleEmergencyStop = () => {
    updateController({ enabled: false });
    setIsPaused(true);
    addLog({
      category: 'controller',
      description: 'EMERGENCY STOP EXECUTED: All virtual cursor movement & input halted.',
      status: 'error',
      isSimulated: true,
    });
    showNotice('EMERGENCY STOP TRIGGERED: Control Immediately Disabled');
  };

  return (
    <div className="w-full flex flex-col gap-6 select-none">
      {/* Safety Alert Notification Toast */}
      {safetyNotification && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="p-3 rounded-xl bg-[rgba(255,100,124,0.15)] border border-[rgba(255,100,124,0.3)] text-[#FF647C] text-xs font-medium flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{safetyNotification}</span>
          </div>
          <span className="text-[10px] uppercase font-mono text-[#FFCB70]">Simulated Event</span>
        </motion.div>
      )}

      {/* Header & Master Safety Controls Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 glass rounded-2xl p-5 border border-[rgba(148,180,210,0.18)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-lg font-bold text-white">Live Control Station</h2>
            <Badge variant={settings.controller.enabled && !isPaused ? 'green' : 'warning'} dot>
              {settings.controller.enabled
                ? isPaused
                  ? 'Controller Paused'
                  : 'Active Dispatch'
                : 'Controller Disabled'}
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            Configure active cursor sensitivity, click thresholds, and dispatch safety boundaries.
          </p>
        </div>

        {/* Master Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Switch
            checked={settings.controller.enabled}
            onChange={handleToggleController}
            label={settings.controller.enabled ? 'Enabled' : 'Disabled'}
            className="mr-2"
          />

          <Button
            variant="secondary"
            size="sm"
            onClick={handlePauseResume}
            disabled={!settings.controller.enabled}
            icon={isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          >
            {isPaused ? 'Resume Controls' : 'Pause Controls'}
          </Button>

          <Button
            variant="danger"
            size="sm"
            onClick={handleEmergencyStop}
            icon={<AlertOctagon className="w-4 h-4" />}
          >
            Emergency Stop
          </Button>
        </div>
      </div>

      {/* Mode Selection Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            id: 'air_mouse',
            label: 'Air Mouse Mode',
            desc: 'Pointer tracking, left/right clicks, dragging & scrolling',
            icon: MousePointer,
          },
          {
            id: 'presentation',
            label: 'Presentation Mode',
            desc: 'Slide forward/backward & laser pointer simulation',
            icon: Presentation,
          },
          {
            id: 'media',
            label: 'Media Controller',
            desc: 'Play/pause, audio volume modulation, fast forward',
            icon: PlaySquare,
          },
          {
            id: 'custom',
            label: 'Custom Mapping',
            desc: 'Direct global keybinding macros and system commands',
            icon: Sparkles,
          },
        ].map((mode) => {
          const Icon = mode.icon;
          const isSelected = activeMode === mode.id;

          return (
            <Card
              key={mode.id}
              variant={isSelected ? 'glow' : 'glass'}
              hoverable
              onClick={() => setActiveMode(mode.id as any)}
              className={`p-4 cursor-pointer transition-all ${
                isSelected ? 'border-[#48DDF5]' : 'border-[rgba(148,180,210,0.12)]'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div
                  className={`p-2 rounded-xl ${
                    isSelected
                      ? 'bg-gradient-to-br from-[#48DDF5] to-[#42F5A5] text-[#070B12]'
                      : 'bg-[rgba(18,29,45,0.7)] text-[#91A4B8]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                {isSelected && <CheckCircle2 className="w-4 h-4 text-[#42F5A5]" />}
              </div>
              <h3 className="text-sm font-bold text-white mb-1">{mode.label}</h3>
              <p className="text-[11px] text-[#91A4B8] leading-relaxed">{mode.desc}</p>
            </Card>
          );
        })}
      </div>

      {/* Main Configurations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN (Col 7): Cursor Movement & Smoothing Sliders */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <Card variant="glass-strong" className="p-6">
            <div className="flex items-center justify-between pb-4 border-b border-[rgba(148,180,210,0.12)] mb-5">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#48DDF5]" />
                <h3 className="text-sm font-bold text-white">Air Mouse Cursor Dynamics</h3>
              </div>
              <Badge variant="cyan">Real-Time State</Badge>
            </div>

            <div className="space-y-5">
              <Slider
                label="Cursor Sensitivity"
                description="Speed multiplier applied to relative fingertip coordinate deltas"
                min={0.1}
                max={2.0}
                step={0.05}
                value={settings.controller.cursorSensitivity}
                onChange={(val) => updateController({ cursorSensitivity: val })}
                formatValue={(v) => `${(v * 100).toFixed(0)}%`}
              />

              <Slider
                label="Movement Smoothing"
                description="Exponential moving average filter weight to eliminate natural hand tremors"
                min={0.1}
                max={0.95}
                step={0.05}
                value={settings.controller.movementSmoothing}
                onChange={(val) => updateController({ movementSmoothing: val })}
                formatValue={(v) => `${(v * 100).toFixed(0)}%`}
              />

              <Slider
                label="Dead-Zone Threshold"
                description="Micro-motion radius ignored around current pointer position"
                min={0.01}
                max={0.2}
                step={0.01}
                value={settings.controller.deadZone}
                onChange={(val) => updateController({ deadZone: val })}
                formatValue={(v) => `${(v * 100).toFixed(1)} px`}
              />

              <Slider
                label="Confidence Threshold"
                description="Minimum neural landmark prediction probability required to trigger pointer"
                min={0.5}
                max={0.98}
                step={0.02}
                value={settings.recognition.confidenceThreshold}
                onChange={(val) => updateRecognition({ confidenceThreshold: val })}
                formatValue={(v) => `${(v * 100).toFixed(0)}%`}
              />

              <Slider
                label="Gesture Activation Delay"
                description="Duration a gesture must be stably held before engaging action"
                min={50}
                max={800}
                step={25}
                unit="ms"
                value={settings.controller.gestureActivationDelay}
                onChange={(val) => updateController({ gestureActivationDelay: val })}
              />

              <Slider
                label="Click Debounce Cooldown"
                description="Refractory period after a click event to prevent accidental double-clicks"
                min={100}
                max={1000}
                step={50}
                unit="ms"
                value={settings.controller.clickCooldown}
                onChange={(val) => updateController({ clickCooldown: val })}
              />
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN (Col 5): Configurable Air Mouse Actions & Safety Information */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <Card variant="glass" className="p-6">
            <h3 className="text-sm font-bold text-white mb-2">Supported Air Mouse Actions</h3>
            <p className="text-xs text-[#91A4B8] mb-4">
              Configured dispatch behaviors ready for Python backend hook attachment:
            </p>

            <div className="space-y-2.5">
              {[
                { name: 'Cursor Movement', gesture: 'Index Finger Pointing', action: 'Direct Vector' },
                { name: 'Left-Click', gesture: 'Index + Thumb Pinch', action: 'Single Click' },
                { name: 'Right-Click', gesture: 'Two Fingers (Victory)', action: 'Context Menu' },
                { name: 'Double-Click', gesture: 'Rapid Double Pinch', action: 'File Launch' },
                { name: 'Scroll Up', gesture: 'Vertical Hand Stroke Up', action: 'Wheel Delta +120' },
                { name: 'Scroll Down', gesture: 'Vertical Hand Stroke Down', action: 'Wheel Delta -120' },
                { name: 'Click-and-Hold', gesture: 'Closed Fist Clench', action: 'Mouse Down Hold' },
                { name: 'Drag-and-Drop', gesture: 'Fist Drag + Open Palm Release', action: 'Mouse Drag' },
              ].map((item) => (
                <div
                  key={item.name}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] text-xs"
                >
                  <div>
                    <span className="font-semibold text-white block">{item.name}</span>
                    <span className="text-[10px] text-[#91A4B8]">{item.gesture}</span>
                  </div>
                  <span className="text-[11px] font-mono text-[#48DDF5] bg-[rgba(72,221,245,0.08)] px-2 py-0.5 rounded border border-[rgba(72,221,245,0.18)]">
                    {item.action}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Safety Protocols Guide Card */}
          <Card variant="glass" className="p-5 border-[rgba(255,203,112,0.2)]">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-[#FFCB70]" />
              <h4 className="text-xs font-bold text-white">Failsafe & Boundaries</h4>
            </div>
            <p className="text-xs text-[#91A4B8] leading-relaxed mb-3">
              To prevent accidental runaway pointer events, the controller automatically drops
              tracking if hand confidence falls below threshold or if emergency shortcut{' '}
              <kbd className="px-1.5 py-0.5 bg-[#070B12] rounded border border-[rgba(148,180,210,0.2)] text-[#FFCB70] font-mono">
                {settings.background.emergencyStopShortcut}
              </kbd>{' '}
              is detected.
            </p>
            <div className="text-[10px] text-[#61758B]">
              * Frontend-only simulation: Actual OS input hooks remain detached.
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
