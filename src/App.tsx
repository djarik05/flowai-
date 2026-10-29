import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from './store/appStore';
import { InitializationScreen } from './features/initialization/InitializationScreen';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardView } from './features/dashboard/DashboardView';
import { LiveControlView } from './features/live-control/LiveControlView';
import { GestureManagerView } from './features/gesture-manager/GestureManagerView';
import { ModelTrainingView } from './features/model-training/ModelTrainingView';
import { ActivityLogsView } from './features/activity-logs/ActivityLogsView';
import { SettingsView } from './features/settings/SettingsView';

export function App() {
  const { currentView } = useAppStore();

  if (currentView === 'initialization') {
    return <InitializationScreen />;
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
      <AnimatePresence mode="wait">
        <motion.div
          key={currentView}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="w-full flex-1 flex flex-col"
        >
          {renderCurrentView()}
        </motion.div>
      </AnimatePresence>
    </AppLayout>
  );
}

export default App;
