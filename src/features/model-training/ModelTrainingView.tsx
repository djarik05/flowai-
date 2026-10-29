import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu,
  Layers,
  Database,
  Play,
  Square,
  RotateCcw,
  Plus,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { useTrainingStore } from '../../store/trainingStore';
import { useActivityStore } from '../../store/activityStore';
import { ModelType, MODEL_TYPE_LABELS, MODEL_TYPE_DESCRIPTIONS } from '../../types/training';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Select } from '../../components/ui/Select';
import { Slider } from '../../components/ui/Slider';

export const ModelTrainingView: React.FC = () => {
  const {
    dataset,
    config,
    status,
    currentEpoch,
    metrics,
    updateConfig,
    startSimulatedTraining,
    stopTraining,
    resetTraining,
  } = useTrainingStore();

  const { addLog } = useActivityStore();
  const [collectionModal, setCollectionModal] = useState(false);

  const isTraining = status === 'training';
  const latestMetric = metrics[metrics.length - 1];

  const handleStart = () => {
    startSimulatedTraining();
    addLog({
      category: 'model',
      description: `Simulated training pipeline started: ${MODEL_TYPE_LABELS[config.modelType]} (${config.epochs} epochs)`,
      status: 'info',
      isSimulated: true,
    });
  };

  const handleStop = () => {
    stopTraining();
    addLog({
      category: 'model',
      description: 'Simulated training pipeline halted by user',
      status: 'warning',
      isSimulated: true,
    });
  };

  // SVG Chart points calculation
  const totalEpochs = config.epochs || 50;
  const chartWidth = 500;
  const chartHeight = 160;

  const getPointsString = (key: 'trainLoss' | 'valLoss' | 'trainAccuracy' | 'valAccuracy') => {
    if (metrics.length === 0) return '';
    return metrics
      .map((m) => {
        const x = (m.epoch / totalEpochs) * chartWidth;
        let y = 0;
        if (key.includes('Loss')) {
          // Loss from 0.0 to 2.0
          y = chartHeight - (Math.min(2.0, m[key]) / 2.0) * (chartHeight - 20) - 10;
        } else {
          // Accuracy from 0 to 100%
          y = chartHeight - (m[key] / 100) * (chartHeight - 20) - 10;
        }
        return `${x},${y}`;
      })
      .join(' ');
  };

  return (
    <div className="w-full flex flex-col gap-6 select-none">
      {/* Top Banner Notice */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass rounded-2xl p-5 border border-[rgba(148,180,210,0.18)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-5 h-5 text-[#48DDF5]" />
            <h2 className="text-lg font-bold text-white">Neural Gesture Training Studio</h2>
            <Badge variant="warning">Backend Not Connected — Prototype Preview</Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            Prepare dataset splits, configure model hyperparameters, and preview training curves.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {isTraining ? (
            <Button
              variant="danger"
              size="sm"
              onClick={handleStop}
              icon={<Square className="w-3.5 h-3.5" />}
            >
              Stop Training
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              onClick={handleStart}
              icon={<Play className="w-3.5 h-3.5" />}
            >
              Start Simulated Training
            </Button>
          )}

          <Button
            variant="secondary"
            size="sm"
            onClick={resetTraining}
            disabled={isTraining}
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Reset
          </Button>
        </div>
      </div>

      {/* Main Grid: Dataset Panel, Hyperparameters, and Live Metrics Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Dataset Metadata & Hyperparameters (Col 5) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* Dataset Panel */}
          <Card variant="glass" className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-[rgba(148,180,210,0.12)] mb-4">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#42F5A5]" />
                <h3 className="text-sm font-bold text-white">Dataset Manifest</h3>
              </div>
              <Badge variant="cyan">Sample V1.4</Badge>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-[rgba(148,180,210,0.08)]">
                <span className="text-[#91A4B8]">Corpus Name</span>
                <span className="text-white font-mono">{dataset.name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[rgba(148,180,210,0.08)]">
                <span className="text-[#91A4B8]">Classes Registered</span>
                <span className="text-[#48DDF5] font-bold">{dataset.gestureClasses} Gesture Poses</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[rgba(148,180,210,0.08)]">
                <span className="text-[#91A4B8]">Total Sample Frames</span>
                <span className="text-white font-mono">{dataset.totalSamples.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[rgba(148,180,210,0.08)]">
                <span className="text-[#91A4B8]">Class Balance Rating</span>
                <span className="text-[#42F5A5]">98.2% Optimal</span>
              </div>
            </div>

            {/* Class distribution progress bars */}
            <div className="mt-4 pt-3 border-t border-[rgba(148,180,210,0.1)]">
              <span className="text-[11px] font-semibold text-[#91A4B8] block mb-2">
                Sample Distribution by Pose
              </span>
              <div className="space-y-1.5">
                {Object.entries(dataset.balance).slice(0, 4).map(([className, count]) => (
                  <div key={className} className="flex items-center justify-between text-[10px]">
                    <span className="text-[#91A4B8] w-24 truncate">{className}</span>
                    <div className="flex-1 mx-2 h-1.5 bg-[#0B1220] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-[#48DDF5] to-[#42F5A5]"
                        style={{ width: `${(count / 1600) * 100}%` }}
                      />
                    </div>
                    <span className="text-white font-mono w-10 text-right">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => alert('Sample Collection Wizard is simulated for this frontend preview.')}
              icon={<Plus className="w-3.5 h-3.5" />}
              className="w-full mt-4 text-xs"
            >
              Add Gesture Class
            </Button>
          </Card>

          {/* Hyperparameters Configuration Card */}
          <Card variant="glass" className="p-5">
            <h3 className="text-sm font-bold text-white mb-3">Model Architecture & Tuning</h3>

            <div className="space-y-4">
              <Select
                label="Model Classifier"
                value={config.modelType}
                onChange={(val) => updateConfig({ modelType: val as ModelType })}
                options={[
                  {
                    value: 'mlp_landmark',
                    label: MODEL_TYPE_LABELS.mlp_landmark,
                    description: MODEL_TYPE_DESCRIPTIONS.mlp_landmark,
                  },
                  {
                    value: 'temporal_gesture',
                    label: MODEL_TYPE_LABELS.temporal_gesture,
                    description: MODEL_TYPE_DESCRIPTIONS.temporal_gesture,
                  },
                  {
                    value: 'cnn_experimental',
                    label: MODEL_TYPE_LABELS.cnn_experimental,
                    description: MODEL_TYPE_DESCRIPTIONS.cnn_experimental,
                  },
                ]}
              />

              <div className="grid grid-cols-2 gap-4">
                <Slider
                  label="Epochs"
                  min={10}
                  max={200}
                  step={10}
                  value={config.epochs}
                  disabled={isTraining}
                  onChange={(val) => updateConfig({ epochs: val })}
                />

                <Slider
                  label="Batch Size"
                  min={8}
                  max={128}
                  step={8}
                  value={config.batchSize}
                  disabled={isTraining}
                  onChange={(val) => updateConfig({ batchSize: val })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Slider
                  label="Learning Rate"
                  min={0.0001}
                  max={0.01}
                  step={0.0005}
                  value={config.learningRate}
                  disabled={isTraining}
                  onChange={(val) => updateConfig({ learningRate: val })}
                  formatValue={(v) => v.toFixed(4)}
                />

                <Slider
                  label="Seq Length"
                  min={10}
                  max={60}
                  step={5}
                  value={config.sequenceLength}
                  disabled={isTraining}
                  onChange={(val) => updateConfig({ sequenceLength: val })}
                />
              </div>

              <div className="text-[11px] text-[#91A4B8] pt-2 flex justify-between border-t border-[rgba(148,180,210,0.1)]">
                <span>Dataset Split (Train / Val / Test)</span>
                <span className="font-mono text-[#48DDF5]">70% / 15% / 15%</span>
              </div>
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN: Real-Time Charts & Training Progress (Col 7) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <Card variant="glass-strong" className="p-6">
            <div className="flex items-center justify-between pb-4 border-b border-[rgba(148,180,210,0.12)] mb-5">
              <div>
                <h3 className="text-sm font-bold text-white">Training Metrics Visualization</h3>
                <span className="text-xs text-[#91A4B8]">
                  {status === 'training'
                    ? `Epoch ${currentEpoch} / ${config.epochs} — Simulating gradient descent`
                    : status === 'completed'
                    ? `Training Completed at Epoch ${currentEpoch}`
                    : 'Awaiting pipeline execution'}
                </span>
              </div>

              <Badge
                variant={
                  status === 'completed' ? 'green' : status === 'training' ? 'cyan' : 'muted'
                }
                dot={status === 'training'}
              >
                {status.toUpperCase()}
              </Badge>
            </div>

            {/* Quick Summary KPIs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              <div className="p-3 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)]">
                <span className="text-[10px] text-[#91A4B8] uppercase">Train Loss</span>
                <div className="text-base font-bold text-[#48DDF5] font-mono mt-0.5">
                  {latestMetric ? latestMetric.trainLoss.toFixed(4) : '—'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)]">
                <span className="text-[10px] text-[#91A4B8] uppercase">Val Loss</span>
                <div className="text-base font-bold text-[#9B7CFF] font-mono mt-0.5">
                  {latestMetric ? latestMetric.valLoss.toFixed(4) : '—'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)]">
                <span className="text-[10px] text-[#91A4B8] uppercase">Train Accuracy</span>
                <div className="text-base font-bold text-[#42F5A5] font-mono mt-0.5">
                  {latestMetric ? `${latestMetric.trainAccuracy.toFixed(1)}%` : '—'}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.1)]">
                <span className="text-[10px] text-[#91A4B8] uppercase">Val Accuracy</span>
                <div className="text-base font-bold text-[#FFCB70] font-mono mt-0.5">
                  {latestMetric ? `${latestMetric.valAccuracy.toFixed(1)}%` : '—'}
                </div>
              </div>
            </div>

            {/* CHART 1: Loss Curve */}
            <div className="mb-6">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="font-semibold text-white">Cross-Entropy Loss Curve</span>
                <div className="flex items-center gap-3 text-[10px] font-mono">
                  <span className="flex items-center gap-1 text-[#48DDF5]">
                    <span className="w-2 h-0.5 bg-[#48DDF5]" /> Train
                  </span>
                  <span className="flex items-center gap-1 text-[#9B7CFF]">
                    <span className="w-2 h-0.5 bg-[#9B7CFF]" /> Val
                  </span>
                </div>
              </div>

              <div className="w-full h-40 bg-[rgba(7,11,18,0.7)] rounded-xl border border-[rgba(148,180,210,0.12)] p-2 relative overflow-hidden">
                {metrics.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-[#61758B]">
                    Click "Start Simulated Training" to generate real-time metrics
                  </div>
                ) : (
                  <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-full overflow-visible">
                    <polyline
                      fill="none"
                      stroke="#48DDF5"
                      strokeWidth="2"
                      points={getPointsString('trainLoss')}
                    />
                    <polyline
                      fill="none"
                      stroke="#9B7CFF"
                      strokeWidth="2"
                      strokeDasharray="4 2"
                      points={getPointsString('valLoss')}
                    />
                  </svg>
                )}
              </div>
            </div>

            {/* CHART 2: Accuracy Curve */}
            <div>
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="font-semibold text-white">Classification Accuracy (%)</span>
                <div className="flex items-center gap-3 text-[10px] font-mono">
                  <span className="flex items-center gap-1 text-[#42F5A5]">
                    <span className="w-2 h-0.5 bg-[#42F5A5]" /> Train
                  </span>
                  <span className="flex items-center gap-1 text-[#FFCB70]">
                    <span className="w-2 h-0.5 bg-[#FFCB70]" /> Val
                  </span>
                </div>
              </div>

              <div className="w-full h-40 bg-[rgba(7,11,18,0.7)] rounded-xl border border-[rgba(148,180,210,0.12)] p-2 relative overflow-hidden">
                {metrics.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-[#61758B]">
                    Awaiting training execution
                  </div>
                ) : (
                  <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-full overflow-visible">
                    <polyline
                      fill="none"
                      stroke="#42F5A5"
                      strokeWidth="2"
                      points={getPointsString('trainAccuracy')}
                    />
                    <polyline
                      fill="none"
                      stroke="#FFCB70"
                      strokeWidth="2"
                      strokeDasharray="4 2"
                      points={getPointsString('valAccuracy')}
                    />
                  </svg>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
