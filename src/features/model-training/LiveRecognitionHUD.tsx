import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  Zap,
  Gauge,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  Fingerprint,
} from 'lucide-react';
import { useClassifierStore } from '../../store/classifierStore';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ClassifierApi } from '../../services/api/classifier';
import { PredictionResponse } from '../../types/classifier';

export const LiveRecognitionHUD: React.FC = () => {
  const { classifierStatus, fetchClassifierStatus } = useClassifierStore();
  const [testPrediction, setTestPrediction] = useState<PredictionResponse | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  useEffect(() => {
    fetchClassifierStatus();
    const interval = window.setInterval(() => {
      fetchClassifierStatus();
    }, 2000);
    return () => window.clearInterval(interval);
  }, [fetchClassifierStatus]);

  const handleRunMockPrediction = async () => {
    setIsTesting(true);
    try {
      // 21 points 3D hand landmarks
      const mockLandmarks: number[][] = Array.from({ length: 21 }, (_, i) => [
        0.5 + Math.sin(i) * 0.1,
        0.5 + Math.cos(i) * 0.1,
        (i % 5) * 0.02,
      ]);
      const res = await ClassifierApi.predictGesture(mockLandmarks, 'Right');
      setTestPrediction(res);
    } catch (err) {
      // ignore
    } finally {
      setIsTesting(false);
    }
  };

  const isLoaded = classifierStatus?.is_model_loaded ?? false;
  const activeModelName = classifierStatus?.active_model_name || 'No Model Active';
  const avgLatency = classifierStatus?.avg_inference_latency_ms ?? 0;
  const inferenceCount = classifierStatus?.inference_count ?? 0;

  return (
    <Card className="p-5 border border-[rgba(148,180,210,0.18)] bg-[#0C121E]/80 backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-[rgba(148,180,210,0.12)]">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#48DDF5]" />
            <h3 className="text-base font-bold text-white tracking-wide">
              Module F: Live Gesture Recognition HUD &amp; Engine Telemetry
            </h3>
            <Badge variant={isLoaded ? 'green' : 'warning'}>
              {isLoaded ? 'Inference Engine Ready' : 'Standby (Load a Model)'}
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Real-time inference pipeline embedded directly inside MediaPipe hand tracking stream. Sub-millisecond latency.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleRunMockPrediction}
            disabled={!isLoaded || isTesting}
            className="text-xs flex items-center gap-1.5 border-[rgba(72,221,245,0.3)] text-[#48DDF5] hover:bg-[#48DDF5]/10"
          >
            <Fingerprint className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
            Test Predict
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={() => fetchClassifierStatus()}
            className="text-xs flex items-center gap-1.5 border-white/10 text-[#91A4B8] hover:text-white"
          >
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {/* Engine Telemetry Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Active Model
          </span>
          <div className="text-sm font-bold font-mono text-white truncate" title={activeModelName}>
            {activeModelName}
          </div>
          <span className="text-[10px] text-[#00E5FF] mt-0.5 block">
            {classifierStatus?.classes?.length ?? 0} gesture classes
          </span>
        </div>

        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Avg Inference Latency
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#10B981]">
              {avgLatency > 0 ? avgLatency.toFixed(2) : '< 0.10'}
            </span>
            <span className="text-xs text-[#91A4B8]">ms</span>
          </div>
          <span className="text-[10px] text-[#10B981] mt-0.5 block">Target: &lt; 15.0 ms</span>
        </div>

        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Confidence Threshold
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold font-mono text-[#00E5FF]">
              {((classifierStatus?.confidence_threshold ?? 0.7) * 100).toFixed(0)}%
            </span>
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Unknown if lower</span>
        </div>

        <div className="p-3 rounded-xl bg-[#111928] border border-[rgba(148,180,210,0.1)]">
          <span className="text-[11px] font-medium text-[#91A4B8] uppercase tracking-wider block mb-1">
            Frames Classified
          </span>
          <div className="text-2xl font-bold font-mono text-white">
            {inferenceCount.toLocaleString()}
          </div>
          <span className="text-[10px] text-[#91A4B8] mt-0.5 block">Live stream inferences</span>
        </div>
      </div>

      {/* Live Recognition HUD Card */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-[#090E17] to-[#111928] border border-[rgba(72,221,245,0.2)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-[#00E5FF]/10 border border-[#00E5FF]/30 flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-[#00E5FF]" />
            </div>

            <div>
              <div className="text-[11px] text-[#91A4B8] uppercase tracking-wider font-semibold">
                HUD Target Gesture Prediction
              </div>
              <div className="text-xl font-bold text-white flex items-center gap-2 mt-0.5">
                {testPrediction
                  ? testPrediction.gesture_name
                  : isLoaded
                  ? 'Awaiting Video Hand Inflow'
                  : 'Load a model to enable HUD'}
                {testPrediction && (
                  <Badge variant={testPrediction.is_recognized ? 'green' : 'warning'}>
                    {testPrediction.gesture_id || 'UNKNOWN'}
                  </Badge>
                )}
              </div>
              <div className="text-xs text-[#91A4B8] mt-0.5">
                {testPrediction
                  ? `Inference time: ${testPrediction.inference_latency_ms.toFixed(3)} ms • Filter threshold: ${(testPrediction.threshold * 100).toFixed(0)}%`
                  : 'Camera frames automatically pass through feature normalization and MLP softmax.'}
              </div>
            </div>
          </div>

          {testPrediction && (
            <div className="sm:text-right min-w-[140px]">
              <div className="text-xs text-[#91A4B8] mb-1">Confidence Score</div>
              <div className="text-2xl font-bold font-mono text-[#00E5FF]">
                {(testPrediction.confidence * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-[#111928] h-1.5 rounded-full mt-1.5 overflow-hidden border border-white/10">
                <div
                  className="h-full bg-gradient-to-r from-[#00E5FF] to-[#10B981]"
                  style={{ width: `${testPrediction.confidence * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
