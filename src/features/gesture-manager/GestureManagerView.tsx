import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Hand,
  Grab,
  MousePointer,
  Sparkles,
  CircleDot,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Music,
  Plus,
  Trash2,
  Edit2,
  Sliders,
  CheckCircle2,
  HelpCircle,
  RotateCcw,
} from 'lucide-react';
import { useGestureStore } from '../../store/gestureStore';
import { useSettingsStore } from '../../store/settingsStore';
import { useActivityStore } from '../../store/activityStore';
import { GestureDefinition, GestureAction, GestureType, GESTURE_ACTION_LABELS } from '../../types/gesture';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Switch } from '../../components/ui/Switch';
import { Slider } from '../../components/ui/Slider';
import { Select } from '../../components/ui/Select';
import { Modal } from '../../components/ui/Modal';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Hand,
  Grab,
  MousePointer,
  Sparkles,
  CircleDot,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Music,
};

const ACTION_OPTIONS = Object.entries(GESTURE_ACTION_LABELS).map(([val, label]) => ({
  value: val,
  label,
}));

export const GestureManagerView: React.FC = () => {
  const { gestures, addGesture, updateGesture, toggleGestureEnabled, deleteGesture, resetToDefaults } =
    useGestureStore();
  const { settings, updateDragDrop } = useSettingsStore();
  const { addLog } = useActivityStore();

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGesture, setEditingGesture] = useState<GestureDefinition | null>(null);

  // Form state
  const [formData, setFormData] = useState<{
    name: string;
    type: GestureType;
    description: string;
    action: GestureAction;
    confidenceThreshold: number;
    enabled: boolean;
    customShortcut: string;
  }>({
    name: '',
    type: 'static',
    description: '',
    action: 'no_action',
    confidenceThreshold: 0.8,
    enabled: true,
    customShortcut: '',
  });

  const openCreateModal = () => {
    setEditingGesture(null);
    setFormData({
      name: '',
      type: 'static',
      description: '',
      action: 'move_cursor',
      confidenceThreshold: 0.8,
      enabled: true,
      customShortcut: '',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (gesture: GestureDefinition) => {
    setEditingGesture(gesture);
    setFormData({
      name: gesture.name,
      type: gesture.type,
      description: gesture.description,
      action: gesture.action,
      confidenceThreshold: gesture.confidenceThreshold,
      enabled: gesture.enabled,
      customShortcut: gesture.customShortcut || '',
    });
    setIsModalOpen(true);
  };

  const handleSaveModal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    if (editingGesture) {
      updateGesture(editingGesture.id, formData);
      addLog({
        category: 'gesture',
        description: `Updated gesture "${formData.name}" configuration`,
        status: 'info',
        isSimulated: false,
      });
    } else {
      addGesture({
        name: formData.name,
        type: formData.type,
        description: formData.description,
        action: formData.action,
        confidenceThreshold: formData.confidenceThreshold,
        enabled: formData.enabled,
        icon: 'Sparkles',
        customShortcut: formData.customShortcut,
      });
      addLog({
        category: 'gesture',
        description: `Created new custom gesture: "${formData.name}"`,
        status: 'success',
        isSimulated: false,
      });
    }

    setIsModalOpen(false);
  };

  const handleDelete = (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete custom gesture "${name}"?`)) {
      deleteGesture(id);
      addLog({
        category: 'gesture',
        description: `Deleted custom gesture "${name}"`,
        status: 'warning',
        isSimulated: false,
      });
    }
  };

  return (
    <div className="w-full flex flex-col gap-8 select-none">
      {/* Top Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass rounded-2xl p-5 border border-[rgba(148,180,210,0.18)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-lg font-bold text-white">Gesture Catalog & Action Mapper</h2>
            <Badge variant="cyan">{gestures.length} Total Gestures</Badge>
          </div>
          <p className="text-xs text-[#91A4B8]">
            Customize pose recognition triggers, sensitivity thresholds, and virtual output events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={resetToDefaults}
            icon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Reset Defaults
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={openCreateModal}
            icon={<Plus className="w-4 h-4" />}
          >
            Add Custom Gesture
          </Button>
        </div>
      </div>

      {/* GESTURES GRID */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[#91A4B8]">
            Registered Static & Temporal Gestures
          </h3>
          <span className="text-xs text-[#61758B]">Configured in Local Storage</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {gestures.map((gesture) => {
            const Icon = ICON_MAP[gesture.icon] || Sparkles;

            return (
              <Card
                key={gesture.id}
                variant="glass"
                className={`p-5 flex flex-col justify-between transition-all ${
                  !gesture.enabled ? 'opacity-60 bg-[rgba(11,18,32,0.4)]' : ''
                }`}
              >
                <div>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center p-2 border ${
                          gesture.enabled
                            ? 'bg-[rgba(72,221,245,0.1)] border-[rgba(72,221,245,0.25)] text-[#48DDF5]'
                            : 'bg-[rgba(18,29,45,0.5)] border-[rgba(148,180,210,0.1)] text-[#61758B]'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white flex items-center gap-2">
                          {gesture.name}
                          {!gesture.isDefault && (
                            <Badge variant="purple" className="text-[10px]">
                              Custom
                            </Badge>
                          )}
                        </h4>
                        <span className="text-[10px] font-mono uppercase text-[#91A4B8]">
                          {gesture.type} Pose
                        </span>
                      </div>
                    </div>

                    <Switch
                      checked={gesture.enabled}
                      onChange={() => toggleGestureEnabled(gesture.id)}
                      title={gesture.enabled ? 'Disable gesture' : 'Enable gesture'}
                    />
                  </div>

                  <p className="text-xs text-[#91A4B8] leading-relaxed mb-4 min-h-[36px]">
                    {gesture.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-[rgba(148,180,210,0.12)] space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#91A4B8]">Assigned Action:</span>
                    <span className="font-mono text-[#42F5A5] font-semibold bg-[rgba(66,245,165,0.08)] px-2 py-0.5 rounded border border-[rgba(66,245,165,0.2)]">
                      {GESTURE_ACTION_LABELS[gesture.action] || gesture.action}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#91A4B8]">Confidence Threshold:</span>
                    <span className="font-mono text-[#48DDF5]">
                      {Math.round(gesture.confidenceThreshold * 100)}%
                    </span>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEditModal(gesture)}
                      icon={<Edit2 className="w-3.5 h-3.5" />}
                    >
                      Edit
                    </Button>

                    {!gesture.isDefault && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(gesture.id, gesture.name)}
                        icon={<Trash2 className="w-3.5 h-3.5 text-[#FF647C]" />}
                      >
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* SECTION 10: DRAG & DROP INTERACTION SETTINGS */}
      <Card variant="glass-strong" className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[rgba(148,180,210,0.12)] mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Grab className="w-5 h-5 text-[#48DDF5]" />
              <h3 className="text-base font-bold text-white">Drag & Drop Interaction Matrix</h3>
              <Badge variant="cyan">Section 10</Badge>
            </div>
            <p className="text-xs text-[#91A4B8]">
              Calibrate virtual pinch-to-hold mechanics, activation latency, and accidental release damping.
            </p>
          </div>

          <Switch
            checked={settings.dragDrop.enabled}
            onChange={(val) => updateDragDrop({ enabled: val })}
            label={settings.dragDrop.enabled ? 'Drag Mode ON' : 'Drag Mode OFF'}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Controls Column (Col 7) */}
          <div className="lg:col-span-7 space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Activation Gesture"
                description="Pose that triggers click-and-hold capture"
                value={settings.dragDrop.activationGesture}
                onChange={(val) => updateDragDrop({ activationGesture: val })}
                options={[
                  { value: 'pinch', label: 'Index + Thumb Pinch' },
                  { value: 'fist', label: 'Closed Fist' },
                  { value: 'two_fingers', label: 'Two Fingers Clench' },
                ]}
              />

              <Select
                label="Release Gesture"
                description="Pose that drops the dragged payload"
                value={settings.dragDrop.releaseGesture}
                onChange={(val) => updateDragDrop({ releaseGesture: val })}
                options={[
                  { value: 'open_palm', label: 'Open Flat Palm' },
                  { value: 'pinch_release', label: 'Release Pinch' },
                  { value: 'fist_open', label: 'Unclench Fist' },
                ]}
              />
            </div>

            <Slider
              label="Drag Activation Delay"
              description="Hold duration before locking mouse down"
              min={100}
              max={1000}
              step={50}
              unit="ms"
              value={settings.dragDrop.activationDelay}
              onChange={(val) => updateDragDrop({ activationDelay: val })}
            />

            <Slider
              label="Minimum Hold Duration"
              description="Required continuous pose contact before initiating item displacement"
              min={200}
              max={1200}
              step={50}
              unit="ms"
              value={settings.dragDrop.minHoldDuration}
              onChange={(val) => updateDragDrop({ minHoldDuration: val })}
            />

            <Slider
              label="Drag Smoothing"
              description="Damping filter applied during active drag state"
              min={0.1}
              max={0.95}
              step={0.05}
              value={settings.dragDrop.cursorSmoothing}
              onChange={(val) => updateDragDrop({ cursorSmoothing: val })}
              formatValue={(v) => `${(v * 100).toFixed(0)}%`}
            />

            <div className="pt-2 flex items-center justify-between">
              <Switch
                checked={settings.dragDrop.accidentalReleasePrevention}
                onChange={(val) => updateDragDrop({ accidentalReleasePrevention: val })}
                label="Accidental-Release Prevention"
                description="Requires 200ms grace period of lost tracking before releasing mouse button"
              />
            </div>
          </div>

          {/* Simulated Drag & Drop Animation Preview Canvas (Col 5) */}
          <div className="lg:col-span-5 flex flex-col items-center">
            <div className="w-full aspect-[4/3] rounded-2xl bg-[rgba(7,11,18,0.7)] border border-[rgba(148,180,210,0.18)] p-4 flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#91A4B8]">
                <span>Interactive Drag Simulation</span>
                <span className="text-[#42F5A5]">Preview (Simulated)</span>
              </div>

              {/* Animated Dragging Object */}
              <div className="relative w-full h-36 flex items-center justify-center">
                <motion.div
                  animate={{
                    x: [-60, 60, -60],
                    y: [-15, 15, -15],
                  }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#48DDF5]/20 to-[#42F5A5]/20 border border-[#48DDF5] shadow-[0_0_20px_rgba(72,221,245,0.3)] flex items-center gap-2 cursor-grab"
                >
                  <Grab className="w-4 h-4 text-[#48DDF5]" />
                  <span className="text-xs font-bold text-white">Dragged Payload</span>
                </motion.div>
              </div>

              <div className="text-[10px] text-[#61758B] text-center">
                Emergency release key: <kbd className="text-[#FFCB70]">Escape</kbd>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* CREATE / EDIT GESTURE MODAL */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingGesture ? 'Edit Gesture Mapping' : 'Create Custom Gesture'}
        description="Bind a hand configuration to an operating system action"
      >
        <form onSubmit={handleSaveModal} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-[#F1F5F9] block mb-1">Gesture Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Three Finger Salute"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-[rgba(11,18,32,0.85)] border border-[rgba(148,180,210,0.2)] rounded-xl px-3.5 py-2 text-sm text-[#F1F5F9] focus:outline-none focus:border-[#48DDF5]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Gesture Type"
              value={formData.type}
              onChange={(val) => setFormData({ ...formData, type: val as GestureType })}
              options={[
                { value: 'static', label: 'Static (Instant Pose)' },
                { value: 'temporal', label: 'Temporal (Time Series Gesture)' },
              ]}
            />

            <Select
              label="Assigned Action"
              value={formData.action}
              onChange={(val) => setFormData({ ...formData, action: val as GestureAction })}
              options={ACTION_OPTIONS}
            />
          </div>

          <div>
            <label className="text-xs font-medium text-[#F1F5F9] block mb-1">Description</label>
            <textarea
              rows={2}
              placeholder="Describe the finger alignment and posture..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full bg-[rgba(11,18,32,0.85)] border border-[rgba(148,180,210,0.2)] rounded-xl px-3.5 py-2 text-xs text-[#F1F5F9] focus:outline-none focus:border-[#48DDF5]"
            />
          </div>

          <Slider
            label="Confidence Threshold"
            description="Minimum match probability required"
            min={0.5}
            max={0.98}
            step={0.02}
            value={formData.confidenceThreshold}
            onChange={(val) => setFormData({ ...formData, confidenceThreshold: val })}
            formatValue={(v) => `${(v * 100).toFixed(0)}%`}
          />

          <div className="pt-2 flex justify-between items-center">
            <Switch
              checked={formData.enabled}
              onChange={(val) => setFormData({ ...formData, enabled: val })}
              label="Enable immediately"
            />
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-[rgba(148,180,210,0.12)]">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              {editingGesture ? 'Save Changes' : 'Create Gesture'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
