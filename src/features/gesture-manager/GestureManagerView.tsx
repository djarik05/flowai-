import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Hand,
  Video,
  Layers,
  Database,
  ShieldCheck,
  Globe,
  Plus,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { useGestureStore } from '../../store/gestureStore';
import { useDatasetStore } from '../../store/datasetStore';
import { useActivityStore } from '../../store/activityStore';
import { GestureDefinition } from '../../types/gesture';
import { GestureLibraryTab } from './components/GestureLibraryTab';
import { DatasetOverviewTab } from './components/DatasetOverviewTab';
import { GestureModal } from './components/GestureModal';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

// Lazy-loaded heavy tabs for code splitting
const CollectionStudioTab = React.lazy(() =>
  import('./components/CollectionStudioTab').then((m) => ({ default: m.CollectionStudioTab }))
);
const SampleExplorerTab = React.lazy(() =>
  import('./components/SampleExplorerTab').then((m) => ({ default: m.SampleExplorerTab }))
);
const ValidationExportTab = React.lazy(() =>
  import('./components/ValidationExportTab').then((m) => ({ default: m.ValidationExportTab }))
);
const PublicDatasetsTab = React.lazy(() =>
  import('./components/public-datasets/PublicDatasetsTab').then((m) => ({ default: m.PublicDatasetsTab }))
);

const TabLoadingFallback: React.FC = () => (
  <div className="w-full min-h-[320px] flex flex-col items-center justify-center gap-3 select-none">
    <div className="relative w-8 h-8 flex items-center justify-center">
      <div className="absolute inset-0 rounded-full border-2 border-[rgba(72,221,245,0.15)] border-t-[#48DDF5] animate-spin" />
    </div>
    <span className="text-xs text-[#91A4B8] font-mono tracking-wider">Loading tab studio...</span>
  </div>
);

export type GestureManagerTab =
  | 'library'
  | 'collection'
  | 'overview'
  | 'samples'
  | 'validation'
  | 'public-datasets';

