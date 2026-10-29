import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface HandTrackingVisualizerProps {
  className?: string;
  showDiagnostics?: boolean;
  activeGestureName?: string;
  isSimulated?: boolean;
}

// Normalized 21 MediaPipe landmarks mapped to 400x440 viewBox
const BASE_LANDMARKS = [
  // 0: Wrist
  { id: 0, x: 200, y: 380, name: 'Wrist' },
  // Thumb: 1-4
  { id: 1, x: 160, y: 340, name: 'Thumb CMC' },
  { id: 2, x: 130, y: 295, name: 'Thumb MCP' },
  { id: 3, x: 105, y: 250, name: 'Thumb IP' },
  { id: 4, x: 85, y: 210, name: 'Thumb Tip' },
  // Index: 5-8
  { id: 5, x: 165, y: 235, name: 'Index MCP' },
  { id: 6, x: 155, y: 175, name: 'Index PIP' },
  { id: 7, x: 148, y: 125, name: 'Index DIP' },
  { id: 8, x: 142, y: 80, name: 'Index Tip' },
  // Middle: 9-12
  { id: 9, x: 202, y: 228, name: 'Middle MCP' },
  { id: 10, x: 202, y: 160, name: 'Middle PIP' },
  { id: 11, x: 202, y: 110, name: 'Middle DIP' },
  { id: 12, x: 202, y: 65, name: 'Middle Tip' },
  // Ring: 13-16
  { id: 13, x: 238, y: 238, name: 'Ring MCP' },
  { id: 14, x: 246, y: 178, name: 'Ring PIP' },
  { id: 15, x: 252, y: 132, name: 'Ring DIP' },
  { id: 16, x: 258, y: 92, name: 'Ring Tip' },
  // Pinky: 17-20
  { id: 17, x: 272, y: 260, name: 'Pinky MCP' },
  { id: 18, x: 292, y: 215, name: 'Pinky PIP' },
  { id: 19, x: 305, y: 180, name: 'Pinky DIP' },
  { id: 20, x: 318, y: 145, name: 'Pinky Tip' },
];

const BONES: [number, number][] = [
  // Palm base
  [0, 1], [1, 2], [2, 5], [5, 9], [9, 13], [13, 17], [17, 0],
  // Thumb
  [2, 3], [3, 4],
  // Index
  [5, 6], [6, 7], [7, 8],
  // Middle
  [9, 10], [10, 11], [11, 12],
  // Ring
  [13, 14], [14, 15], [15, 16],
  // Pinky
  [17, 18], [18, 19], [19, 20],
];

