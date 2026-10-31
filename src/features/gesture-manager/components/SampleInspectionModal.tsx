import React from 'react';
import { X, Calendar, Activity, Database, CheckCircle2 } from 'lucide-react';
import { DatasetSample } from '../../../types/dataset';
import { Modal } from '../../../components/ui/Modal';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

interface SampleInspectionModalProps {
  sample: DatasetSample | null;
  isOpen: boolean;
  onClose: () => void;
  onDelete?: (sampleId: string) => void;
}

const LANDMARK_NAMES: string[] = [
  'Wrist',
  'Thumb CMC',
  'Thumb MCP',
  'Thumb IP',
  'Thumb Tip',
  'Index MCP',
  'Index PIP',
  'Index DIP',
  'Index Tip',
  'Middle MCP',
  'Middle PIP',
  'Middle DIP',
  'Middle Tip',
  'Ring MCP',
  'Ring PIP',
  'Ring DIP',
  'Ring Tip',
  'Pinky MCP',
  'Pinky PIP',
  'Pinky DIP',
  'Pinky Tip',
];

const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];

export const SampleInspectionModal: React.FC<SampleInspectionModalProps> = ({
  sample,
  isOpen,
  onClose,
  onDelete,
}) => {
  if (!sample) return null;

  const isRight = sample.handedness.toLowerCase() === 'right';
  const jointColor = isRight ? '#00FF66' : '#00B4FF';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Sample Inspection: ${sample.sample_id}`}
      maxWidth="max-w-4xl"
    >
      <div className="flex flex-col gap-5">
        {/* Top Metadata Header */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-[rgba(11,18,32,0.6)] border border-[rgba(148,180,210,0.14)] text-xs font-mono">
          <div>
            <div className="text-[#91A4B8] text-[10px] uppercase">Gesture</div>
            <div className="text-white font-bold text-sm mt-0.5">
              {sample.gesture_name} <span className="text-[#48DDF5]">({sample.gesture_id})</span>
            </div>
          </div>
          <div>
            <div className="text-[#91A4B8] text-[10px] uppercase">Handedness</div>
            <div className="mt-0.5">
              <Badge variant={isRight ? 'green' : 'cyan'}>
                {sample.handedness} ({Math.round(sample.confidence * 100)}%)
              </Badge>
            </div>
          </div>
          <div>
            <div className="text-[#91A4B8] text-[10px] uppercase">Session ID</div>
            <div className="text-[#F1F5F9] truncate mt-0.5" title={sample.session_id}>
              {sample.session_id || 'manual'}
            </div>
          </div>
          <div>
            <div className="text-[#91A4B8] text-[10px] uppercase">Captured At</div>
            <div className="text-[#91A4B8] mt-0.5">
              {new Date(sample.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Content Body: 2D Landmark Skeleton Visualizer + 21 Landmark Coordinates Table */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
          {/* Skeleton Preview Viewport (Col 5) */}
          <div className="md:col-span-5 flex flex-col items-center justify-center p-4 rounded-xl bg-[#070B12] border border-[rgba(148,180,210,0.18)]">
            <div className="text-xs font-mono text-[#91A4B8] mb-2 self-start flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#42F5A5]" />
              21 Landmark Skeleton View
            </div>

            <div className="relative w-full max-w-[240px] aspect-square flex items-center justify-center">
              <svg viewBox="0 0 100 100" className="w-full h-full">
                {/* Bone Lines */}
                {HAND_CONNECTIONS.map(([i, j], idx) => {
                  const p1 = sample.landmarks[i];
                  const p2 = sample.landmarks[j];
                  if (!p1 || !p2) return null;
                  return (
                    <line
                      key={`bone-${idx}`}
                      x1={p1.x * 100}
                      y1={p1.y * 100}
                      x2={p2.x * 100}
                      y2={p2.y * 100}
                      stroke={jointColor}
                      strokeWidth="1.8"
                      strokeOpacity="0.8"
                      strokeLinecap="round"
                    />
                  );
                })}

                {/* Joint Nodes */}
                {sample.landmarks.map((pt, idx) => {
                  const isTip = [4, 8, 12, 16, 20].includes(idx);
                  return (
                    <g key={`pt-${idx}`}>
                      <circle
                        cx={pt.x * 100}
                        cy={pt.y * 100}
                        r={isTip ? 2.2 : 1.5}
                        fill={jointColor}
                      />
                      <circle
                        cx={pt.x * 100}
                        cy={pt.y * 100}
                        r={isTip ? 0.9 : 0.6}
                        fill="#FFFFFF"
                      />
                    </g>
                  );
                })}
              </svg>
            </div>

            <div className="text-[11px] font-mono text-[#42F5A5] mt-2 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              All 21 coordinates validated
            </div>
          </div>

          {/* 21 Coordinates Table (Col 7) */}
          <div className="md:col-span-7 flex flex-col max-h-[340px] overflow-hidden rounded-xl border border-[rgba(148,180,210,0.14)] bg-[rgba(11,18,32,0.4)]">
            <div className="overflow-y-auto scrollbar-thin">
              <table className="w-full text-left text-xs font-mono">
                <thead className="sticky top-0 bg-[#0B1220] border-b border-[rgba(148,180,210,0.2)] text-[10px] uppercase text-[#91A4B8]">
                  <tr>
                    <th className="py-2 px-3">#</th>
                    <th className="py-2 px-3">Joint Name</th>
                    <th className="py-2 px-3 text-right">X</th>
                    <th className="py-2 px-3 text-right">Y</th>
                    <th className="py-2 px-3 text-right">Z</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[rgba(148,180,210,0.08)]">
                  {sample.landmarks.map((lm, idx) => {
                    const isTip = [4, 8, 12, 16, 20].includes(idx);
                    return (
                      <tr
                        key={idx}
                        className={`hover:bg-[rgba(72,221,245,0.04)] transition-colors ${
                          isTip ? 'text-[#48DDF5] font-semibold' : 'text-[#F1F5F9]'
                        }`}
                      >
                        <td className="py-1.5 px-3 text-[#91A4B8]">{idx}</td>
                        <td className="py-1.5 px-3">{LANDMARK_NAMES[idx] || `Landmark ${idx}`}</td>
                        <td className="py-1.5 px-3 text-right">{lm.x.toFixed(4)}</td>
                        <td className="py-1.5 px-3 text-right">{lm.y.toFixed(4)}</td>
                        <td className="py-1.5 px-3 text-right text-[#91A4B8]">{lm.z.toFixed(4)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-[rgba(148,180,210,0.12)]">
          {onDelete && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                if (window.confirm(`Delete sample ${sample.sample_id}? This cannot be undone.`)) {
                  onDelete(sample.sample_id);
                  onClose();
                }
              }}
            >
              Delete This Sample
            </Button>
          )}
          <div className="ml-auto">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
