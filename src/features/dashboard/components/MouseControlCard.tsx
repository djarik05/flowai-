import React, { useEffect } from 'react';
import {
  MousePointer,
  Sliders,
  Power,
  ShieldCheck,
  Activity,
  Move,
  Layers,
  Monitor,
  Zap,
  Clock,
  CheckCircle2,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { useMouseStore } from '../../../store/mouseStore';
import { useCameraStore } from '../../../store/cameraStore';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export const MouseControlCard: React.FC = () => {
  const {
    status,
    isLoading,
    error,
    isBackendConnected,
    fetchStatus,
    toggleMouse,
    toggleLeftClick,
    toggleRightClick,
    triggerClick,
    triggerRightClick,
    updateSettings,
  } = useMouseStore();

  // Periodically poll mouse status while on the dashboard
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      fetchStatus();
    }, isBackendConnected ? 400 : 2500);
    return () => clearInterval(interval);
  }, [fetchStatus, isBackendConnected]);

  const getStatusBadge = () => {
    if (!isBackendConnected) {
      return (
        <Badge variant="warning" dot>
          Backend Offline
        </Badge>
      );
    }

    switch (status.state) {
      case 'active':
        return (
          <Badge variant="green" dot>
            Active & Tracking
          </Badge>
        );
      case 'waiting_for_hand':
        return (
          <Badge variant="cyan" dot>
            Awaiting Hand
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="error" dot>
            Error
          </Badge>
        );
      case 'disabled':
      default:
        return (
          <Badge variant="muted">
            Disabled (Safe)
          </Badge>
        );
    }
  };

  return (
    <Card variant="glass" className="p-5 flex flex-col gap-4 border-[rgba(148,180,210,0.14)] w-full">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(148,180,210,0.1)]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[rgba(72,221,245,0.1)] text-[#48DDF5] border border-[rgba(72,221,245,0.2)]">
            <MousePointer className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Desktop Mouse Control
              </h3>
              <span className="text-[10px] text-[#42F5A5] font-mono px-2 py-0.5 rounded bg-[rgba(66,245,165,0.1)] border border-[rgba(66,245,165,0.2)]">
                Phase 6A & 6B
              </span>
            </div>
            <p className="text-xs text-[#91A4B8] mt-0.5">
              Move cursor with Open Palm • Left click with Index Finger • Right click with Victory (Two Fingers)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge()}
          {isBackendConnected ? (
            <Button
              size="sm"
              variant={status.enabled ? 'danger' : 'primary'}
              onClick={toggleMouse}
              disabled={isLoading}
              icon={<Power className="w-4 h-4" />}
              className="font-semibold text-xs tracking-wide min-w-[190px]"
            >
              {isLoading
                ? 'Updating...'
                : status.enabled
                ? 'Disable Cursor Control'
                : 'Enable Cursor Control'}
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={fetchStatus}
              disabled={isLoading}
              icon={<Power className="w-4 h-4 text-[#F59E0B]" />}
              className="font-semibold text-xs tracking-wide border-[rgba(245,158,11,0.3)] text-[#FBBF24] hover:bg-[rgba(245,158,11,0.1)]"
            >
              {isLoading ? 'Checking connection...' : 'Retry Backend Connection'}
            </Button>
          )}
        </div>
      </div>

      {/* Error or Backend Offline Alert */}
      {!isBackendConnected ? (
        <div className="p-3 rounded-xl bg-[rgba(245,158,11,0.12)] border border-[rgba(245,158,11,0.25)] text-xs text-[#FBBF24] flex flex-col gap-1.5">
          <div className="flex items-center gap-2 font-medium">
            <span className="w-2 h-2 rounded-full bg-[#F59E0B] animate-ping" />
            <span>FastAPI Backend Offline (Port 8000)</span>
          </div>
          <p className="text-[11px] text-[#91A4B8] leading-relaxed">
            Desktop cursor movement requires the Python backend service. Run <code className="text-[#48DDF5] bg-[rgba(11,18,32,0.8)] px-1.5 py-0.5 rounded font-mono">run_gestureflow.bat</code> or <code className="text-[#48DDF5] bg-[rgba(11,18,32,0.8)] px-1.5 py-0.5 rounded font-mono">npm run backend</code> in your terminal.
          </p>
        </div>
      ) : (error || status.last_error) ? (
        <div className="p-2.5 rounded-xl bg-[rgba(239,68,68,0.12)] border border-[rgba(239,68,68,0.25)] text-xs text-[#F87171] flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444]" />
          <span>{error || status.last_error}</span>
        </div>
      ) : null}

      {/* Cursor Movement Calibration */}
      <div className="p-3.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-3">
        <div className="flex items-center justify-between text-xs font-semibold text-white">
          <span className="flex items-center gap-1.5 text-[#91A4B8]">
            <Sliders className="w-3.5 h-3.5 text-[#48DDF5]" />
            Cursor Movement & Tracking Calibration
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Sensitivity Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
              <span>Cursor Sensitivity</span>
              <span className="text-[#48DDF5] font-bold">{status.sensitivity.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.2"
              max="3.0"
              step="0.1"
              value={status.sensitivity}
              onChange={(e) => updateSettings({ sensitivity: parseFloat(e.target.value) })}
              className="w-full accent-[#48DDF5] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
            />
          </div>

          {/* Smoothing Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
              <span>Smoothing Alpha (EMA)</span>
              <span className="text-[#42F5A5] font-bold">
                {status.smoothing_alpha.toFixed(2)}{' '}
                <span className="text-[10px] text-[#91A4B8]">
                  ({status.smoothing_alpha <= 0.25 ? 'High' : status.smoothing_alpha <= 0.5 ? 'Balanced' : 'Fast'})
                </span>
              </span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.80"
              step="0.05"
              value={status.smoothing_alpha}
              onChange={(e) => updateSettings({ smoothing_alpha: parseFloat(e.target.value) })}
              className="w-full accent-[#42F5A5] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
            />
          </div>

          {/* Active Margin Slider */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
              <span>Active Tracking Margin</span>
              <span className="text-[#A78BFA] font-bold">
                {Math.round(status.active_margin_x * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.30"
              step="0.05"
              value={status.active_margin_x}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                updateSettings({ active_margin_x: val, active_margin_y: val });
              }}
              className="w-full accent-[#A78BFA] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* GESTURE CLICK CONTROLS (PHASE 6B.1 & PHASE 6B.2) - RESIZED HORIZONTAL DUAL BOXES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* LEFT CLICK CONTROL SECTION (PHASE 6B.1) */}
        <div className="p-4 rounded-xl bg-[rgba(11,18,32,0.7)] border border-[rgba(72,221,245,0.25)] flex flex-col gap-3.5 shadow-lg">
          {/* Header & Independent Toggle */}
          <div className="flex items-center justify-between pb-2 border-b border-[rgba(148,180,210,0.08)]">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-[rgba(66,245,165,0.1)] text-[#42F5A5]">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white uppercase tracking-wider">
                    Gesture Left Click
                  </span>
                  <span className="text-[10px] text-[#48DDF5] font-mono px-1.5 py-0.5 rounded bg-[rgba(72,221,245,0.1)] border border-[rgba(72,221,245,0.2)]">
                    Phase 6B.1
                  </span>
                </div>
                <span className="text-[11px] text-[#91A4B8]">
                  Index Finger Point or Pinch (Landmark 8)
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={toggleLeftClick}
              disabled={!status.enabled}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors border ${
                !status.enabled
                  ? 'opacity-50 cursor-not-allowed bg-[rgba(11,18,32,0.4)] border-[rgba(148,180,210,0.1)] text-[#91A4B8]'
                  : status.left_click_enabled
                  ? 'bg-[rgba(66,245,165,0.15)] border-[#42F5A5]/40 text-[#42F5A5]'
                  : 'bg-[rgba(239,68,68,0.12)] border-[#EF4444]/30 text-[#F87171]'
              }`}
            >
              {status.left_click_enabled ? (
                <>
                  <ToggleRight className="w-4 h-4 text-[#42F5A5]" />
                  <span>Enabled</span>
                </>
              ) : (
                <>
                  <ToggleLeft className="w-4 h-4 text-[#F87171]" />
                  <span>Disabled</span>
                </>
              )}
            </button>
          </div>

          {/* Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            {/* Activation Gesture */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Gesture</span>
              <span className="text-white font-semibold flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full bg-[#48DDF5] shrink-0" />
                Index Finger
              </span>
              <span className="text-[10px] text-[#91A4B8]">Point / Pinch (L8)</span>
            </div>

            {/* Pinch Detection Status */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Pinch Status</span>
              <span
                className={`font-bold flex items-center gap-1.5 truncate ${
                  !status.left_click_enabled || !status.enabled
                    ? 'text-[#91A4B8]'
                    : status.pinch_state === 'pinched'
                    ? 'text-[#42F5A5] animate-pulse'
                    : status.pinch_state === 'cooldown'
                    ? 'text-[#FBBF24]'
                    : 'text-[#48DDF5]'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    !status.left_click_enabled || !status.enabled
                      ? 'bg-[#91A4B8]'
                      : status.pinch_state === 'pinched'
                      ? 'bg-[#42F5A5]'
                      : status.pinch_state === 'cooldown'
                      ? 'bg-[#FBBF24]'
                      : 'bg-[#48DDF5]'
                  }`}
                />
                {!status.enabled
                  ? 'Standby'
                  : !status.left_click_enabled
                  ? 'Disabled'
                  : status.pinch_state === 'pinched'
                  ? 'CLICKED'
                  : status.pinch_state === 'cooldown'
                  ? 'Cooldown'
                  : 'Ready'}
              </span>
              <span className="text-[10px] text-[#91A4B8] truncate">
                {status.pinch_distance !== null
                  ? `Dist: ${(status.pinch_distance * 100).toFixed(1)}% (act ≤ ${(status.pinch_activation_threshold * 100).toFixed(0)}%)`
                  : 'Dist: N/A'}
              </span>
            </div>

            {/* Cooldown Status */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Cooldown</span>
              <span className={`font-semibold flex items-center gap-1.5 truncate ${status.pinch_state === 'cooldown' ? 'text-[#FBBF24]' : 'text-[#42F5A5]'}`}>
                <Clock className="w-3 h-3 shrink-0" />
                {status.pinch_state === 'cooldown' ? 'Debouncing' : 'Ready'}
              </span>
              <span className="text-[10px] text-[#91A4B8]">{status.click_cooldown_ms}ms window</span>
            </div>

            {/* Last Click Event */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Last Click</span>
              <span className="text-white font-semibold truncate flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-[#42F5A5] shrink-0" />
                {status.last_click_position
                  ? `(${status.last_click_position.x}, ${status.last_click_position.y})`
                  : 'None yet'}
              </span>
              <span className="text-[10px] text-[#91A4B8]">Total: {status.click_count || 0}</span>
            </div>
          </div>

          {/* Pinch Thresholds & Cooldown Sliders */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-[rgba(148,180,210,0.08)]">
            {/* Activation Threshold Slider */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
                <span>Activation Threshold</span>
                <span className="text-[#48DDF5] font-bold">
                  {(status.pinch_activation_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.02"
                max="0.12"
                step="0.01"
                value={status.pinch_activation_threshold}
                onChange={(e) => updateSettings({ pinch_activation_threshold: parseFloat(e.target.value) })}
                className="w-full accent-[#48DDF5] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
              />
            </div>

            {/* Release Threshold Slider (Hysteresis) */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
                <span>Release (Hysteresis)</span>
                <span className="text-[#A78BFA] font-bold">
                  {(status.pinch_release_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.04"
                max="0.20"
                step="0.01"
                value={status.pinch_release_threshold}
                onChange={(e) => updateSettings({ pinch_release_threshold: parseFloat(e.target.value) })}
                className="w-full accent-[#A78BFA] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
              />
            </div>

            {/* Cooldown Duration Slider */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
                <span>Click Cooldown</span>
                <span className="text-[#42F5A5] font-bold">
                  {Math.round(status.click_cooldown_ms)}ms
                </span>
              </div>
              <input
                type="range"
                min="150"
                max="1000"
                step="50"
                value={status.click_cooldown_ms}
                onChange={(e) => updateSettings({ click_cooldown_ms: parseFloat(e.target.value) })}
                className="w-full accent-[#42F5A5] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* RIGHT CLICK CONTROL SECTION (PHASE 6B.2) */}
        <div className="p-4 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(245,158,11,0.25)] flex flex-col gap-3.5 shadow-lg">
          {/* Header & Independent Toggle */}
          <div className="flex items-center justify-between pb-2 border-b border-[rgba(148,180,210,0.08)]">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-[rgba(245,158,11,0.1)] text-[#F59E0B]">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white uppercase tracking-wider">
                    Gesture Right Click
                  </span>
                  <span className="text-[10px] text-[#FBBF24] font-mono px-1.5 py-0.5 rounded bg-[rgba(245,158,11,0.1)] border border-[rgba(245,158,11,0.2)]">
                    Phase 6B.2
                  </span>
                </div>
                <span className="text-[11px] text-[#91A4B8]">
                  Two Fingers (Victory) or Middle Pinch (L8 & L12)
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={toggleRightClick}
              disabled={!status.enabled}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors border ${
                !status.enabled
                  ? 'opacity-50 cursor-not-allowed bg-[rgba(11,18,32,0.4)] border-[rgba(148,180,210,0.1)] text-[#91A4B8]'
                  : status.right_click_enabled
                  ? 'bg-[rgba(245,158,11,0.15)] border-[#F59E0B]/40 text-[#FBBF24]'
                  : 'bg-[rgba(239,68,68,0.12)] border-[#EF4444]/30 text-[#F87171]'
              }`}
            >
              {status.right_click_enabled ? (
                <>
                  <ToggleRight className="w-4 h-4 text-[#FBBF24]" />
                  <span>Enabled</span>
                </>
              ) : (
                <>
                  <ToggleLeft className="w-4 h-4 text-[#F87171]" />
                  <span>Disabled</span>
                </>
              )}
            </button>
          </div>

          {/* Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            {/* Activation Gesture */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Gesture</span>
              <span className="text-white font-semibold flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] shrink-0" />
                Two Fingers
              </span>
              <span className="text-[10px] text-[#91A4B8]">Victory (L8 & L12)</span>
            </div>

            {/* Pinch Detection Status */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Pinch Status</span>
              <span
                className={`font-bold flex items-center gap-1.5 truncate ${
                  !status.right_click_enabled || !status.enabled
                    ? 'text-[#91A4B8]'
                    : status.right_pinch_state === 'pinched'
                    ? 'text-[#FBBF24] animate-pulse'
                    : status.right_pinch_state === 'cooldown'
                    ? 'text-[#48DDF5]'
                    : 'text-[#F59E0B]'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    !status.right_click_enabled || !status.enabled
                      ? 'bg-[#91A4B8]'
                      : status.right_pinch_state === 'pinched'
                      ? 'bg-[#FBBF24]'
                      : status.right_pinch_state === 'cooldown'
                      ? 'bg-[#48DDF5]'
                      : 'bg-[#F59E0B]'
                  }`}
                />
                {!status.enabled
                  ? 'Standby'
                  : !status.right_click_enabled
                  ? 'Disabled'
                  : status.right_pinch_state === 'pinched'
                  ? 'CLICKED'
                  : status.right_pinch_state === 'cooldown'
                  ? 'Cooldown'
                  : 'Ready'}
              </span>
              <span className="text-[10px] text-[#91A4B8] truncate">
                {status.right_pinch_distance !== null
                  ? `Dist: ${(status.right_pinch_distance * 100).toFixed(1)}% (act ≤ ${(status.right_pinch_activation_threshold * 100).toFixed(0)}%)`
                  : 'Dist: N/A'}
              </span>
            </div>

            {/* Cooldown Status */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Cooldown</span>
              <span className={`font-semibold flex items-center gap-1.5 truncate ${status.right_pinch_state === 'cooldown' ? 'text-[#48DDF5]' : 'text-[#42F5A5]'}`}>
                <Clock className="w-3 h-3 shrink-0" />
                {status.right_pinch_state === 'cooldown' ? 'Debouncing' : 'Ready'}
              </span>
              <span className="text-[10px] text-[#91A4B8]">{status.right_click_cooldown_ms}ms window</span>
            </div>

            {/* Last Right Click Event */}
            <div className="p-2 rounded-lg bg-[rgba(5,8,14,0.6)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-0.5">
              <span className="text-[#91A4B8] text-[10px] uppercase">Last Click</span>
              <span className="text-white font-semibold truncate flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-[#FBBF24] shrink-0" />
                {status.last_right_click_position
                  ? `(${status.last_right_click_position.x}, ${status.last_right_click_position.y})`
                  : 'None yet'}
              </span>
              <span className="text-[10px] text-[#91A4B8]">Total: {status.right_click_count || 0}</span>
            </div>
          </div>

          {/* Right Pinch Thresholds & Cooldown Sliders */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-[rgba(148,180,210,0.08)]">
            {/* Activation Threshold Slider */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
                <span>Activation Threshold</span>
                <span className="text-[#FBBF24] font-bold">
                  {(status.right_pinch_activation_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.02"
                max="0.12"
                step="0.01"
                value={status.right_pinch_activation_threshold}
                onChange={(e) => updateSettings({ right_pinch_activation_threshold: parseFloat(e.target.value) })}
                className="w-full accent-[#FBBF24] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
              />
            </div>

            {/* Release Threshold Slider (Hysteresis) */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
                <span>Release (Hysteresis)</span>
                <span className="text-[#F472B6] font-bold">
                  {(status.right_pinch_release_threshold * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.04"
                max="0.20"
                step="0.01"
                value={status.right_pinch_release_threshold}
                onChange={(e) => updateSettings({ right_pinch_release_threshold: parseFloat(e.target.value) })}
                className="w-full accent-[#F472B6] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
              />
            </div>

            {/* Cooldown Duration Slider */}
            <div className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-[11px] font-mono text-[#91A4B8]">
                <span>Click Cooldown</span>
                <span className="text-[#48DDF5] font-bold">
                  {Math.round(status.right_click_cooldown_ms)}ms
                </span>
              </div>
              <input
                type="range"
                min="150"
                max="1000"
                step="50"
                value={status.right_click_cooldown_ms}
                onChange={(e) => updateSettings({ right_click_cooldown_ms: parseFloat(e.target.value) })}
                className="w-full accent-[#48DDF5] cursor-pointer h-1.5 bg-[#05080E] rounded-lg"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Live Information & Telemetry - Full Width 6 Columns */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 text-[11px] font-mono">
        <div className="p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-0.5">
          <span className="text-[#91A4B8] flex items-center gap-1">
            <Activity className="w-3 h-3 text-[#48DDF5]" />
            Hand Detected
          </span>
          <span className={`font-bold ${status.hand_detected ? 'text-[#42F5A5]' : 'text-[#91A4B8]'}`}>
            {status.hand_detected ? 'YES (Index Tip)' : 'NO (Stopped)'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-0.5">
          <span className="text-[#91A4B8] flex items-center gap-1">
            <Move className="w-3 h-3 text-[#A78BFA]" />
            Control Point
          </span>
          <span className="text-white font-bold truncate">
            {status.control_point
              ? `X: ${status.control_point.x.toFixed(2)} | Y: ${status.control_point.y.toFixed(2)}`
              : 'N/A'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-0.5">
          <span className="text-[#91A4B8] flex items-center gap-1">
            <MousePointer className="w-3 h-3 text-[#42F5A5]" />
            Cursor (Px)
          </span>
          <span className="text-white font-bold">
            {status.cursor_position.x}, {status.cursor_position.y}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-0.5">
          <span className="text-[#91A4B8] flex items-center gap-1">
            <Monitor className="w-3 h-3 text-[#FFEA00]" />
            Display Resolution
          </span>
          <span className="text-white font-bold">
            {status.screen_size.width} × {status.screen_size.height}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-0.5">
          <span className="text-[#91A4B8] flex items-center gap-1">
            <Layers className="w-3 h-3 text-[#38BDF8]" />
            Camera Owner
          </span>
          <span className="text-white font-bold uppercase">
            {useCameraStore.getState().cameraOwner}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)] flex flex-col gap-0.5">
          <span className="text-[#91A4B8] flex items-center gap-1">
            <Activity className="w-3 h-3 text-[#A855F7]" />
            Background Mode
          </span>
          <span className={`font-bold ${status.enabled ? 'text-[#42F5A5]' : 'text-[#91A4B8]'}`}>
            {status.enabled ? 'Independent (OS)' : 'Standby'}
          </span>
        </div>
      </div>

      {/* Safety Note */}
      <div className="text-[10px] text-[#91A4B8] flex items-center gap-1.5 px-2.5 py-2 rounded-lg bg-[rgba(11,18,32,0.4)] border border-[rgba(148,180,210,0.08)]">
        <ShieldCheck className="w-3.5 h-3.5 text-[#42F5A5] shrink-0" />
        <span>Safety active: Cursor halts immediately when hand disappears (150ms TTL)</span>
      </div>
    </Card>
  );
};