export const HandTrackingVisualizer: React.FC<HandTrackingVisualizerProps> = ({
  className = '',
  showDiagnostics = true,
  activeGestureName = 'Index Finger (Point)',
  isSimulated = true,
}) => {
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setPulse((p) => (p + 1) % 100);
    }, 50);
    return () => clearInterval(id);
  }, []);

  // Subtle natural floating jitter for demo landmarks
  const jitter = Math.sin(pulse * 0.1) * 2;

  return (
    <div className={`relative w-full h-full flex flex-col items-center justify-center p-4 select-none overflow-hidden ${className}`}>
      {/* Background Cyber Grid */}
      <div className="absolute inset-0 opacity-15 pointer-events-none">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="hand-grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#48DDF5" strokeWidth="0.5" strokeOpacity="0.4" />
              <circle cx="0" cy="0" r="1" fill="#48DDF5" fillOpacity="0.8" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#hand-grid)" />
        </svg>
      </div>

      {/* Target Reticle Radar Circles */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
        <div className="w-72 h-72 rounded-full border border-dashed border-[#48DDF5] animate-[spin_60s_linear_infinite]" />
        <div className="absolute w-52 h-52 rounded-full border border-[#42F5A5]/40" />
      </div>

      {/* Main SVG Hand Mesh */}
      <div className="relative z-10 w-full max-w-[380px] aspect-[400/440]">
        <svg
          viewBox="0 0 400 440"
          className="w-full h-full filter drop-shadow-[0_0_12px_rgba(72,221,245,0.25)]"
        >
          <defs>
            <linearGradient id="laserGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#48DDF5" stopOpacity="0" />
              <stop offset="50%" stopColor="#48DDF5" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#42F5A5" stopOpacity="0" />
            </linearGradient>

            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Faint Hand Silhouette Area */}
          <path
            d="M 195 385 C 150 365 110 320 85 210 C 75 190 95 180 110 205 L 125 240 L 140 85 C 143 70 157 70 160 85 L 172 170 L 198 70 C 202 55 215 55 218 70 L 222 170 L 254 95 C 258 80 270 82 272 98 L 268 180 L 314 145 C 322 135 334 145 328 160 C 315 220 280 340 205 385 Z"
            fill="rgba(18, 29, 45, 0.4)"
            stroke="rgba(72, 221, 245, 0.12)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />

          {/* Bone Skeletal Connections */}
          {BONES.map(([startIdx, endIdx], i) => {
            const p1 = BASE_LANDMARKS[startIdx];
            const p2 = BASE_LANDMARKS[endIdx];
            return (
              <line
                key={`bone-${i}`}
                x1={p1.x + (startIdx === 8 ? jitter : 0)}
                y1={p1.y}
                x2={p2.x + (endIdx === 8 ? jitter : 0)}
                y2={p2.y}
                stroke="rgba(72, 221, 245, 0.55)"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            );
          })}

          {/* Secondary Palm Structural Web */}
          <line x1={BASE_LANDMARKS[2].x} y1={BASE_LANDMARKS[2].y} x2={BASE_LANDMARKS[9].x} y2={BASE_LANDMARKS[9].y} stroke="rgba(66, 245, 165, 0.25)" strokeWidth="1" strokeDasharray="2 2" />
          <line x1={BASE_LANDMARKS[5].x} y1={BASE_LANDMARKS[5].y} x2={BASE_LANDMARKS[13].x} y2={BASE_LANDMARKS[13].y} stroke="rgba(66, 245, 165, 0.25)" strokeWidth="1" strokeDasharray="2 2" />

          {/* Landmark Nodes */}
          {BASE_LANDMARKS.map((lm) => {
            const isFingertip = [4, 8, 12, 16, 20].includes(lm.id);
            const isTargetPoint = lm.id === 8; // Index tip
            const currentX = lm.x + (isTargetPoint ? jitter : 0);

            return (
              <g key={`node-${lm.id}`}>
                {/* Outer Ring for Fingertips */}
                {isFingertip && (
                  <circle
                    cx={currentX}
                    cy={lm.y}
                    r={isTargetPoint ? 9 : 6}
                    fill="none"
                    stroke={isTargetPoint ? '#42F5A5' : '#48DDF5'}
                    strokeWidth="1.5"
                    opacity={0.8}
                    className={isTargetPoint ? 'animate-ping' : ''}
                  />
                )}

                {/* Inner Core Node */}
                <circle
                  cx={currentX}
                  cy={lm.y}
                  r={isFingertip ? 4.5 : 3}
                  fill={isTargetPoint ? '#42F5A5' : '#48DDF5'}
                  filter="url(#glow)"
                />

                {/* Micro Landmark Number */}
                <text
                  x={currentX + 6}
                  y={lm.y - 4}
                  fill="rgba(148, 180, 210, 0.6)"
                  fontSize="8"
                  fontFamily="monospace"
                >
                  {lm.id}
                </text>
              </g>
            );
          })}

          {/* Animated Scanning Line Sweeper */}
          <motion.g
            animate={{
              y: [40, 390, 40],
            }}
            transition={{
              duration: 3.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <line
              x1="50"
              y1="0"
              x2="350"
              y2="0"
              stroke="#48DDF5"
              strokeWidth="1.5"
              strokeOpacity="0.8"
              filter="url(#glow)"
            />
            <rect x="50" y="-12" width="300" height="24" fill="url(#laserGrad)" opacity="0.35" />
          </motion.g>
        </svg>
      </div>

      {/* Diagnostics & Specs Badge Footer */}
      {showDiagnostics && (
        <div className="relative z-10 mt-3 w-full max-w-[360px] flex flex-col gap-2">
          <div className="flex items-center justify-between text-[11px] text-[#91A4B8] font-mono px-2 py-1.5 rounded-lg bg-[rgba(11,18,32,0.85)] border border-[rgba(148,180,210,0.15)] backdrop-blur-sm">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#42F5A5] animate-pulse" />
              21 Hand Landmarks
            </span>
            <span className="text-[#48DDF5]">MediaPipe Engine</span>
            <span className="text-xs text-[#91A4B8]">30 FPS</span>
          </div>

          <div className="flex items-center justify-between px-2 text-[10px] text-[#61758B]">
            <span>{isSimulated ? 'Real-Time Tracking Preview (Simulated)' : 'Live Model Stream'}</span>
            <span className="text-[#42F5A5] font-medium">{activeGestureName}</span>
          </div>
        </div>
      )}
    </div>
  );
};
