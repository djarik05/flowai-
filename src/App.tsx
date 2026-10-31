import React, { Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from './store/appStore';
import { AppLayout } from './components/layout/AppLayout';

// Route-based lazy loaded views for code splitting
const DashboardView = React.lazy(() =>
  import('./features/dashboard/DashboardView').then((m) => ({ default: m.DashboardView }))
);
const LiveControlView = React.lazy(() =>
  import('./features/live-control/LiveControlView').then((m) => ({ default: m.LiveControlView }))
);
const GestureManagerView = React.lazy(() =>
  import('./features/gesture-manager/GestureManagerView').then((m) => ({ default: m.GestureManagerView }))
);
const ModelTrainingView = React.lazy(() =>
  import('./features/model-training/ModelTrainingView').then((m) => ({ default: m.ModelTrainingView }))
);
const ActivityLogsView = React.lazy(() =>
  import('./features/activity-logs/ActivityLogsView').then((m) => ({ default: m.ActivityLogsView }))
);
const SettingsView = React.lazy(() =>
  import('./features/settings/SettingsView').then((m) => ({ default: m.SettingsView }))
);
const InitializationScreen = React.lazy(() =>
  import('./features/initialization/InitializationScreen').then((m) => ({ default: m.InitializationScreen }))
);

const ViewLoadingFallback: React.FC = () => (
  <div className="w-full flex-1 min-h-[400px] flex flex-col items-center justify-center gap-3 select-none">
    <div className="relative w-10 h-10 flex items-center justify-center">
      <div className="absolute inset-0 rounded-full border-2 border-[rgba(72,221,245,0.15)] border-t-[#48DDF5] animate-spin" />
      <div className="w-3 h-3 rounded-full bg-[#48DDF5]/40 animate-pulse" />
    </div>
    <span className="text-xs text-[#91A4B8] font-mono tracking-wider">Loading view...</span>
  </div>
);

export function App() {
  const { currentView } = useAppStore();

  if (currentView === 'initialization') {
    return (
      <Suspense fallback={<ViewLoadingFallback />}>
        <InitializationScreen />
      </Suspense>
    );
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView key="dashboard" />;
      case 'live-control':
        return <LiveControlView key="live-control" />;
      case 'gesture-manager':
        return <GestureManagerView key="gesture-manager" />;
      case 'model-training':
        return <ModelTrainingView key="model-training" />;
      case 'activity-logs':
        return <ActivityLogsView key="activity-logs" />;
      case 'settings':
        return <SettingsView key="settings" />;
      default:
        return <DashboardView key="dashboard" />;
    }
  };

  return (
    <AppLayout>
      {/* Persistent Dashboard container: stays mounted so webcam tracking and mouse control
          continue uninterrupted when navigating between in-app tabs (Settings, Logs, Training). */}
      <div className={currentView === 'dashboard' ? 'w-full flex-1 flex flex-col' : 'hidden'}>
        <Suspense fallback={<ViewLoadingFallback />}>
          <DashboardView />
        </Suspense>
      </div>

      {currentView !== 'dashboard' && (
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="w-full flex-1 flex flex-col"
          >
            <Suspense fallback={<ViewLoadingFallback />}>
              {renderCurrentView()}
            </Suspense>
          </motion.div>
        </AnimatePresence>
      )}
    </AppLayout>
  );
}

export default App;
