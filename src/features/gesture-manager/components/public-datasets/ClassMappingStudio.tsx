import React, { useEffect, useState, useMemo } from 'react';
import {
  Link2,
  Save,
  RotateCcw,
  Search,
  CheckCircle2,
  PlusCircle,
  EyeOff,
  Sparkles,
  Layers,
} from 'lucide-react';
import { Card } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Button } from '../../../../components/ui/Button';
import { usePublicDatasetStore } from '../../../../store/publicDatasetStore';
import { HagridClassMapping } from '../../../../types/publicDataset';

export const ClassMappingStudio: React.FC = () => {
  const {
    mappings,
    availableGestures,
    classes,
    isLoadingMappings,
    isSavingMappings,
    fetchMappings,
    updateMappingEntry,
    saveMappings,
  } = usePublicDatasetStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState<'all' | 'map' | 'create_new' | 'skip'>('all');
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(false);

  useEffect(() => {
    fetchMappings();
  }, [fetchMappings]);

  const mappingEntries = useMemo(() => {
    return Object.entries(mappings).filter(([cls, m]) => {
      const matchesSearch = cls.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (m.target_gesture_name && m.target_gesture_name.toLowerCase().includes(searchQuery.toLowerCase()));
      if (!matchesSearch) return false;
      if (actionFilter !== 'all' && m.action !== actionFilter) return false;
      return true;
    });
  }, [mappings, searchQuery, actionFilter]);

  const handleSave = async () => {
    const ok = await saveMappings();
    if (ok) {
      setSaveSuccessMsg(true);
      setTimeout(() => setSaveSuccessMsg(false), 2500);
    }
  };

  return (
    <Card variant="glass" className="p-5 flex flex-col gap-4 border-[rgba(148,180,210,0.12)]">
      {/* Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[rgba(148,180,210,0.1)]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Link2 className="w-4 h-4 text-[#48DDF5]" />
              Gesture Class Mapping Studio
            </h3>
            <Badge variant="cyan" className="text-[10px] font-mono">
              Schema Bridge
            </Badge>
          </div>
          <p className="text-xs text-[#91A4B8] mt-1">
            Map official HaGRID labels to GestureFlow gestures, designate new gestures to create, or skip classes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {saveSuccessMsg && (
            <span className="text-xs font-semibold text-[#42F5A5] flex items-center gap-1 font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Saved!
            </span>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={isSavingMappings}
            icon={<Save className="w-3.5 h-3.5" />}
            className="text-xs font-semibold"
          >
            {isSavingMappings ? 'Saving...' : 'Save Mappings'}
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-2.5 rounded-xl bg-[rgba(148,180,210,0.04)] border border-[rgba(148,180,210,0.08)]">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#91A4B8] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search mappings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 pr-3 py-1.5 rounded-lg bg-[rgba(15,23,42,0.6)] border border-[rgba(148,180,210,0.15)] text-xs text-white placeholder-[#91A4B8] focus:outline-none focus:border-[#48DDF5] w-48 sm:w-60"
          />
        </div>

        <div className="flex items-center gap-1 text-xs">
          {(['all', 'map', 'create_new', 'skip'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setActionFilter(filter)}
              className={`px-2 py-1 rounded text-[11px] font-medium capitalize transition-colors ${
                actionFilter === filter ? 'bg-[#48DDF5]/20 text-[#48DDF5]' : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              {filter.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Mapping Table */}
      <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[rgba(148,180,210,0.1)] text-[#91A4B8] font-mono text-[10px] uppercase">
              <th className="py-2.5 px-3">HaGRID Class</th>
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3">Action</th>
              <th className="py-2.5 px-3">Target Gesture</th>
              <th className="py-2.5 px-3">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(148,180,210,0.06)] font-mono">
            {mappingEntries.map(([clsName, m]) => {
              const classMeta = classes.find((c) => c.name === clsName);
              const isTwoHanded = classMeta?.is_two_handed ?? false;

              return (
                <tr key={clsName} className="hover:bg-[rgba(148,180,210,0.03)] transition-colors">
                  {/* HaGRID Class */}
                  <td className="py-2.5 px-3 text-white font-semibold capitalize font-mono">
                    {clsName.replace(/_/g, ' ')}
                  </td>

                  {/* Type */}
                  <td className="py-2.5 px-3">
                    {isTwoHanded ? (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-[rgba(245,158,11,0.1)] text-[#F59E0B]">
                        2-Hand
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-[rgba(72,221,245,0.1)] text-[#48DDF5]">
                        1-Hand
                      </span>
                    )}
                  </td>

                  {/* Action */}
                  <td className="py-2.5 px-3">
                    <select
                      value={m.action}
                      onChange={(e) =>
                        updateMappingEntry(clsName, {
                          action: e.target.value as 'map' | 'skip' | 'create_new',
                        })
                      }
                      className="px-2 py-1 rounded bg-[rgba(15,23,42,0.8)] border border-[rgba(148,180,210,0.2)] text-xs text-white focus:outline-none focus:border-[#48DDF5]"
                    >
                      <option value="map">Map to Existing</option>
                      <option value="create_new">Create New Gesture</option>
                      <option value="skip">Skip Class</option>
                    </select>
                  </td>

                  {/* Target Gesture */}
                  <td className="py-2.5 px-3">
                    {m.action === 'map' ? (
                      <select
                        value={m.target_gesture_id || ''}
                        onChange={(e) => {
                          const targetId = e.target.value;
                          const found = availableGestures.find((g) => g.id === targetId);
                          updateMappingEntry(clsName, {
                            target_gesture_id: targetId || null,
                            target_gesture_name: found?.name || null,
                          });
                        }}
                        className="px-2 py-1 rounded bg-[rgba(15,23,42,0.8)] border border-[rgba(148,180,210,0.2)] text-xs text-white focus:outline-none focus:border-[#48DDF5] max-w-xs"
                      >
                        <option value="">-- Select Gesture --</option>
                        {availableGestures.map((g) => (
                          <option key={g.id} value={g.id}>
                            {g.name} ({g.id})
                          </option>
                        ))}
                      </select>
                    ) : m.action === 'create_new' ? (
                      <span className="text-[#42F5A5] flex items-center gap-1 text-[11px]">
                        <PlusCircle className="w-3 h-3" />
                        Auto-generate definition
                      </span>
                    ) : (
                      <span className="text-[#91A4B8] flex items-center gap-1 text-[11px]">
                        <EyeOff className="w-3 h-3" />
                        Excluded
                      </span>
                    )}
                  </td>

                  {/* Confidence Threshold */}
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min={0.5}
                        max={1.0}
                        step={0.05}
                        value={m.confidence_threshold}
                        onChange={(e) =>
                          updateMappingEntry(clsName, {
                            confidence_threshold: parseFloat(e.target.value),
                          })
                        }
                        className="w-16 accent-[#48DDF5]"
                      />
                      <span className="text-[11px] text-[#91A4B8] w-8">
                        {Math.round(m.confidence_threshold * 100)}%
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
