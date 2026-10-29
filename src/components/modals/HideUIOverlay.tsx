import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, ShieldAlert, Sparkles, Activity, AlertOctagon } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { useSettingsStore } from '../../store/settingsStore';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export const HideUIOverlay: React.FC = () => {
  const { isUIMinimized, setUIMinimized, trackingStatus } = useAppStore();
  const { settings, updateController } = useSettingsStore();

  if (!isUIMinimized) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 pointer-events-none flex flex-col justify-end p-6">
        {/* Floating compact desktop overlay widget */}
        <motion.div
          initial={{ y: 50, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 50, opacity: 0, scale: 0.95 }}
          className="pointer-events-auto self-end w-full max-w-md glass-strong rounded-2xl border border-[rgba(72,221,245,0.3)] shadow-[0_12px_40px_rgba(0,0,0,0.7)] p-4 flex flex-col gap-3 backdrop-blur-xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-[#48DDF5] to-[#42F5A5] flex items-center justify-center p-0.5">
                <div className="w-full h-full bg-[#070B12] rounded-[6px] flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5 text-[#48DDF5]" />
                </div>
              </div>
              <span className="text-xs font-bold text-white">GestureFlow AI (Background Mode)</span>
            </div>

            <Badge variant="cyan" dot>
              Simulated Tray
            </Badge>
          </div>

          {/* Educational notice regarding desktop runtime integration */}
          <div className="text-[11px] text-[#91A4B8] bg-[rgba(11,18,32,0.85)] p-2.5 rounded-xl border border-[rgba(148,180,210,0.12)]">
            <div className="flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-[#FFCB70] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[#F1F5F9] block font-medium mb-0.5">
                  Frontend Prototype Demonstration
                </strong>
                True background system tray minimization and OS-wide global hotkeys require the
                future Python / Electron desktop runtime.
              </div>
            </div>
          </div>

          {/* Active telemetry readout */}
          <div className="flex items-center justify-between text-xs font-mono text-[#91A4B8] bg-[rgba(18,29,45,0.6)] px-3 py-2 rounded-lg border border-[rgba(148,180,210,0.1)]">
            <div className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-[#42F5A5] animate-pulse" />
              <span>Simulated Hand:</span>
              <span className="text-[#48DDF5]">
                {trackingStatus.currentGesture?.name || 'Tracking Active'}
              </span>
            </div>
            <span className="text-[#42F5A5]">
              {settings.controller.enabled ? 'Controller ON' : 'Standby'}
            </span>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-between gap-3 pt-1">
            <Button
              variant="danger"
              size="sm"
              onClick={() => updateController({ enabled: false })}
              icon={<AlertOctagon className="w-3.5 h-3.5" />}
            >
              Emergency Halt
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setUIMinimized(false)}
              icon={<Eye className="w-3.5 h-3.5" />}
            >
              Restore Interface
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
