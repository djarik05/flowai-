import React, { useEffect, useState } from 'react';
import {
  FileCode,
  FolderInput,
  Play,
  StopCircle,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  FolderOpen,
  Filter,
  Layers,
  Sparkles,
} from 'lucide-react';
import { Card } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Button } from '../../../../components/ui/Button';
import { usePublicDatasetStore } from '../../../../store/publicDatasetStore';

export const AnnotationImporterPanel: React.FC = () => {
  const {
    hagridInfo,
    classes,
    importSourceType,
    localImportPath,
    selectedSplits,
    maxSamplesPerClass,
    createMissingGestures,
    activeImportJob,
    selectedImportClasses,
    setImportSourceType,
    setLocalImportPath,
    toggleSplit,
    setMaxSamplesPerClass,
    setCreateMissingGestures,
    toggleImportClass,
    selectAllImportClasses,
    clearImportClasses,
    startImport,
    cancelImport,
    pollImportStatus,
    fetchSources,
  } = usePublicDatasetStore();

  const [isOptionsOpen, setIsOptionsOpen] = useState(false);

  // Polling loop for active import job
  useEffect(() => {
    if (!activeImportJob || activeImportJob.status === 'completed' || activeImportJob.status === 'cancelled' || activeImportJob.status === 'error') {
      return;
    }
    const timer = setInterval(async () => {
      const res = await pollImportStatus(activeImportJob.job_id);
      if (res?.status === 'completed') {
        fetchSources();
      }
    }, 1500);

    return () => clearInterval(timer);
  }, [activeImportJob, pollImportStatus, fetchSources]);

  const isImporting = activeImportJob?.status === 'running' || activeImportJob?.status === 'pending';

  const handleStartImport = async () => {
    await startImport();
  };

  return (
    <Card variant="glass" className="p-5 flex flex-col gap-4 border-[rgba(148,180,210,0.12)]">
      {/* Title & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(148,180,210,0.1)]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <FolderInput className="w-4 h-4 text-[#42F5A5]" />
              HaGRID Annotation Parser &amp; Ingestion Engine
            </h3>
            <Badge variant="green" className="text-[10px] font-mono">
              2D MediaPipe Normalized
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Extracts hand bounding boxes and 21 normalized landmarks from annotations. Saves samples directly into isolated public storage.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleStartImport}
            disabled={isImporting}
            icon={isImporting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            className="text-xs font-semibold"
          >
            {isImporting ? 'Parsing...' : 'Start Ingestion'}
          </Button>
        </div>
      </div>

      {/* Active Import Job Banner */}
      {activeImportJob && (
        <div className={`p-4 rounded-xl border flex flex-col gap-2.5 transition-all ${
          activeImportJob.status === 'completed'
            ? 'bg-[rgba(66,245,165,0.08)] border-[rgba(66,245,165,0.25)]'
            : activeImportJob.status === 'error'
            ? 'bg-[rgba(239,68,68,0.08)] border-[rgba(239,68,68,0.25)]'
            : activeImportJob.status === 'cancelled'
            ? 'bg-[rgba(245,158,11,0.08)] border-[rgba(245,158,11,0.25)]'
            : 'bg-[rgba(66,245,165,0.08)] border-[rgba(66,245,165,0.25)]'
        }`}>
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              {activeImportJob.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-[#42F5A5]" />}
              {activeImportJob.status === 'error' && <AlertTriangle className="w-4 h-4 text-[#EF4444]" />}
              {activeImportJob.status === 'cancelled' && <AlertTriangle className="w-4 h-4 text-[#F59E0B]" />}
              {isImporting && <RefreshCw className="w-4 h-4 text-[#42F5A5] animate-spin" />}
              <span className="font-semibold text-white">
                {activeImportJob.message || 'Import in progress...'}
              </span>
              <span className="font-mono text-[10px] text-[#91A4B8]">
                ID: {activeImportJob.job_id.slice(0, 8)}
              </span>
            </div>

            <div className="flex items-center gap-3">
              {activeImportJob.details?.samples_imported !== undefined && (
                <span className="text-[11px] font-mono text-[#42F5A5]">
                  {activeImportJob.details.samples_imported} samples
                </span>
              )}
              {isImporting && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => cancelImport(activeImportJob.job_id)}
                  icon={<StopCircle className="w-3.5 h-3.5 text-[#EF4444]" />}
                  className="text-xs text-[#EF4444] border-[rgba(239,68,68,0.3)] hover:bg-[rgba(239,68,68,0.1)] py-1 h-7"
                >
                  Cancel
                </Button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-[rgba(148,180,210,0.1)] h-2 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 rounded-full ${
                activeImportJob.status === 'completed'
                  ? 'bg-[#42F5A5]'
                  : activeImportJob.status === 'error'
                  ? 'bg-[#EF4444]'
                  : 'bg-gradient-to-r from-[#42F5A5] to-[#48DDF5]'
              }`}
              style={{ width: `${Math.max(2, Math.min(100, activeImportJob.progress_percent))}%` }}
            />
          </div>

          {/* Class Breakdown if completed */}
          {activeImportJob.details?.class_distribution && Object.keys(activeImportJob.details.class_distribution).length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap pt-1 text-[10px] font-mono">
              <span className="text-[#91A4B8]">Imported distribution:</span>
              {Object.entries(activeImportJob.details.class_distribution).map(([cls, cnt]) => (
                <span key={cls} className="px-1.5 py-0.5 rounded bg-[rgba(66,245,165,0.1)] text-[#42F5A5]">
                  {cls}: {cnt}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Ingestion Source Tabs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Source 1: Downloaded Archives */}
        <div
          onClick={() => setImportSourceType('downloaded_archives')}
          className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col gap-2 ${
            importSourceType === 'downloaded_archives'
              ? 'bg-[rgba(66,245,165,0.08)] border-[#42F5A5]'
              : 'bg-[rgba(148,180,210,0.03)] border-[rgba(148,180,210,0.1)] hover:border-[rgba(148,180,210,0.25)]'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-[#42F5A5]" />
              Downloaded Archive Directory
            </span>
            <input
              type="radio"
              checked={importSourceType === 'downloaded_archives'}
              onChange={() => setImportSourceType('downloaded_archives')}
              className="text-[#42F5A5] focus:ring-0"
            />
          </div>
          <p className="text-[11px] text-[#91A4B8]">
            Ingests from official annotations downloaded to <span className="font-mono text-white">backend/datasets/public/hagrid/</span>.
          </p>
          <div className="text-[10px] text-[#42F5A5] font-mono">
            {hagridInfo?.annotations_downloaded ? 'Annotations available for parsing' : 'Annotations not yet downloaded'}
          </div>
        </div>

        {/* Source 2: Local File Path */}
        <div
          onClick={() => setImportSourceType('local_path')}
          className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col gap-2 ${
            importSourceType === 'local_path'
              ? 'bg-[rgba(72,221,245,0.08)] border-[#48DDF5]'
              : 'bg-[rgba(148,180,210,0.03)] border-[rgba(148,180,210,0.1)] hover:border-[rgba(148,180,210,0.25)]'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white flex items-center gap-2">
              <FileCode className="w-4 h-4 text-[#48DDF5]" />
              Custom Local HaGRID JSON / Directory
            </span>
            <input
              type="radio"
              checked={importSourceType === 'local_path'}
              onChange={() => setImportSourceType('local_path')}
              className="text-[#48DDF5] focus:ring-0"
            />
          </div>
          <p className="text-[11px] text-[#91A4B8]">
            Point directly to an existing extracted HaGRID annotations JSON or folder on your local drive.
          </p>
          {importSourceType === 'local_path' && (
            <input
              type="text"
              placeholder="e.g. C:\datasets\hagrid\ann_subsample"
              value={localImportPath}
              onChange={(e) => setLocalImportPath(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              className="px-2.5 py-1 rounded bg-[rgba(15,23,42,0.8)] border border-[rgba(148,180,210,0.2)] text-xs text-white placeholder-[#91A4B8] font-mono focus:outline-none focus:border-[#48DDF5] w-full"
            />
          )}
        </div>
      </div>

      {/* Advanced Parsing & Filtering Controls */}
      <div className="p-3.5 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 font-mono">
            <Filter className="w-3.5 h-3.5 text-[#48DDF5]" />
            Import Configuration &amp; Split Filters
          </span>
          <button
            onClick={() => setIsOptionsOpen(!isOptionsOpen)}
            className="text-[11px] text-[#48DDF5] hover:underline"
          >
            {isOptionsOpen ? 'Hide Options' : 'Show Advanced Filters'}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          {/* Split Selectors */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] text-[#91A4B8]">Splits to Ingest:</span>
            <div className="flex items-center gap-1.5 font-mono">
              {(['train', 'val', 'test'] as const).map((split) => {
                const isSelected = selectedSplits.includes(split);
                return (
                  <button
                    key={split}
                    onClick={() => toggleSplit(split)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                      isSelected
                        ? 'bg-[#48DDF5]/20 text-[#48DDF5] border border-[#48DDF5]/40'
                        : 'bg-[rgba(148,180,210,0.05)] text-[#91A4B8] border border-transparent hover:text-white'
                    }`}
                  >
                    {split}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sample Cap */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] text-[#91A4B8]">Max Samples Per Class:</span>
            <input
              type="number"
              min={10}
              max={10000}
              step={50}
              value={maxSamplesPerClass}
              onChange={(e) => setMaxSamplesPerClass(Math.max(1, parseInt(e.target.value) || 100))}
              className="px-2.5 py-1 rounded-lg bg-[rgba(15,23,42,0.8)] border border-[rgba(148,180,210,0.2)] text-xs text-white font-mono focus:outline-none focus:border-[#48DDF5] w-28"
            />
          </div>

          {/* Auto-create gestures checkbox */}
          <div className="flex flex-col justify-end">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={createMissingGestures}
                onChange={(e) => setCreateMissingGestures(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-[#48DDF5] focus:ring-0 bg-[#0F172A]"
              />
              <span className="text-white text-[11px]">Auto-register Missing Gestures</span>
            </label>
          </div>
        </div>
      </div>
    </Card>
  );
};
