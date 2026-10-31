import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cpu,
  Layers,
  Database,
  Sliders,
  Activity,
  Award,
  Zap,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  LayoutDashboard,
} from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { DatasetReadinessCard } from './DatasetReadinessCard';
import { TrainingConfigPanel } from './TrainingConfigPanel';
import { TrainingMonitorPanel } from './TrainingMonitorPanel';
import { EvaluationDashboard } from './EvaluationDashboard';
import { ModelRegistryTable } from './ModelRegistryTable';
import { LiveRecognitionHUD } from './LiveRecognitionHUD';
import { Badge } from '../../components/ui/Badge';

export type ModelTrainingTab = 'overview' | 'train' | 'evaluate' | 'registry' | 'hud';

export const ModelTrainingView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ModelTrainingTab>('overview');
  const {
    readiness,
    activeModel,
    isTraining,
    error,
    fetchReadiness,
    fetchModels,
    fetchActiveModel,
    fetchClassifierStatus,
    clearError,
  } = useClassifierStore();

  useEffect(() => {
    fetchReadiness();
    fetchModels();
    fetchActiveModel();
    fetchClassifierStatus();
  }, [fetchReadiness, fetchModels, fetchActiveModel, fetchClassifierStatus]);

  const isReady = readiness?.is_training_ready ?? false;

  return (
    <div className="w-full flex flex-col gap-6 select-none pb-12">
      {/* Top Banner Notice */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass rounded-2xl p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-5 h-5 text-[#48DDF5]" />
            <h2 className="text-lg font-bold text-white tracking-wide">
              Neural Gesture Training Studio
            </h2>
            <Badge variant="green">Phase 4 Active</Badge>
            {isTraining && (
              <Badge variant="cyan" className="animate-pulse">
                Training In Progress
              </Badge>
            )}
          </div>
          <p className="text-xs text-[#91A4B8]">
            Train translation- and scale-invariant MLP classifiers on 63-dimensional MediaPipe 3D hand coordinates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {activeModel ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#10B981]/10 border border-[#10B981]/30">
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
              <div className="text-left">
                <span className="text-[10px] text-[#91A4B8] block leading-none">Active Model</span>
                <span className="text-xs font-mono font-bold text-white">
                  {activeModel.model_name}
                </span>
              </div>
            </div>
          ) : (
            <div className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-[#91A4B8]">
              No active model loaded
            </div>
          )}

          <div
            className={`px-3 py-1.5 rounded-xl text-xs font-mono border ${
              isReady
                ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]'
                : 'bg-[#EF4444]/10 border-[#EF4444]/30 text-[#EF4444]'
            }`}
          >
            {isReady ? 'Dataset Ready' : 'Dataset Incomplete'}
          </div>
        </div>
      </div>

      {/* Global Error Alert */}
      {error && (
        <div className="p-3.5 rounded-xl bg-[#EF4444]/15 border border-[#EF4444]/30 flex items-center justify-between text-xs text-[#FCA5A5]">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#EF4444] shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => clearError()}
            className="text-xs text-[#91A4B8] hover:text-white px-2 py-1 rounded bg-white/5"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-[rgba(148,180,210,0.12)]">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            activeTab === 'overview'
              ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
              : 'text-[#91A4B8] hover:text-white hover:bg-white/5 border border-transparent'
          }`}
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          Full Studio
        </button>

        <button
          onClick={() => setActiveTab('train')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            activeTab === 'train'
              ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
              : 'text-[#91A4B8] hover:text-white hover:bg-white/5 border border-transparent'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          Train &amp; Monitor
          {isTraining && <span className="w-1.5 h-1.5 rounded-full bg-[#00E5FF] animate-ping" />}
        </button>

        <button
          onClick={() => setActiveTab('evaluate')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            activeTab === 'evaluate'
              ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
              : 'text-[#91A4B8] hover:text-white hover:bg-white/5 border border-transparent'
          }`}
        >
          <Award className="w-3.5 h-3.5" />
          Evaluation &amp; Matrix
        </button>

        <button
          onClick={() => setActiveTab('registry')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            activeTab === 'registry'
              ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
              : 'text-[#91A4B8] hover:text-white hover:bg-white/5 border border-transparent'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Model Registry
        </button>

        <button
          onClick={() => setActiveTab('hud')}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            activeTab === 'hud'
              ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
              : 'text-[#91A4B8] hover:text-white hover:bg-white/5 border border-transparent'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          Live Recognition HUD
        </button>
      </div>

      {/* Tab Contents */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex flex-col gap-6"
          >
            {/* Module A: Dataset Readiness */}
            <DatasetReadinessCard />

            {/* Two-column layout for Config and Live Monitor */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <TrainingConfigPanel />
              <TrainingMonitorPanel />
            </div>

            {/* Module D: Evaluation & Confusion Matrix */}
            <EvaluationDashboard />

            {/* Module E: Model Registry */}
            <ModelRegistryTable />

            {/* Module F: Live Recognition HUD */}
            <LiveRecognitionHUD />
          </motion.div>
        )}

        {activeTab === 'train' && (
          <motion.div
            key="train"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex flex-col gap-6"
          >
            <DatasetReadinessCard />
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <TrainingConfigPanel />
              <TrainingMonitorPanel />
            </div>
          </motion.div>
        )}

        {activeTab === 'evaluate' && (
          <motion.div
            key="evaluate"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex flex-col gap-6"
          >
            <EvaluationDashboard />
            <ModelRegistryTable />
          </motion.div>
        )}

        {activeTab === 'registry' && (
          <motion.div
            key="registry"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex flex-col gap-6"
          >
            <ModelRegistryTable />
            <EvaluationDashboard />
          </motion.div>
        )}

        {activeTab === 'hud' && (
          <motion.div
            key="hud"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex flex-col gap-6"
          >
            <LiveRecognitionHUD />
            <ModelRegistryTable />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
