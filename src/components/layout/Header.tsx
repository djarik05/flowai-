import React from 'react';
import {
  Sparkles,
  LayoutDashboard,
  Radio,
  Hand,
  Cpu,
  ScrollText,
  Settings,
  EyeOff,
  PowerOff,
  AlertOctagon,
} from 'lucide-react';
import { useAppStore, AppView } from '../../store/appStore';
import { useSettingsStore } from '../../store/settingsStore';
import { useActivityStore } from '../../store/activityStore';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface NavItem {
  id: AppView;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Home', icon: LayoutDashboard },
  { id: 'live-control', label: 'Live Control', icon: Radio },
  { id: 'gesture-manager', label: 'Gestures', icon: Hand },
  { id: 'model-training', label: 'Train Model', icon: Cpu },
  { id: 'activity-logs', label: 'Activity Logs', icon: ScrollText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

import { useMouseStore } from '../../store/mouseStore';

export const Header: React.FC = () => {
  const { currentView, setCurrentView, setUIMinimized, trackingStatus } = useAppStore();
  const { settings, updateController } = useSettingsStore();
  const { addLog } = useActivityStore();

  const handleEmergencyStop = () => {
    updateController({ enabled: false });
    // Phase 6A.3: Immediate hardware emergency stop on backend
    useMouseStore.getState().emergencyStop().catch(console.error);
    addLog({
      category: 'controller',
      description: 'Emergency Stop triggered: Desktop mouse control halted immediately',
      status: 'error',
      isSimulated: false,
    });
  };

  return (
    <header className="sticky top-0 z-40 w-full glass-strong border-b border-[rgba(148,180,210,0.16)] px-4 lg:px-6 py-2.5 flex items-center justify-between gap-4">
      {/* Brand logo & title */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={() => setCurrentView('dashboard')}
          className="flex items-center gap-2.5 text-left group cursor-pointer"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#48DDF5] to-[#42F5A5] p-0.5 shadow-[0_0_12px_rgba(72,221,245,0.3)] group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#070B12] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-[#48DDF5]" />
            </div>
          </div>
          <div className="hidden sm:block">
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1">
              GestureFlow <span className="text-[#48DDF5]">AI</span>
            </h1>
            <p className="text-[10px] text-[#91A4B8]">Webcam Controller</p>
          </div>
        </button>

        <Badge variant="cyan" className="hidden md:inline-flex" dot>
          Demo Mode
        </Badge>
      </div>

      {/* Main Navigation Links */}
      <nav className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-[rgba(72,221,245,0.14)] text-[#48DDF5] border border-[rgba(72,221,245,0.3)] shadow-[0_0_12px_rgba(72,221,245,0.15)]'
                  : 'text-[#91A4B8] hover:text-[#F1F5F9] hover:bg-[rgba(148,180,210,0.08)] border border-transparent'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right side controls: Status, Hide UI, Emergency Stop */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Controller Status Indicator */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.12)] text-[11px]">
          <span
            className={`w-2 h-2 rounded-full ${
              settings.controller.enabled ? 'bg-[#42F5A5] animate-pulse' : 'bg-[#61758B]'
            }`}
          />
          <span className="text-[#91A4B8]">
            {settings.controller.enabled ? 'Controller Active' : 'Controller Standby'}
          </span>
        </div>

        {/* Hide UI (Background Simulation) Action */}
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setUIMinimized(true)}
          icon={<EyeOff className="w-3.5 h-3.5" />}
          title="Minimize to background mode overlay (Simulated)"
          className="text-xs"
        >
          <span className="hidden sm:inline">Hide UI</span>
        </Button>

        {/* Emergency Stop Button */}
        <Button
          variant="danger"
          size="sm"
          onClick={handleEmergencyStop}
          icon={<AlertOctagon className="w-3.5 h-3.5" />}
          title="Immediate halt of all simulated mouse & click actions"
          className="text-xs"
        >
          <span className="hidden sm:inline">Stop</span>
        </Button>
      </div>
    </header>
  );
};
