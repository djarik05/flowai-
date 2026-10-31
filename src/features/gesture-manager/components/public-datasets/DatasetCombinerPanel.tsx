import React, { useEffect, useState } from 'react';
import {
  GitMerge,
  Download,
  ShieldCheck,
  Sparkles,
  PieChart,
  Layers,
  FileSpreadsheet,
  FileJson,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Users,
} from 'lucide-react';
import { Card } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Button } from '../../../../components/ui/Button';
import { usePublicDatasetStore } from '../../../../store/publicDatasetStore';
import { DatasetCombineRequest } from '../../../../types/publicDataset';
import { API_BASE_URL } from '../../../../services/api/client';

export const DatasetCombinerPanel: React.FC = () => {
  const {
    sources,
    combinedDatasets,
    lastCombineResult,
    isLoadingSources,
    isCombining,
    fetchSources,
    fetchCombinedDatasets,
    combineDatasets,
  } = usePublicDatasetStore();

  const [datasetName, setDatasetName] = useState('gestureflow_combined_v1');
  const [includeCustom, setIncludeCustom] = useState(true);
  const [includeHagrid, setIncludeHagrid] = useState(true);
  const [compatibilityMode, setCompatibilityMode] = useState<'2d_projection' | '2d_only' | '3d_only'>('2d_projection');
  const [preserveSubjects, setPreserveSubjects] = useState(true);

  // Split ratios
  const [trainRatio, setTrainRatio] = useState(0.7);
  const [valRatio, setValRatio] = useState(0.15);
  const [testRatio, setTestRatio] = useState(0.15);

  useEffect(() => {
    fetchSources();
    fetchCombinedDatasets();
  }, [fetchSources, fetchCombinedDatasets]);

  const handleCombine = async () => {
    const req: DatasetCombineRequest = {
      name: datasetName,
      include_custom: includeCustom,
      include_hagrid: includeHagrid,
      compatibility_mode: compatibilityMode,
      preserve_subject_splits: preserveSubjects,
      train_ratio: trainRatio,
      val_ratio: valRatio,
      test_ratio: testRatio,
    };
    await combineDatasets(req);
  };

  const handleExportDownload = (combinedId: string, format: 'csv' | 'json') => {
    const url = `${API_BASE_URL}/dataset/combined/${encodeURIComponent(combinedId)}/export/${format}`;
    window.open(url, '_blank');
  };

  const customCount = sources?.custom_samples_count ?? 0;
  const hagridCount = sources?.hagrid_samples_count ?? 0;
  const totalAvailable = customCount + hagridCount;

  return (
    <Card variant="glass" className="p-5 flex flex-col gap-5 border-[rgba(148,180,210,0.12)]">
      {/* Title & Description */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(148,180,210,0.1)]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <GitMerge className="w-4 h-4 text-[#48DDF5]" />
              Dataset Combiner &amp; Subject-Level Split Engine
            </h3>
            <Badge variant="cyan" className="text-[10px] font-mono">
              Leakage-Free Splitting
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Fuse custom webcam recordings with official HaGRID public samples. Automatically projects 3D coordinates to 2D and enforces subject boundaries to prevent data contamination.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchSources();
              fetchCombinedDatasets();
            }}
            disabled={isLoadingSources}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoadingSources ? 'animate-spin' : ''}`} />}
            className="text-xs"
          >
            Refresh Sources
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleCombine}
            disabled={isCombining || totalAvailable === 0}
            icon={isCombining ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            className="text-xs font-semibold"
          >
            {isCombining ? 'Combining...' : 'Generate Combined Dataset'}
          </Button>
        </div>
      </div>

      {/* Sources Overview KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center justify-between">
            <span>Custom Webcam Data</span>
            <Badge variant="green" className="text-[9px] font-mono">3D Coordinates</Badge>
          </div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{customCount}</div>
          <div className="text-[10px] text-[#91A4B8] mt-0.5">Physical webcam capture sessions</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center justify-between">
            <span>HaGRID Public Data</span>
            <Badge variant="cyan" className="text-[9px] font-mono">2D Coordinates</Badge>
          </div>
          <div className="text-2xl font-bold text-[#48DDF5] mt-1 font-mono">{hagridCount}</div>
          <div className="text-[10px] text-[#91A4B8] mt-0.5">Imported public benchmark samples</div>
        </div>

        <div className="p-3.5 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center justify-between">
            <span>Total Available</span>
            <Badge variant="muted" className="text-[9px] font-mono">Unified Pool</Badge>
          </div>
          <div className="text-2xl font-bold text-[#42F5A5] mt-1 font-mono">{totalAvailable}</div>
          <div className="text-[10px] text-[#91A4B8] mt-0.5">Ready for train/val/test export</div>
        </div>
      </div>

      {/* Configuration Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Sources & Compatibility */}
        <div className="p-4 rounded-xl bg-[rgba(148,180,210,0.03)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-3">
          <span className="text-xs font-bold text-white uppercase font-mono tracking-wider">
            1. Source Inclusions &amp; Coordinate Alignment
          </span>

          <div className="flex flex-col gap-2 text-xs">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={includeCustom}
                onChange={(e) => setIncludeCustom(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-[#48DDF5] focus:ring-0 bg-[#0F172A]"
              />
              <span className="text-white font-medium">Include Custom Webcam Samples ({customCount})</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={includeHagrid}
                onChange={(e) => setIncludeHagrid(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-[#48DDF5] focus:ring-0 bg-[#0F172A]"
              />
              <span className="text-white font-medium">Include HaGRID Public Samples ({hagridCount})</span>
            </label>
          </div>

          <div className="pt-2 border-t border-[rgba(148,180,210,0.08)]">
            <span className="text-[11px] text-[#91A4B8] block mb-1.5 font-semibold">
              Coordinate Compatibility Mode:
            </span>
            <div className="flex flex-col gap-1.5 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="compatMode"
                  value="2d_projection"
                  checked={compatibilityMode === '2d_projection'}
                  onChange={() => setCompatibilityMode('2d_projection')}
                  className="text-[#48DDF5] focus:ring-0"
                />
                <div>
                  <span className="text-white font-medium">2D Projection (Recommended)</span>
                  <span className="text-[10px] text-[#91A4B8] block">
                    Projects 3D custom samples to 2D by dropping z-depth, forming a unified 42-feature ML matrix.
                  </span>
                </div>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="compatMode"
                  value="2d_only"
                  checked={compatibilityMode === '2d_only'}
                  onChange={() => setCompatibilityMode('2d_only')}
                  className="text-[#48DDF5] focus:ring-0"
                />
                <div>
                  <span className="text-white font-medium">2D Only</span>
                  <span className="text-[10px] text-[#91A4B8] block">
                    Includes only native 2D samples (HaGRID imports).
                  </span>
                </div>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="compatMode"
                  value="3d_only"
                  checked={compatibilityMode === '3d_only'}
                  onChange={() => setCompatibilityMode('3d_only')}
                  className="text-[#48DDF5] focus:ring-0"
                />
                <div>
                  <span className="text-white font-medium">3D Only</span>
                  <span className="text-[10px] text-[#91A4B8] block">
                    Includes only native 3D samples (Custom webcam captures).
                  </span>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Right: Subject Split & Ratio Controls */}
        <div className="p-4 rounded-xl bg-[rgba(148,180,210,0.03)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-3">
          <span className="text-xs font-bold text-white uppercase font-mono tracking-wider">
            2. Leakage-Free Partitioning
          </span>

          {/* Subject boundary preservation toggle */}
          <div className="p-3 rounded-xl bg-[rgba(72,221,245,0.05)] border border-[rgba(72,221,245,0.15)] flex flex-col gap-1.5">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={preserveSubjects}
                onChange={(e) => setPreserveSubjects(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-[#48DDF5] focus:ring-0 bg-[#0F172A]"
              />
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#48DDF5]" />
                Preserve Subject-Level Split Boundaries
              </span>
            </label>
            <p className="text-[10px] text-[#91A4B8] pl-6 leading-relaxed">
              Partitions full subject user IDs instead of random frames to ensure images of the same individual never leak across train, validation, and test splits.
            </p>
          </div>

          {/* Split Sliders */}
          <div className="flex flex-col gap-2 pt-1">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[#91A4B8]">Train / Val / Test Split:</span>
              <span className="text-white font-semibold">
                {Math.round(trainRatio * 100)}% / {Math.round(valRatio * 100)}% / {Math.round(testRatio * 100)}%
              </span>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => {
                  setTrainRatio(0.7);
                  setValRatio(0.15);
                  setTestRatio(0.15);
                }}
                className="px-2.5 py-1 rounded text-[11px] font-mono bg-[rgba(148,180,210,0.06)] hover:bg-[rgba(148,180,210,0.12)] text-white border border-[rgba(148,180,210,0.1)]"
              >
                70 / 15 / 15
              </button>
              <button
                type="button"
                onClick={() => {
                  setTrainRatio(0.8);
                  setValRatio(0.1);
                  setTestRatio(0.1);
                }}
                className="px-2.5 py-1 rounded text-[11px] font-mono bg-[rgba(148,180,210,0.06)] hover:bg-[rgba(148,180,210,0.12)] text-white border border-[rgba(148,180,210,0.1)]"
              >
                80 / 10 / 10
              </button>
              <button
                type="button"
                onClick={() => {
                  setTrainRatio(0.6);
                  setValRatio(0.2);
                  setTestRatio(0.2);
                }}
                className="px-2.5 py-1 rounded text-[11px] font-mono bg-[rgba(148,180,210,0.06)] hover:bg-[rgba(148,180,210,0.12)] text-white border border-[rgba(148,180,210,0.1)]"
              >
                60 / 20 / 20
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Latest Combine Result Notification Banner */}
      {lastCombineResult && (
        <div className="p-4 rounded-xl bg-[rgba(66,245,165,0.08)] border border-[rgba(66,245,165,0.3)] flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-[#42F5A5]" />
              <div>
                <span className="font-bold text-white text-xs">
                  Successfully Generated Combined Dataset: "{lastCombineResult.name}"
                </span>
                <span className="text-[10px] text-[#91A4B8] block font-mono">
                  ID: {lastCombineResult.combined_id} &bull; {lastCombineResult.total_samples} total samples across {lastCombineResult.classes_included.length} classes
                </span>
              </div>
            </div>

            {/* Quick Export Downloads */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportDownload(lastCombineResult.combined_id, 'csv')}
                icon={<FileSpreadsheet className="w-3.5 h-3.5 text-[#42F5A5]" />}
                className="text-xs border-[rgba(66,245,165,0.3)] text-[#42F5A5]"
              >
                Export CSV (42-feat)
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExportDownload(lastCombineResult.combined_id, 'json')}
                icon={<FileJson className="w-3.5 h-3.5 text-[#48DDF5]" />}
                className="text-xs border-[rgba(72,221,245,0.3)] text-[#48DDF5]"
              >
                Export JSON
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-2 pt-2 border-t border-[rgba(66,245,165,0.15)] text-[11px] font-mono">
            <div>
              <span className="text-[#91A4B8] block">Train Split</span>
              <span className="text-white font-bold">{lastCombineResult.train_samples} samples</span>
            </div>
            <div>
              <span className="text-[#91A4B8] block">Val Split</span>
              <span className="text-white font-bold">{lastCombineResult.val_samples} samples</span>
            </div>
            <div>
              <span className="text-[#91A4B8] block">Test Split</span>
              <span className="text-white font-bold">{lastCombineResult.test_samples} samples</span>
            </div>
            <div>
              <span className="text-[#91A4B8] block">Subjects</span>
              <span className="text-[#42F5A5] font-bold">{lastCombineResult.unique_subjects} distinct</span>
            </div>
          </div>
        </div>
      )}

      {/* Historical Combined Datasets List */}
      {combinedDatasets.length > 0 && (
        <div className="flex flex-col gap-2 pt-2 border-t border-[rgba(148,180,210,0.1)]">
          <span className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#48DDF5]" />
            Generated Datasets Catalog ({combinedDatasets.length})
          </span>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {combinedDatasets.map((ds) => (
              <div
                key={ds.combined_id}
                className="p-3 rounded-xl bg-[rgba(148,180,210,0.03)] border border-[rgba(148,180,210,0.08)] flex items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="font-semibold text-white">{ds.name}</div>
                  <div className="text-[10px] text-[#91A4B8] font-mono mt-0.5">
                    {ds.total_samples} samples &bull; {ds.classes.length} classes &bull; {ds.coordinate_format}
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExportDownload(ds.combined_id, 'csv')}
                    className="text-[10px] py-1 h-7 text-[#42F5A5] border-[rgba(66,245,165,0.25)]"
                  >
                    CSV
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExportDownload(ds.combined_id, 'json')}
                    className="text-[10px] py-1 h-7 text-[#48DDF5] border-[rgba(72,221,245,0.25)]"
                  >
                    JSON
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};
