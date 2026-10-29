import React, { useState } from 'react';
import {
  Settings,
  Camera,
  Cpu,
  MousePointer,
  Monitor,
  RotateCcw,
  Save,
  CheckCircle2,
  ShieldAlert,
} from 'lucide-react';
import { useSettingsStore } from '../../store/settingsStore';
import { useActivityStore } from '../../store/activityStore';
import { Card } from '../../components/ui/Card';
import { Switch } from '../../components/ui/Switch';
import { Slider } from '../../components/ui/Slider';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

export const SettingsView: React.FC = () => {
  const {
    settings,
    updateGeneral,
    updateCamera,
    updateRecognition,
    updateController,
    updateBackground,
    resetAll,
  } = useSettingsStore();

  const { addLog } = useActivityStore();
  const [saveToast, setSaveToast] = useState(false);

  const handleManualSave = () => {
    setSaveToast(true);
    addLog({
      category: 'settings',
      description: 'User settings profile confirmed and persisted to localStorage',
      status: 'success',
      isSimulated: false,
    });
    setTimeout(() => setSaveToast(false), 2500);
  };

  const handleReset = () => {
    if (window.confirm('Reset all GestureFlow AI preferences to defaults?')) {
      resetAll();
      addLog({
        category: 'settings',
        description: 'All user settings restored to factory defaults',
        status: 'warning',
        isSimulated: false,
      });
    }
  };

  return (
    <div className="w-full flex flex-col gap-6 select-none">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass rounded-2xl p-5 border border-[rgba(148,180,210,0.18)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Settings className="w-5 h-5 text-[#48DDF5]" />
            <h2 className="text-lg font-bold text-white">System Configuration & Preferences</h2>
            <Badge variant="cyan">Schema v1</Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            Manage application runtime, camera simulation parameters, and background shortcut hooks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleReset}
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Reset All
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleManualSave}
            icon={<Save className="w-3.5 h-3.5" />}
          >
            {saveToast ? 'Saved!' : 'Save Preferences'}
          </Button>
        </div>
      </div>

      {saveToast && (
        <div className="p-3 rounded-xl bg-[rgba(66,245,165,0.15)] border border-[rgba(66,245,165,0.3)] text-[#42F5A5] text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Settings saved to local storage</span>
        </div>
      )}

      {/* Main Settings Sections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SECTION 1: GENERAL PREFERENCES */}
        <Card variant="glass" className="p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[rgba(148,180,210,0.12)]">
            <Monitor className="w-4 h-4 text-[#48DDF5]" />
            <h3 className="text-sm font-bold text-white">General & Interface</h3>
          </div>

          <div className="space-y-4">
            <Switch
              checked={settings.general.autoLaunch}
              onChange={(val) => updateGeneral({ autoLaunch: val })}
              label="Auto-Launch at System Startup"
              description="Launches GestureFlow AI on user login (Desktop runtime hook)"
            />

            <Select
              label="Visual Theme"
              description="Application interface color mode"
              value={settings.general.theme}
              onChange={(val) => updateGeneral({ theme: val as any })}
              options={[
                { value: 'dark', label: 'Dark Cyber Glass (Default)' },
                { value: 'system', label: 'Match Operating System Theme' },
              ]}
            />

            <Switch
              checked={settings.general.animationsEnabled}
              onChange={(val) => updateGeneral({ animationsEnabled: val })}
              label="Framer Motion Transitions"
              description="Enable smooth spring physics across dialogs and charts"
            />

            <Switch
              checked={settings.general.reducedMotion}
              onChange={(val) => updateGeneral({ reducedMotion: val })}
              label="Respect Reduced Motion"
              description="Minimize parallax and continuous pulsating glows"
            />

            <Select
              label="Language"
              value={settings.general.language}
              onChange={(val) => updateGeneral({ language: val })}
              options={[
                { value: 'en', label: 'English (US)' },
                { value: 'es', label: 'Español (Coming soon in backend)' },
                { value: 'de', label: 'Deutsch (Coming soon in backend)' },
              ]}
            />
          </div>
        </Card>

        {/* SECTION 2: CAMERA SIMULATION (Hardware not opened) */}
        <Card variant="glass" className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[rgba(148,180,210,0.12)]">
            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-[#42F5A5]" />
              <h3 className="text-sm font-bold text-white">Camera Module (Mockup)</h3>
            </div>
            <Badge variant="warning">Hardware Detached</Badge>
          </div>

          <div className="space-y-4">
            <Select
              label="Camera Video Source"
              description="Select physical or virtual video device"
              value={settings.camera.deviceId}
              onChange={(val) => updateCamera({ deviceId: val })}
              options={[
                { value: 'default', label: 'Integrated HD Webcam (Default)' },
                { value: 'usb_cam_1', label: 'External USB Vision Cam 1080p' },
                { value: 'obs_virtual', label: 'OBS Virtual Camera Stream' },
              ]}
            />

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Stream Resolution"
                value={settings.camera.resolution}
                onChange={(val) => updateCamera({ resolution: val as any })}
                options={[
                  { value: '480p', label: '640 × 480 (Low Latency)' },
                  { value: '720p', label: '1280 × 720 (Recommended)' },
                  { value: '1080p', label: '1920 × 1080 (High Detail)' },
                ]}
              />

              <Select
                label="Target FPS"
                value={String(settings.camera.frameRate)}
                onChange={(val) => updateCamera({ frameRate: Number(val) as any })}
                options={[
                  { value: '15', label: '15 FPS (Battery Saver)' },
                  { value: '30', label: '30 FPS (Smooth)' },
                  { value: '60', label: '60 FPS (Pro)' },
                ]}
              />
            </div>

            <Switch
              checked={settings.camera.mirrorPreview}
              onChange={(val) => updateCamera({ mirrorPreview: val })}
              label="Mirror Video Viewport"
              description="Flip preview horizontally to feel like a natural mirror"
            />
          </div>
        </Card>

        {/* SECTION 3: GESTURE RECOGNITION TUNING */}
        <Card variant="glass" className="p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[rgba(148,180,210,0.12)]">
            <Cpu className="w-4 h-4 text-[#9B7CFF]" />
            <h3 className="text-sm font-bold text-white">Gesture Recognition Pipeline</h3>
          </div>

          <div className="space-y-4">
            <Slider
              label="Global Confidence Threshold"
              description="Rejects landmark matches lower than this probability"
              min={0.5}
              max={0.95}
              step={0.05}
              value={settings.recognition.confidenceThreshold}
              onChange={(val) => updateRecognition({ confidenceThreshold: val })}
              formatValue={(v) => `${(v * 100).toFixed(0)}%`}
            />

            <Slider
              label="Prediction Temporal Smoothing"
              description="Window filter to reduce false-positive frame flickers"
              min={0.1}
              max={0.9}
              step={0.05}
              value={settings.recognition.predictionSmoothing}
              onChange={(val) => updateRecognition({ predictionSmoothing: val })}
              formatValue={(v) => `${(v * 100).toFixed(0)}%`}
            />

            <Slider
              label="Global Gesture Cooldown"
              description="Minimum delay between discrete triggering events"
              min={100}
              max={1000}
              step={50}
              unit="ms"
              value={settings.recognition.gestureCooldown}
              onChange={(val) => updateRecognition({ gestureCooldown: val })}
            />

            <Select
              label="Unknown Gesture Handling"
              value={settings.recognition.unknownGestureAction}
              onChange={(val) => updateRecognition({ unknownGestureAction: val as any })}
              options={[
                { value: 'ignore', label: 'Silently Ignore (Recommended)' },
                { value: 'notify', label: 'Show Low-Confidence Toast' },
                { value: 'log', label: 'Log Event to Journal' },
              ]}
            />
          </div>
        </Card>

        {/* SECTION 4: BACKGROUND OPERATION & HOTKEYS */}
        <Card variant="glass" className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[rgba(148,180,210,0.12)]">
            <div className="flex items-center gap-2">
              <MousePointer className="w-4 h-4 text-[#FFCB70]" />
              <h3 className="text-sm font-bold text-white">Background Mode & Hotkeys</h3>
            </div>
            <Badge variant="cyan">Desktop Ready</Badge>
          </div>

          <div className="space-y-4">
            <Switch
              checked={settings.background.hideUI}
              onChange={(val) => updateBackground({ hideUI: val })}
              label="Enable Background Service Simulation"
              description="Allows hiding main window while dispatch engine continues running"
            />

            <Switch
              checked={settings.background.startMinimized}
              onChange={(val) => updateBackground({ startMinimized: val })}
              label="Start Minimized to System Tray"
              description="Launches silently in the background on startup"
            />

            <div className="space-y-2 pt-2 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)]">
                <span className="text-[#91A4B8]">Restore Interface Global Shortcut</span>
                <kbd className="px-2 py-1 rounded bg-[#070B12] text-[#48DDF5] font-mono border border-[rgba(72,221,245,0.2)]">
                  {settings.background.returnShortcut}
                </kbd>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)]">
                <span className="text-[#91A4B8]">Emergency Kill Shortcut</span>
                <kbd className="px-2 py-1 rounded bg-[#070B12] text-[#FF647C] font-mono border border-[rgba(255,100,124,0.2)]">
                  {settings.background.emergencyStopShortcut}
                </kbd>
              </div>
            </div>

            <div className="flex items-start gap-2 p-3 rounded-xl bg-[rgba(255,203,112,0.08)] border border-[rgba(255,203,112,0.2)] text-[11px] text-[#FFCB70]">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                Note: Global system-wide keyboard hooks operate only when running inside the
                compiled desktop runtime (Electron / PyInstaller).
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
