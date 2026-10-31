import React, { useEffect, useState, useMemo } from 'react';
import {
  DownloadCloud,
  CheckCircle2,
  XCircle,
  HardDrive,
  RefreshCw,
  Search,
  Check,
  AlertTriangle,
  StopCircle,
  FolderDown,
  Layers,
} from 'lucide-react';
import { Card } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Button } from '../../../../components/ui/Button';
import { usePublicDatasetStore } from '../../../../store/publicDatasetStore';

export const ClassSelectorAndDownloader: React.FC = () => {
  const {
    classes,
    hagridInfo,
    selectedDownloadClasses,
    includeAnnotationsDownload,
    activeDownloadJob,
    toggleDownloadClass,
    selectAllDownloadClasses,
    clearDownloadClasses,
    setIncludeAnnotationsDownload,
    startDownload,
    cancelDownload,
    pollDownloadStatus,
    fetchHagridInfo,
  } = usePublicDatasetStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'one_handed' | 'two_handed' | 'downloaded'>('all');

  // Job Polling Loop
  useEffect(() => {
    if (!activeDownloadJob || activeDownloadJob.status === 'completed' || activeDownloadJob.status === 'cancelled' || activeDownloadJob.status === 'error') {
      return;
    }
    const timer = setInterval(async () => {
      await pollDownloadStatus(activeDownloadJob.job_id);
    }, 1500);

    return () => clearInterval(timer);
  }, [activeDownloadJob, pollDownloadStatus]);

  const downloadedClassesSet = useMemo(() => {
    return new Set(hagridInfo?.downloaded_classes || []);
  }, [hagridInfo?.downloaded_classes]);

  // Filtered classes
  const filteredClasses = useMemo(() => {
    return classes.filter((cls) => {
      const matchesSearch = cls.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cls.description.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;

      if (filterType === 'one_handed') return !cls.is_two_handed;
      if (filterType === 'two_handed') return cls.is_two_handed;
      if (filterType === 'downloaded') return downloadedClassesSet.has(cls.name);
      return true;
    });
  }, [classes, searchQuery, filterType, downloadedClassesSet]);

  // Total selected size calculation
  const totalSelectedGb = useMemo(() => {
    let sum = 0;
    if (includeAnnotationsDownload && !hagridInfo?.annotations_downloaded) {
      sum += 1.9; // Annotations zip size
    }
    classes.forEach((c) => {
      if (selectedDownloadClasses.includes(c.name)) {
        sum += c.size_gb;
      }
    });
    return Math.round(sum * 10) / 10;
  }, [classes, selectedDownloadClasses, includeAnnotationsDownload, hagridInfo?.annotations_downloaded]);

  const handleStartDownload = async () => {
    if (selectedDownloadClasses.length === 0 && !includeAnnotationsDownload) return;
    await startDownload();
  };

  const isDownloading = activeDownloadJob?.status === 'running' || activeDownloadJob?.status === 'pending';

  return (
    <Card variant="glass" className="p-5 flex flex-col gap-4 border-[rgba(148,180,210,0.12)]">
      {/* Title & Description */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(148,180,210,0.1)]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <DownloadCloud className="w-4 h-4 text-[#48DDF5]" />
              Selective Gesture Archive Downloader
            </h3>
            <Badge variant="cyan" className="text-[10px] font-mono">
              Safe Chunked Transfer
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Choose specific gesture categories to download from official HaGRID mirrors. Prevents downloading the full 1.5 TB raw dataset.
          </p>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={selectAllDownloadClasses}
            disabled={isDownloading}
            className="text-xs"
          >
            Select All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearDownloadClasses}
            disabled={isDownloading || selectedDownloadClasses.length === 0}
            className="text-xs"
          >
            Clear
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleStartDownload}
            disabled={isDownloading || (selectedDownloadClasses.length === 0 && !includeAnnotationsDownload)}
            icon={<DownloadCloud className="w-3.5 h-3.5" />}
            className="text-xs font-semibold"
          >
            {isDownloading ? 'Downloading...' : `Download (${totalSelectedGb} GB)`}
          </Button>
        </div>
      </div>

      {/* Active Download Banner */}
      {activeDownloadJob && (
        <div className={`p-4 rounded-xl border flex flex-col gap-2.5 transition-all ${
          activeDownloadJob.status === 'completed'
            ? 'bg-[rgba(66,245,165,0.08)] border-[rgba(66,245,165,0.25)]'
            : activeDownloadJob.status === 'error'
            ? 'bg-[rgba(239,68,68,0.08)] border-[rgba(239,68,68,0.25)]'
            : activeDownloadJob.status === 'cancelled'
            ? 'bg-[rgba(245,158,11,0.08)] border-[rgba(245,158,11,0.25)]'
            : 'bg-[rgba(72,221,245,0.08)] border-[rgba(72,221,245,0.25)]'
        }`}>
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              {activeDownloadJob.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-[#42F5A5]" />}
              {activeDownloadJob.status === 'error' && <XCircle className="w-4 h-4 text-[#EF4444]" />}
              {activeDownloadJob.status === 'cancelled' && <AlertTriangle className="w-4 h-4 text-[#F59E0B]" />}
              {isDownloading && <RefreshCw className="w-4 h-4 text-[#48DDF5] animate-spin" />}
              <span className="font-semibold text-white">
                {activeDownloadJob.message || 'Processing download job...'}
              </span>
              <span className="font-mono text-[10px] text-[#91A4B8]">
                ID: {activeDownloadJob.job_id.slice(0, 8)}
              </span>
            </div>

            <div className="flex items-center gap-3">
              {activeDownloadJob.details?.speed_mbps !== undefined && (
                <span className="text-[11px] font-mono text-[#48DDF5]">
                  {activeDownloadJob.details.speed_mbps.toFixed(1)} MB/s
                </span>
              )}
              {isDownloading && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => cancelDownload(activeDownloadJob.job_id)}
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
                activeDownloadJob.status === 'completed'
                  ? 'bg-[#42F5A5]'
                  : activeDownloadJob.status === 'error'
                  ? 'bg-[#EF4444]'
                  : activeDownloadJob.status === 'cancelled'
                  ? 'bg-[#F59E0B]'
                  : 'bg-gradient-to-r from-[#48DDF5] to-[#42F5A5]'
              }`}
              style={{ width: `${Math.max(2, Math.min(100, activeDownloadJob.progress_percent))}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-[#91A4B8] font-mono">
            <span>
              {activeDownloadJob.details?.current_file ? `File: ${activeDownloadJob.details.current_file}` : 'Waiting...'}
            </span>
            <span>{Math.round(activeDownloadJob.progress_percent)}%</span>
          </div>
        </div>
      )}

      {/* Annotations & Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
        {/* Annotations Option */}
        <label className="flex items-center gap-2.5 cursor-pointer text-xs select-none">
          <input
            type="checkbox"
            checked={includeAnnotationsDownload}
            onChange={(e) => setIncludeAnnotationsDownload(e.target.checked)}
            disabled={isDownloading || hagridInfo?.annotations_downloaded}
            className="w-4 h-4 rounded border-gray-600 text-[#48DDF5] focus:ring-0 bg-[#0F172A]"
          />
          <div className="flex items-center gap-2">
            <span className="font-semibold text-white">Download Annotations with Landmarks</span>
            <Badge variant={hagridInfo?.annotations_downloaded ? 'green' : 'cyan'} className="text-[10px] font-mono">
              {hagridInfo?.annotations_downloaded ? 'Already Present' : '1.9 GB'}
            </Badge>
          </div>
        </label>

        {/* Search & Filter pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#91A4B8] absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search classes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-lg bg-[rgba(15,23,42,0.6)] border border-[rgba(148,180,210,0.15)] text-xs text-white placeholder-[#91A4B8] focus:outline-none focus:border-[#48DDF5] w-36 sm:w-44"
            />
          </div>

          <div className="flex items-center gap-1 bg-[rgba(15,23,42,0.6)] p-0.5 rounded-lg border border-[rgba(148,180,210,0.1)] text-xs">
            <button
              onClick={() => setFilterType('all')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                filterType === 'all' ? 'bg-[#48DDF5]/20 text-[#48DDF5]' : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              All (34)
            </button>
            <button
              onClick={() => setFilterType('one_handed')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                filterType === 'one_handed' ? 'bg-[#48DDF5]/20 text-[#48DDF5]' : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              1-Hand
            </button>
            <button
              onClick={() => setFilterType('two_handed')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                filterType === 'two_handed' ? 'bg-[#48DDF5]/20 text-[#48DDF5]' : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              2-Hand (7)
            </button>
            <button
              onClick={() => setFilterType('downloaded')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                filterType === 'downloaded' ? 'bg-[#42F5A5]/20 text-[#42F5A5]' : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              Downloaded ({downloadedClassesSet.size})
            </button>
          </div>
        </div>
      </div>

      {/* Class Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5 max-h-[420px] overflow-y-auto pr-1">
        {filteredClasses.map((cls) => {
          const isDownloaded = downloadedClassesSet.has(cls.name);
          const isSelected = selectedDownloadClasses.includes(cls.name);

          return (
            <div
              key={cls.name}
              onClick={() => {
                if (!isDownloading) toggleDownloadClass(cls.name);
              }}
              className={`p-2.5 rounded-xl border transition-all cursor-pointer select-none flex flex-col justify-between gap-1.5 ${
                isSelected
                  ? 'bg-[rgba(72,221,245,0.14)] border-[#48DDF5] shadow-sm'
                  : isDownloaded
                  ? 'bg-[rgba(66,245,165,0.06)] border-[rgba(66,245,165,0.25)] hover:border-[rgba(66,245,165,0.4)]'
                  : 'bg-[rgba(148,180,210,0.03)] border-[rgba(148,180,210,0.08)] hover:border-[rgba(148,180,210,0.2)]'
              }`}
            >
              <div className="flex items-start justify-between gap-1">
                <span className="font-mono text-xs font-bold text-white truncate capitalize">
                  {cls.name.replace(/_/g, ' ')}
                </span>
                <div className={`w-4 h-4 rounded flex items-center justify-center shrink-0 text-white ${
                  isSelected
                    ? 'bg-[#48DDF5]'
                    : isDownloaded
                    ? 'bg-[#42F5A5]/40 text-[#42F5A5]'
                    : 'border border-[rgba(148,180,210,0.3)]'
                }`}>
                  {isSelected && <Check className="w-3 h-3 text-[#0F172A] stroke-[3]" />}
                  {!isSelected && isDownloaded && <CheckCircle2 className="w-3 h-3 text-[#42F5A5]" />}
                </div>
              </div>

              <p className="text-[10px] text-[#91A4B8] line-clamp-1">
                {cls.description}
              </p>

              <div className="flex items-center justify-between text-[10px] font-mono pt-1 border-t border-[rgba(148,180,210,0.08)]">
                <span className="text-[#91A4B8]">{cls.size_gb} GB</span>
                {cls.is_two_handed ? (
                  <span className="text-[#F59E0B]">2-Hands</span>
                ) : (
                  <span className="text-[#48DDF5]">1-Hand</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