export const GestureManagerView: React.FC = () => {
  const {
    gestures,
    fetchGestures,
    addGesture,
    updateGesture,
    deleteGesture,
    isLoading: isLoadingGestures,
  } = useGestureStore();

  const { fetchStats, fetchSamples } = useDatasetStore();
  const { addLog } = useActivityStore();

  // Active Tab
  const [activeTab, setActiveTab] = useState<GestureManagerTab>('library');

  // Selected Gesture for Collection
  const [collectionGestureId, setCollectionGestureId] = useState<string>('');

  // Modal State
  const [isGestureModalOpen, setIsGestureModalOpen] = useState(false);
  const [editingGesture, setEditingGesture] = useState<GestureDefinition | null>(null);

  // Initial Fetch on View Mount
  useEffect(() => {
    fetchGestures();
    fetchStats();
  }, [fetchGestures, fetchStats]);

  // Set default selected collection gesture once gestures load
  useEffect(() => {
    if (!collectionGestureId && gestures.length > 0) {
      setCollectionGestureId(gestures[0].id);
    }
  }, [gestures, collectionGestureId]);

  const handleOpenCreateModal = () => {
    setEditingGesture(null);
    setIsGestureModalOpen(true);
  };

  const handleOpenEditModal = (gesture: GestureDefinition) => {
    setEditingGesture(gesture);
    setIsGestureModalOpen(true);
  };

  const handleSaveGesture = async (data: {
    id?: string;
    name: string;
    description: string;
    type: 'static' | 'temporal';
    action: any;
    confidenceThreshold: number;
    customShortcut?: string;
  }) => {
    if (editingGesture) {
      await updateGesture(editingGesture.id, data);
      addLog({
        category: 'gesture',
        description: `Updated gesture: "${data.name}" (${editingGesture.id})`,
        status: 'info',
        isSimulated: false,
      });
    } else {
      const created = await addGesture(data);
      addLog({
        category: 'gesture',
        description: `Created new gesture: "${data.name}" (${created?.id || 'new'})`,
        status: 'success',
        isSimulated: false,
      });
    }
    // Refresh gestures & stats
    fetchGestures();
    fetchStats();
  };

  const handleDeleteGesture = async (id: string, name: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete gesture "${name}" (${id})?\n\nAssociated sample files will be cleaned up safely.`
    );
    if (!confirmed) return;

    await deleteGesture(id);
    addLog({
      category: 'gesture',
      description: `Deleted gesture "${name}" (${id})`,
      status: 'warning',
      isSimulated: false,
    });
    fetchGestures();
    fetchStats();
  };

  const handleSelectForCollection = (gestureId: string) => {
    setCollectionGestureId(gestureId);
    setActiveTab('collection');
  };

  const handleCollectionComplete = () => {
    fetchGestures();
    fetchStats();
    fetchSamples();
    addLog({
      category: 'gesture',
      description: `Completed dataset collection session for gesture ${collectionGestureId}`,
      status: 'success',
      isSimulated: false,
    });
  };

  const tabs: { id: GestureManagerTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'library', label: 'Gesture Library', icon: Hand },
    { id: 'collection', label: 'Collection Studio', icon: Video },
    { id: 'overview', label: 'Dataset Overview', icon: Layers },
    { id: 'samples', label: 'Sample Explorer', icon: Database },
    { id: 'validation', label: 'Validation & Export', icon: ShieldCheck },
    { id: 'public-datasets', label: 'Public Datasets (HaGRID)', icon: Globe },
  ];

  return (
    <div className="flex flex-col gap-6 p-4 lg:p-6 max-w-7xl mx-auto w-full">
      {/* Top Main Title & Navigation Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[rgba(148,180,210,0.14)]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              Gesture &amp; Dataset Studio
            </h1>
            <Badge variant="cyan">
              Phase 3 Live
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Create custom gestures, record real-time 21-landmark datasets with your webcam, inspect coordinates, and export ML-ready files.
          </p>
        </div>

        {/* Global Quick Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchGestures();
              fetchStats();
            }}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoadingGestures ? 'animate-spin' : ''}`} />}
            className="text-xs"
          >
            Sync
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleOpenCreateModal}
            icon={<Plus className="w-3.5 h-3.5" />}
            className="text-xs"
          >
            New Gesture
          </Button>
        </div>
      </div>

      {/* Modern Horizontal Navigation Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-[rgba(148,180,210,0.1)] scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'bg-gradient-to-r from-[#48DDF5]/20 to-[#42F5A5]/20 text-[#48DDF5] border border-[#48DDF5]/40 shadow-sm'
                  : 'text-[#91A4B8] hover:text-white hover:bg-[rgba(148,180,210,0.06)] border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[#48DDF5]' : 'text-[#91A4B8]'}`} />
              <span>{tab.label}</span>
              {tab.id === 'library' && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-[rgba(148,180,210,0.15)] text-[#F1F5F9] font-mono">
                  {gestures.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab View Content */}
      <div className="w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
          >
            <React.Suspense fallback={<TabLoadingFallback />}>
              {activeTab === 'library' && (
                <GestureLibraryTab
                  gestures={gestures}
                  onOpenCreate={handleOpenCreateModal}
                  onOpenEdit={handleOpenEditModal}
                  onDelete={handleDeleteGesture}
                  onSelectForCollection={handleSelectForCollection}
                />
              )}

              {activeTab === 'collection' && (
                <CollectionStudioTab
                  gestures={gestures}
                  selectedGestureId={collectionGestureId}
                  onSelectGestureId={setCollectionGestureId}
                  onCollectionComplete={handleCollectionComplete}
                />
              )}

              {activeTab === 'overview' && (
                <DatasetOverviewTab
                  gestures={gestures}
                  onSelectForCollection={handleSelectForCollection}
                />
              )}

              {activeTab === 'samples' && (
                <SampleExplorerTab gestures={gestures} />
              )}

              {activeTab === 'validation' && (
                <ValidationExportTab />
              )}

              {activeTab === 'public-datasets' && (
                <PublicDatasetsTab />
              )}
            </React.Suspense>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Create / Edit Gesture Modal */}
      <GestureModal
        isOpen={isGestureModalOpen}
        onClose={() => setIsGestureModalOpen(false)}
        onSave={handleSaveGesture}
        editingGesture={editingGesture}
      />
    </div>
  );
};
