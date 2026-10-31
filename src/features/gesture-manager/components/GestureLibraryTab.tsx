import React, { useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  Edit2,
  Trash2,
  Play,
  Sparkles,
  HelpCircle,
  Database,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { GestureDefinition } from '../../../types/gesture';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

interface GestureLibraryTabProps {
  gestures: GestureDefinition[];
  onOpenCreate: () => void;
  onOpenEdit: (gesture: GestureDefinition) => void;
  onDelete: (id: string, name: string) => void;
  onSelectForCollection: (gestureId: string) => void;
}

export const GestureLibraryTab: React.FC<GestureLibraryTabProps> = ({
  gestures,
  onOpenCreate,
  onOpenEdit,
  onDelete,
  onSelectForCollection,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'static' | 'temporal'>('all');

  const filteredGestures = gestures.filter((g) => {
    const matchesSearch =
      g.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      g.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      g.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || g.type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="flex flex-col gap-5">
      {/* Search, Filter & Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.14)]">
        <div className="flex items-center gap-3 flex-1 min-w-[260px]">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 text-[#91A4B8] absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search gestures by name or ID..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[rgba(18,29,45,0.7)] border border-[rgba(148,180,210,0.2)] text-xs text-white placeholder-[#61758B] focus:outline-none focus:border-[#48DDF5] transition-colors"
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[rgba(18,29,45,0.7)] border border-[rgba(148,180,210,0.15)] text-xs">
            <button
              onClick={() => setTypeFilter('all')}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                typeFilter === 'all'
                  ? 'bg-[#48DDF5] text-[#070B12] font-semibold'
                  : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              All ({gestures.length})
            </button>
            <button
              onClick={() => setTypeFilter('static')}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                typeFilter === 'static'
                  ? 'bg-[#48DDF5] text-[#070B12] font-semibold'
                  : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              Static
            </button>
            <button
              onClick={() => setTypeFilter('temporal')}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                typeFilter === 'temporal'
                  ? 'bg-[#48DDF5] text-[#070B12] font-semibold'
                  : 'text-[#91A4B8] hover:text-white'
              }`}
            >
              Temporal
            </button>
          </div>
        </div>

        {/* Register Button */}
        <Button
          variant="primary"
          size="sm"
          onClick={onOpenCreate}
          icon={<Plus className="w-3.5 h-3.5" />}
        >
          Create Custom Gesture
        </Button>
      </div>

      {/* Gestures Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredGestures.map((gesture) => {
          const sampleCount = gesture.sampleCount ?? gesture.sample_count ?? 0;
          const isAdequate = sampleCount >= 30;

          return (
            <Card
              key={gesture.id}
              variant="glass"
              className="p-4 flex flex-col justify-between hover:border-[rgba(72,221,245,0.35)] transition-all group"
            >
              <div>
                {/* Header: ID, Name, Badges */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md bg-[rgba(72,221,245,0.12)] border border-[rgba(72,221,245,0.3)] text-[#48DDF5] font-mono text-[11px] font-bold">
                      {gesture.id}
                    </span>
                    <h3 className="text-sm font-bold text-white group-hover:text-[#48DDF5] transition-colors">
                      {gesture.name}
                    </h3>
                  </div>

                  <Badge variant={gesture.type === 'static' ? 'cyan' : 'purple'}>
                    {gesture.type}
                  </Badge>
                </div>

                {/* Description */}
                <p className="text-xs text-[#91A4B8] line-clamp-2 min-h-[32px] mb-3">
                  {gesture.description || 'No description provided.'}
                </p>

                {/* Metadata Row: Action & Sample Count */}
                <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-[rgba(11,18,32,0.5)] border border-[rgba(148,180,210,0.1)] text-xs font-mono mb-4">
                  <div>
                    <span className="text-[10px] text-[#61758B] uppercase block">Action</span>
                    <span className="text-[#F1F5F9] font-medium">{gesture.action}</span>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-[#61758B] uppercase block">Collected</span>
                    <span
                      className={`font-bold flex items-center gap-1 ${
                        isAdequate ? 'text-[#42F5A5]' : 'text-[#FFB547]'
                      }`}
                    >
                      {isAdequate ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : (
                        <AlertTriangle className="w-3 h-3" />
                      )}
                      {sampleCount} samples
                    </span>
                  </div>
                </div>
              </div>

              {/* Bottom Action Buttons */}
              <div className="flex items-center justify-between gap-2 pt-2 border-t border-[rgba(148,180,210,0.1)]">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSelectForCollection(gesture.id)}
                  icon={<Play className="w-3 h-3 text-[#42F5A5]" />}
                  className="text-xs py-1"
                >
                  Collect Samples
                </Button>

                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onOpenEdit(gesture)}
                    icon={<Edit2 className="w-3.5 h-3.5 text-[#91A4B8]" />}
                    title="Edit Gesture"
                    className="p-1.5"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(gesture.id, gesture.name)}
                    icon={<Trash2 className="w-3.5 h-3.5 text-[#FF647C]" />}
                    title="Delete Gesture"
                    className="p-1.5 hover:bg-[rgba(255,100,124,0.15)]"
                  />
                </div>
              </div>
            </Card>
          );
        })}

        {filteredGestures.length === 0 && (
          <div className="col-span-full py-12 flex flex-col items-center justify-center text-center p-6 rounded-2xl bg-[rgba(11,18,32,0.4)] border border-dashed border-[rgba(148,180,210,0.2)]">
            <Sparkles className="w-8 h-8 text-[#91A4B8] mb-2 opacity-60" />
            <h4 className="text-sm font-semibold text-white">No gestures found</h4>
            <p className="text-xs text-[#91A4B8] max-w-sm mt-1 mb-4">
              {searchTerm
                ? `No gestures match query "${searchTerm}".`
                : 'Get started by creating your first custom gesture!'}
            </p>
            <Button variant="primary" size="sm" onClick={onOpenCreate} icon={<Plus className="w-3.5 h-3.5" />}>
              Create Gesture
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
