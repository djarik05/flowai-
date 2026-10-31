import React from 'react';
import { Sliders, Play, Lock, AlertCircle, Info } from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Slider } from '../../components/ui/Slider';
import { Switch } from '../../components/ui/Switch';

export const TrainingConfigPanel: React.FC = () => {
  const {
    config,
    readiness,
    isTraining,
    updateConfig,
    startTraining,
  } = useClassifierStore();

  const isReady = readiness?.is_training_ready ?? false;

  const handleEpochsChange = (val: number) => {
    updateConfig({ epochs: val });
  };

  const handleThresholdChange = (val: number) => {
    updateConfig({ confidence_threshold: val / 100 });
  };

  return (
    <Card className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(148,180,210,0.12)]">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-[#48DDF5]" />
          <h3 className="text-base font-bold text-white tracking-wide">
            Module B: Hyperparameter Configuration
          </h3>
        </div>
        <span className="text-xs font-mono text-[#00E5FF] bg-[#00E5FF]/10 px-2.5 py-1 rounded-lg border border-[#00E5FF]/20">
          Architecture: 63-D &rarr; 128 &rarr; 64 &rarr; {readiness?.ready_classes_count ?? 'N'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left Column: Model Name & Core Hyperparameters */}
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-[#91A4B8] block mb-1.5">
              Model Identifier Name
            </label>
            <input
              type="text"
              value={config.model_name}
              onChange={(e) => updateConfig({ model_name: e.target.value })}
              disabled={isTraining}
              className="w-full px-3 py-2 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.2)] text-white text-xs font-mono focus:outline-none focus:border-[#48DDF5]"
              placeholder="e.g. GestureMLP_v1"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-[#91A4B8]">
                Training Epochs: <span className="text-white font-mono">{config.epochs}</span>
              </label>
              <span className="text-[11px] text-[#6B7280]">10 – 100</span>
            </div>
            <Slider
              min={10}
              max={100}
              step={5}
              value={config.epochs}
              onChange={handleEpochsChange}
              disabled={isTraining}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-[#91A4B8] block mb-1.5">
                Batch Size
              </label>
              <select
                value={config.batch_size}
                onChange={(e) => updateConfig({ batch_size: Number(e.target.value) })}
                disabled={isTraining}
                className="w-full px-3 py-2 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.2)] text-white text-xs font-mono focus:outline-none focus:border-[#48DDF5]"
              >
                <option value={8}>8 samples</option>
                <option value={16}>16 samples (Recommended)</option>
                <option value={32}>32 samples</option>
                <option value={64}>64 samples</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#91A4B8] block mb-1.5">
                Learning Rate (Adam)
              </label>
              <select
                value={config.learning_rate}
                onChange={(e) => updateConfig({ learning_rate: Number(e.target.value) })}
                disabled={isTraining}
                className="w-full px-3 py-2 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.2)] text-white text-xs font-mono focus:outline-none focus:border-[#48DDF5]"
              >
                <option value={0.0005}>0.0005 (Fine)</option>
                <option value={0.001}>0.001 (Default)</option>
                <option value={0.002}>0.002 (Fast)</option>
                <option value={0.005}>0.005 (Aggressive)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Right Column: Splits, Threshold, Session-Aware Splitting */}
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-semibold text-[#91A4B8]">
                Inference Confidence Threshold:{' '}
                <span className="text-[#00E5FF] font-mono">
                  {(config.confidence_threshold * 100).toFixed(0)}%
                </span>
              </label>
              <span className="text-[11px] text-[#6B7280]">50% – 95%</span>
            </div>
            <Slider
              min={50}
              max={95}
              step={5}
              value={Math.round(config.confidence_threshold * 100)}
              onChange={handleThresholdChange}
              disabled={isTraining}
            />
            <span className="text-[10px] text-[#91A4B8] mt-1 block">
              Predictions below this confidence are filtered out as "Unknown" to prevent false triggers.
            </span>
          </div>

          <div>
            <label className="text-xs font-semibold text-[#91A4B8] block mb-1.5">
              Dataset Partitioning
            </label>
            <div className="p-2.5 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)] flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 font-mono">
                <span className="text-[#10B981]">70% Train</span>
                <span className="text-[#6B7280]">•</span>
                <span className="text-[#3B82F6]">15% Val</span>
                <span className="text-[#6B7280]">•</span>
                <span className="text-[#F59E0B]">15% Test</span>
              </div>
              <span className="text-[11px] text-[#91A4B8]">Independent Holdout</span>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
            <div className="flex flex-col pr-3">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-white">Session-Aware Partitioning</span>
                <Info className="w-3.5 h-3.5 text-[#91A4B8]" />
              </div>
              <span className="text-[11px] text-[#91A4B8] mt-0.5">
                Keeps recording sessions isolated across splits to prevent temporal data leakage.
              </span>
            </div>
            <Switch
              checked={config.session_aware_split}
              onChange={(checked) => updateConfig({ session_aware_split: checked })}
              disabled={isTraining}
            />
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="mt-5 pt-4 border-t border-[rgba(148,180,210,0.12)] flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="text-xs text-[#91A4B8] flex items-center gap-1.5">
          {!isReady && (
            <span className="text-[#EF4444] flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              Training disabled: Audit report requires $\ge 2$ classes with valid 3D samples.
            </span>
          )}
          {isReady && !isTraining && (
            <span className="text-[#10B981] flex items-center gap-1">
              Ready: All requirements met for training.
            </span>
          )}
          {isTraining && (
            <span className="text-[#00E5FF] animate-pulse">
              Training job running in background...
            </span>
          )}
        </div>

        <Button
          size="md"
          variant="primary"
          onClick={() => startTraining()}
          disabled={!isReady || isTraining}
          className="w-full sm:w-auto px-6 py-2.5 font-bold flex items-center justify-center gap-2 bg-gradient-to-r from-[#00E5FF] to-[#0091FF] text-black shadow-lg shadow-[#00E5FF]/20"
        >
          {isTraining ? (
            <>
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
              Training MLP Classifier...
            </>
          ) : !isReady ? (
            <>
              <Lock className="w-4 h-4" />
              Dataset Not Ready
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-black" />
              Start Neural Training
            </>
          )}
        </Button>
      </div>
    </Card>
  );
};
