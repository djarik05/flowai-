import React, { useState, useEffect } from 'react';
import {
  Eye,
  Trash2,
  Filter,
  RefreshCw,
  Search,
  Database,
  Calendar,
  Layers,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import { useDatasetStore } from '../../../store/datasetStore';
import { GestureDefinition } from '../../../types/gesture';
import { DatasetSample } from '../../../types/dataset';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { SampleInspectionModal } from './SampleInspectionModal';

interface SampleExplorerTabProps {
  gestures: GestureDefinition[];
}

export const SampleExplorerTab: React.FC<SampleExplorerTabProps> = ({ gestures }) => {
  const {
    samples,
    samplesTotal,
    samplesLimit,
    samplesOffset,
    selectedGestureFilter,
    selectedSessionFilter,
    isLoadingSamples,
    fetchSamples,
    inspectSample,
    selectedSample,
    clearInspectedSample,
    deleteSample,
    deleteSession,
  } = useDatasetStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sessionInput, setSessionInput] = useState('');

  useEffect(() => {
    fetchSamples({ offset: 0 });
  }, [fetchSamples]);

  const handleInspect = async (sampleId: string) => {
    await inspectSample(sampleId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    clearInspectedSample();
  };

  const handleGestureFilterChange = (gestureId: string) => {
    fetchSamples({
      gesture_id: gestureId || undefined,
      offset: 0,
    });
  };

  const handleSessionSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchSamples({
      session_id: sessionInput.trim() || undefined,
      offset: 0,
    });
  };

  const handleClearFilters = () => {
    setSessionInput('');
    fetchSamples({
      gesture_id: undefined,
      session_id: undefined,
      offset: 0,
    });
  };

  const handleDeleteSession = async () => {
    if (!selectedSessionFilter) return;
    if (
      window.confirm(
        `Are you sure you want to delete ALL samples from session "${selectedSessionFilter}"?`
      )
    ) {
      await deleteSession(selectedSessionFilter);
    }
  };

  const totalPages = Math.ceil(samplesTotal / samplesLimit) || 1;
  const currentPage = Math.floor(samplesOffset / samplesLimit) + 1;

  return (
    <div className="flex flex-col gap-5">
      {/* Filter and Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.14)]">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Gesture Dropdown Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#91A4B8] font-mono">Gesture:</span>
            <select
              value={selectedGestureFilter || ''}
              onChange={(e) => handleGestureFilterChange(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-[rgba(18,29,45,0.8)] border border-[rgba(148,180,210,0.2)] text-xs text-white focus:outline-none focus:border-[#48DDF5] cursor-pointer"
            >
              <option value="" className="bg-[#0B1220]">All Gestures</option>
              {gestures.map((g) => (
                <option key={g.id} value={g.id} className="bg-[#0B1220]">
                  {g.name} ({g.id})
                </option>
              ))}
            </select>
          </div>

          {/* Session ID Search Form */}
          <form onSubmit={handleSessionSearch} className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#91A4B8] absolute left-3 top-2 pointer-events-none" />
              <input
                type="text"
                value={sessionInput}
                onChange={(e) => setSessionInput(e.target.value)}
                placeholder="Filter by Session ID..."
                className="pl-8 pr-3 py-1.5 rounded-lg bg-[rgba(18,29,45,0.8)] border border-[rgba(148,180,210,0.2)] text-xs text-white placeholder-[#61758B] focus:outline-none focus:border-[#48DDF5] w-48 font-mono"
              />
            </div>
            <Button variant="secondary" size="sm" type="submit" className="text-xs py-1">
              Filter
            </Button>
          </form>

          {(selectedGestureFilter || selectedSessionFilter) && (
            <Button variant="ghost" size="sm" onClick={handleClearFilters} className="text-xs py-1 text-[#91A4B8]">
              Clear Filters
            </Button>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {selectedSessionFilter && (
            <Button
              variant="danger"
              size="sm"
              onClick={handleDeleteSession}
              icon={<Trash2 className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              Delete Session Samples
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchSamples()}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
            title="Refresh samples"
            className="p-1.5"
          />
        </div>
      </div>

      {/* Samples Table */}
      <Card variant="glass" className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0B1220] border-b border-[rgba(148,180,210,0.16)] text-[10px] uppercase text-[#91A4B8]">
              <tr>
                <th className="py-3 px-4">Sample ID</th>
                <th className="py-3 px-4">Gesture</th>
                <th className="py-3 px-4">Handedness</th>
                <th className="py-3 px-4">Session ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(148,180,210,0.08)]">
              {samples.map((sample) => {
                const isRight = sample.handedness.toLowerCase() === 'right';
                return (
                  <tr
                    key={sample.sample_id}
                    className="hover:bg-[rgba(72,221,245,0.04)] transition-colors"
                  >
                    <td className="py-2.5 px-4 text-white font-bold">
                      {sample.sample_id}
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="text-[#F1F5F9] font-medium">{sample.gesture_name}</span>{' '}
                      <span className="text-[#48DDF5] text-[10px]">({sample.gesture_id})</span>
                    </td>
                    <td className="py-2.5 px-4">
                      <Badge variant={isRight ? 'green' : 'cyan'}>
                        {sample.handedness} ({Math.round(sample.confidence * 100)}%)
                      </Badge>
                    </td>
                    <td className="py-2.5 px-4 text-[#91A4B8] max-w-[140px] truncate" title={sample.session_id}>
                      {sample.session_id || 'manual'}
                    </td>
                    <td className="py-2.5 px-4 text-[#91A4B8]">
                      {new Date(sample.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleInspect(sample.sample_id)}
                          icon={<Eye className="w-3.5 h-3.5 text-[#48DDF5]" />}
                          title="Inspect 21 coordinates"
                          className="p-1 hover:bg-[rgba(72,221,245,0.15)]"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (window.confirm(`Delete sample ${sample.sample_id}?`)) {
                              deleteSample(sample.sample_id);
                            }
                          }}
                          icon={<Trash2 className="w-3.5 h-3.5 text-[#FF647C]" />}
                          title="Delete sample"
                          className="p-1 hover:bg-[rgba(255,100,124,0.15)]"
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}

              {samples.length === 0 && !isLoadingSamples && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-[#91A4B8]">
                    <Database className="w-8 h-8 text-[#91A4B8] mx-auto mb-2 opacity-50" />
                    <p className="font-semibold text-white">No samples found</p>
                    <p className="text-xs mt-1">
                      Start a collection session in the Collection Studio to capture 21-landmark samples.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between p-3.5 border-t border-[rgba(148,180,210,0.12)] bg-[rgba(11,18,32,0.4)] text-xs font-mono">
          <div className="text-[#91A4B8]">
            Showing {samples.length > 0 ? samplesOffset + 1 : 0} to{' '}
            {Math.min(samplesOffset + samples.length, samplesTotal)} of {samplesTotal} samples
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={samplesOffset <= 0}
              onClick={() =>
                fetchSamples({
                  offset: Math.max(0, samplesOffset - samplesLimit),
                })
              }
              icon={<ChevronLeft className="w-3.5 h-3.5" />}
              className="p-1.5"
            />
            <span className="text-[#F1F5F9]">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={samplesOffset + samplesLimit >= samplesTotal}
              onClick={() =>
                fetchSamples({
                  offset: samplesOffset + samplesLimit,
                })
              }
              icon={<ChevronRight className="w-3.5 h-3.5" />}
              className="p-1.5"
            />
          </div>
        </div>
      </Card>

      {/* Inspection Modal */}
      <SampleInspectionModal
        sample={selectedSample}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onDelete={(id) => deleteSample(id)}
      />
    </div>
  );
};
