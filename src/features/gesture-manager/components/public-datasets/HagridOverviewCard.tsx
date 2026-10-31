import React from 'react';
import {
  Database,
  ExternalLink,
  BookOpen,
  Award,
  HardDrive,
  Layers,
  FileCheck2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { Card } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { HagridDatasetInfo } from '../../../../types/publicDataset';

interface HagridOverviewCardProps {
  info: HagridDatasetInfo | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export const HagridOverviewCard: React.FC<HagridOverviewCardProps> = ({
  info,
  isLoading,
  onRefresh,
}) => {
  const downloadedCount = info?.downloaded_classes?.length ?? 0;
  const annotationsDownloaded = info?.annotations_downloaded ?? false;
  const totalImportedSamples = Object.values(info?.imported_sample_counts ?? {}).reduce(
    (acc, val) => acc + val,
    0
  );

  return (
    <Card variant="glass" className="p-5 flex flex-col gap-4 border-[rgba(72,221,245,0.2)] bg-gradient-to-br from-[rgba(15,23,42,0.85)] to-[rgba(7,13,26,0.95)]">
      {/* Top Header with Attribution & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-[rgba(148,180,210,0.12)]">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#48DDF5]/20 to-[#42F5A5]/20 border border-[#48DDF5]/30 flex items-center justify-center text-[#48DDF5] shrink-0 mt-0.5">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base font-bold text-white tracking-tight">
                {info?.full_name || 'HaGRIDv2: HAnd Gesture Recognition Image Dataset v2'}
              </h2>
              <Badge variant="cyan" className="text-[10px] uppercase font-mono">
                Official Integration
              </Badge>
              <Badge variant="muted" className="text-[10px] font-mono">
                v{info?.version || '2.0.0'}
              </Badge>
            </div>
            <p className="text-xs text-[#91A4B8] mt-1 max-w-3xl leading-relaxed">
              Large-scale benchmark dataset with 34 gesture classes, precise bounding boxes, 21-point hand landmarks, and diverse real-world lighting, backgrounds, and subjects.
            </p>
          </div>
        </div>

        {/* Paper & Repo Links */}
        <div className="flex items-center gap-2 shrink-0 self-end md:self-auto">
          <a
            href={info?.paper_url || 'https://arxiv.org/abs/2412.01508'}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#48DDF5] bg-[rgba(72,221,245,0.1)] hover:bg-[rgba(72,221,245,0.18)] transition-colors border border-[rgba(72,221,245,0.2)]"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>arXiv:2412.01508</span>
            <ExternalLink className="w-3 h-3 ml-0.5 opacity-70" />
          </a>
          <a
            href={info?.repository_url || 'https://github.com/hukenovs/hagrid'}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-[#91A4B8] hover:text-white bg-[rgba(148,180,210,0.08)] hover:bg-[rgba(148,180,210,0.15)] transition-colors border border-[rgba(148,180,210,0.12)]"
          >
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3 ml-0.5 opacity-70" />
          </a>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center gap-1">
            <Layers className="w-3 h-3 text-[#48DDF5]" />
            Dataset Classes
          </div>
          <div className="text-xl font-bold text-white mt-1">34 Classes</div>
          <div className="text-[10px] text-[#91A4B8] mt-0.5">33 Gestures + no_gesture</div>
        </div>

        <div className="p-3 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center gap-1">
            <HardDrive className="w-3 h-3 text-[#F59E0B]" />
            Full Raw Archive
          </div>
          <div className="text-xl font-bold text-white mt-1">~1.5 TB</div>
          <div className="text-[10px] text-[#F59E0B] mt-0.5 flex items-center gap-1">
            <AlertCircle className="w-2.5 h-2.5" />
            Selective Download Only
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center gap-1">
            <FileCheck2 className="w-3 h-3 text-[#42F5A5]" />
            Annotations Status
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {annotationsDownloaded ? 'Available' : 'Not Downloaded'}
          </div>
          <div className="text-[10px] text-[#91A4B8] mt-0.5">
            {annotationsDownloaded ? 'annotations_with_landmarks' : 'Download archive (1.9 GB)'}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
          <div className="text-[10px] text-[#91A4B8] uppercase font-mono flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-[#48DDF5]" />
            Imported Samples
          </div>
          <div className="text-xl font-bold text-[#42F5A5] mt-1 font-mono">
            {totalImportedSamples.toLocaleString()}
          </div>
          <div className="text-[10px] text-[#91A4B8] mt-0.5">
            Across {downloadedCount} downloaded archives
          </div>
        </div>
      </div>

      {/* Mandatory License & Citation Notice */}
      <div className="p-3 rounded-xl bg-[rgba(72,221,245,0.05)] border border-[rgba(72,221,245,0.15)] flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
        <div className="flex items-start gap-2.5">
          <Award className="w-4 h-4 text-[#48DDF5] shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-white">
              Dataset License: {info?.license || 'CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0 International)'}
            </div>
            <div className="text-[11px] text-[#91A4B8] mt-0.5">
              Citation: <span className="font-mono text-[#F1F5F9]">Kapitanov, A., et al. (2024). HaGRIDv2: HAnd Gesture Recognition Image Dataset v2. arXiv:2412.01508.</span>
            </div>
          </div>
        </div>
        <a
          href={info?.license_url || 'https://creativecommons.org/licenses/by-sa/4.0/'}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[11px] text-[#48DDF5] hover:underline shrink-0 font-medium"
        >
          View Full License &rarr;
        </a>
      </div>
    </Card>
  );
};
