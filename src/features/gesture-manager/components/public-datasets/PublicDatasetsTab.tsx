import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DownloadCloud,
  FolderInput,
  Link2,
  GitMerge,
} from 'lucide-react';
import { usePublicDatasetStore } from '../../../../store/publicDatasetStore';
import { HagridOverviewCard } from './HagridOverviewCard';

// Lazy-loaded sub-panels for granular chunking
const ClassSelectorAndDownloader = React.lazy(() =>
  import('./ClassSelectorAndDownloader').then((m) => ({ default: m.ClassSelectorAndDownloader }))
);
const AnnotationImporterPanel = React.lazy(() =>
  import('./AnnotationImporterPanel').then((m) => ({ default: m.AnnotationImporterPanel }))
);
const ClassMappingStudio = React.lazy(() =>
  import('./ClassMappingStudio').then((m) => ({ default: m.ClassMappingStudio }))
);
const DatasetCombinerPanel = React.lazy(() =>
  import('./DatasetCombinerPanel').then((m) => ({ default: m.DatasetCombinerPanel }))
);

const SubPanelLoadingFallback: React.FC = () => (
  <div className="w-full min-h-[260px] flex flex-col items-center justify-center gap-3 select-none">
    <div className="relative w-7 h-7 flex items-center justify-center">
      <div className="absolute inset-0 rounded-full border-2 border-[rgba(72,221,245,0.15)] border-t-[#48DDF5] animate-spin" />
    </div>
    <span className="text-xs text-[#91A4B8] font-mono tracking-wider">Loading panel...</span>
  </div>
);

type SubTab = 'downloader' | 'importer' | 'mappings' | 'combiner';

export const PublicDatasetsTab: React.FC = () => {
  const {
    hagridInfo,
    isLoadingInfo,
    fetchHagridInfo,
    fetchMappings,
    fetchSources,
    fetchCombinedDatasets,
  } = usePublicDatasetStore();

  const [activeSubTab, setActiveSubTab] = useState<SubTab>('downloader');

  useEffect(() => {
    fetchHagridInfo();
    fetchMappings();
    fetchSources();
    fetchCombinedDatasets();
  }, [fetchHagridInfo, fetchMappings, fetchSources, fetchCombinedDatasets]);

  const subTabs: { id: SubTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'downloader', label: 'Selective Downloader', icon: DownloadCloud },
    { id: 'importer', label: 'Annotation Ingestion', icon: FolderInput },
    { id: 'mappings', label: 'Class Mappings', icon: Link2 },
    { id: 'combiner', label: 'Dataset Combiner', icon: GitMerge },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Overview & Metadata Card */}
      <HagridOverviewCard
        info={hagridInfo}
        isLoading={isLoadingInfo}
        onRefresh={() => {
          fetchHagridInfo();
          fetchSources();
        }}
      />

      {/* Sub Navigation Bar */}
      <div className="flex items-center gap-1 bg-[rgba(15,23,42,0.6)] p-1 rounded-xl border border-[rgba(148,180,210,0.12)] max-w-fit overflow-x-auto">
        {subTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? 'bg-gradient-to-r from-[#48DDF5]/20 to-[#42F5A5]/20 text-[#48DDF5] border border-[#48DDF5]/40 shadow-sm'
                  : 'text-[#91A4B8] hover:text-white hover:bg-[rgba(148,180,210,0.06)] border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#48DDF5]' : 'text-[#91A4B8]'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Sub Tab View Content */}
      <div className="w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSubTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
          >
            <React.Suspense fallback={<SubPanelLoadingFallback />}>
              {activeSubTab === 'downloader' && <ClassSelectorAndDownloader />}
              {activeSubTab === 'importer' && <AnnotationImporterPanel />}
              {activeSubTab === 'mappings' && <ClassMappingStudio />}
              {activeSubTab === 'combiner' && <DatasetCombinerPanel />}
            </React.Suspense>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};
