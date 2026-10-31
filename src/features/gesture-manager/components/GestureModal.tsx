import React, { useState, useEffect } from 'react';
import { Sparkles, Hash, Layers } from 'lucide-react';
import { GestureDefinition, GestureType, GestureAction, GESTURE_ACTION_LABELS } from '../../../types/gesture';
import { Modal } from '../../../components/ui/Modal';
import { Button } from '../../../components/ui/Button';
import { Select } from '../../../components/ui/Select';
import { Slider } from '../../../components/ui/Slider';

interface GestureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (gestureData: {
    id?: string;
    name: string;
    description: string;
    type: GestureType;
    action: GestureAction;
    confidenceThreshold: number;
    customShortcut?: string;
  }) => Promise<void>;
  editingGesture: GestureDefinition | null;
}

const ACTION_OPTIONS = Object.entries(GESTURE_ACTION_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export const GestureModal: React.FC<GestureModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingGesture,
}) => {
  const [name, setName] = useState('');
  const [customId, setCustomId] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<GestureType>('static');
  const [action, setAction] = useState<GestureAction>('move_cursor');
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.8);
  const [customShortcut, setCustomShortcut] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editingGesture) {
      setName(editingGesture.name);
      setCustomId(editingGesture.id);
      setDescription(editingGesture.description || '');
      setType(editingGesture.type);
      setAction(editingGesture.action);
      setConfidenceThreshold(editingGesture.confidenceThreshold || 0.8);
      setCustomShortcut(editingGesture.customShortcut || '');
    } else {
      setName('');
      setCustomId('');
      setDescription('');
      setType('static');
      setAction('move_cursor');
      setConfidenceThreshold(0.8);
      setCustomShortcut('');
    }
    setError(null);
  }, [editingGesture, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Gesture name is required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSave({
        id: customId.trim() || undefined,
        name: name.trim(),
        description: description.trim(),
        type,
        action,
        confidenceThreshold,
        customShortcut: customShortcut.trim() || undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to save gesture');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editingGesture ? `Edit Gesture: ${editingGesture.name}` : 'Register New Custom Gesture'}
      maxWidth="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-xs">
        {error && (
          <div className="p-3 rounded-lg bg-[rgba(255,100,124,0.12)] border border-[rgba(255,100,124,0.3)] text-[#FF647C]">
            {error}
          </div>
        )}

        {/* Gesture Name & ID */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-[#91A4B8] font-medium mb-1">
              Gesture Name <span className="text-[#FF647C]">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Victory Sign"
              required
              className="w-full px-3 py-2 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.2)] text-white focus:outline-none focus:border-[#48DDF5] transition-colors"
            />
          </div>

          <div>
            <label className="block text-[#91A4B8] font-medium mb-1 flex items-center justify-between">
              <span>Gesture ID</span>
              <span className="text-[10px] text-[#61758B]">(Auto-generated if blank)</span>
            </label>
            <div className="relative">
              <Hash className="w-3.5 h-3.5 text-[#91A4B8] absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                value={customId}
                onChange={(e) => setCustomId(e.target.value.toUpperCase())}
                placeholder="e.g. G008"
                disabled={!!editingGesture}
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.2)] text-white focus:outline-none focus:border-[#48DDF5] transition-colors disabled:opacity-50 font-mono uppercase"
              />
            </div>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-[#91A4B8] font-medium mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            placeholder="Describe the hand pose or usage instructions..."
            className="w-full px-3 py-2 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.2)] text-white focus:outline-none focus:border-[#48DDF5] transition-colors resize-none"
          />
        </div>

        {/* Type & Action */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-[#91A4B8] font-medium mb-1">Gesture Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as GestureType)}
              className="w-full px-3 py-2 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.2)] text-white focus:outline-none focus:border-[#48DDF5] transition-colors cursor-pointer"
            >
              <option value="static" className="bg-[#0B1220]">Static (Single Pose)</option>
              <option value="temporal" className="bg-[#0B1220]">Temporal (Motion Path)</option>
            </select>
          </div>

          <div>
            <label className="block text-[#91A4B8] font-medium mb-1">Mapped Action</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value as GestureAction)}
              className="w-full px-3 py-2 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.2)] text-white focus:outline-none focus:border-[#48DDF5] transition-colors cursor-pointer"
            >
              {ACTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[#0B1220]">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Custom Keyboard Shortcut */}
        {action === 'custom_shortcut' && (
          <div>
            <label className="block text-[#91A4B8] font-medium mb-1">Keyboard Shortcut</label>
            <input
              type="text"
              value={customShortcut}
              onChange={(e) => setCustomShortcut(e.target.value)}
              placeholder="e.g. Ctrl+Shift+P"
              className="w-full px-3 py-2 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.2)] text-white font-mono"
            />
          </div>
        )}

        {/* Confidence Threshold Slider */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-[#91A4B8] font-medium">Confidence Threshold</label>
            <span className="font-mono text-[#48DDF5] font-bold">
              {Math.round(confidenceThreshold * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
            className="w-full accent-[#48DDF5] cursor-pointer"
          />
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[rgba(148,180,210,0.12)]">
          <Button variant="ghost" size="sm" type="button" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : editingGesture ? 'Update Gesture' : 'Register Gesture'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
