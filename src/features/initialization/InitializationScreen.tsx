import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MousePointer,
  Mouse,
  ArrowUpDown,
  Grab,
  Presentation,
  PlaySquare,
  Sparkles,
  Sliders,
  CheckCircle2,
  Clock,
  Loader2,
  AlertTriangle,
  RotateCcw,
  Minus,
  Square,
  X,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { HandTrackingVisualizer } from '../../components/visuals/HandTrackingVisualizer';
import { Button } from '../../components/ui/Button';
import { Switch } from '../../components/ui/Switch';
import { Badge } from '../../components/ui/Badge';

const FEATURE_CARDS = [
  {
    icon: MousePointer,
    name: 'Cursor Control',
    desc: 'Fluid air mouse navigation driven by real-time index fingertip motion vectoring.',
    tag: 'Core',
  },
  {
    icon: Mouse,
    name: 'Click Actions',
    desc: 'Zero-latency pinch detection for left, right, and double clicks with debounce.',
    tag: 'Precise',
  },
  {
    icon: ArrowUpDown,
    name: 'Scroll Control',
    desc: 'Vertical gestures for variable-speed document and web page scrolling.',
    tag: 'Intuitive',
  },
  {
    icon: Grab,
    name: 'Drag & Drop',
    desc: 'Continuous fist-clench tracking for natural window and item dragging.',
    tag: 'Advanced',
  },
  {
    icon: Presentation,
    name: 'Presentation Mode',
    desc: 'Swipe gestures mapped to next/previous slide triggers during keynotes.',
    tag: 'Productivity',
  },
  {
    icon: PlaySquare,
    name: 'Media Controls',
    desc: 'Quick hand signs to play, pause, and adjust system audio volume.',
    tag: 'Media',
  },
  {
    icon: Sparkles,
    name: 'Custom Gestures',
    desc: 'Record unique poses and bind them to application shortcuts.',
    tag: 'Custom',
  },
  {
    icon: Sliders,
    name: 'Feature Toggle',
    desc: 'Fine-grained enable/disable controls for every gesture independently.',
    tag: 'Control',
  },
];

export const InitializationScreen: React.FC = () => {
  const {
    initState,
    startInitialization,
    cancelInitialization,
    retryInitialization,
    advanceInitStep,
    setAutoStart,
    setCurrentView,
  } = useAppStore();

  const [mockFailure, setMockFailure] = useState(false);

  // Run initialization sequence timer if status is 'initializing'
  useEffect(() => {
    if (initState.status === 'idle') {
      startInitialization();
    }
  }, []);

  useEffect(() => {
    if (initState.status !== 'initializing') return;

    const currentStep = initState.steps[initState.currentStepIndex];
    if (!currentStep) return;

    const timeout = setTimeout(() => {
      // Allow user to trigger simulated failure if tested
      if (mockFailure && initState.currentStepIndex === 3) {
        useAppStore.setState((state) => {
          const steps = [...state.initState.steps];
          steps[3].state = 'failed';
          steps[3].errorMessage = 'Simulated camera device timeout (Demo error mode)';
          return {
            initState: {
              ...state.initState,
              status: 'failed',
              steps,
              statusMessage: 'Initialization halted: Camera interface check failed (Simulated).',
            },
          };
        });
        return;
      }

      advanceInitStep();
    }, currentStep.durationMs || 900);

    return () => clearTimeout(timeout);
  }, [initState.status, initState.currentStepIndex, mockFailure]);

  return (
    <div className="relative min-h-screen w-full bg-[#070B12] text-[#F1F5F9] flex flex-col justify-between overflow-x-hidden p-4 md:p-6 select-none">
      {/* Background radial glow spots */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[400px] bg-[radial-gradient(ellipse_at_top,rgba(72,221,245,0.08)_0%,transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[350px] bg-[radial-gradient(ellipse_at_bottom,rgba(66,245,165,0.06)_0%,transparent_70%)] pointer-events-none" />

      {/* TOP HEADER */}
      <header className="relative z-10 flex items-center justify-between pb-4 border-b border-[rgba(148,180,210,0.12)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#48DDF5] to-[#42F5A5] flex items-center justify-center p-0.5 shadow-[0_0_16px_rgba(72,221,245,0.3)]">
            <div className="w-full h-full bg-[#070B12] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-[#48DDF5]" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                GestureFlow <span className="text-[#48DDF5]">AI</span>
              </h1>
              <Badge variant="cyan">v1.0.0</Badge>
              <Badge variant="muted">Simulated Demo</Badge>
            </div>
            <p className="text-xs text-[#91A4B8]">Smart Hand Control for Your Computer</p>
          </div>
        </div>

        {/* Right side: Mock desktop window frame controls & status */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs text-[#91A4B8]">
            <span
              className={`w-2 h-2 rounded-full ${
                initState.status === 'completed'
                  ? 'bg-[#42F5A5]'
                  : initState.status === 'failed'
                  ? 'bg-[#FF647C]'
                  : 'bg-[#48DDF5] animate-pulse'
              }`}
            />
            <span className="capitalize">{initState.status} (Simulated)</span>
          </div>

          {/* Desktop Shell Mock Controls */}
          <div className="flex items-center gap-1 bg-[rgba(18,29,45,0.6)] px-2 py-1 rounded-lg border border-[rgba(148,180,210,0.15)] text-[#91A4B8]">
            <button
              title="Minimize (Desktop Shell Mock)"
              className="p-1 hover:text-white hover:bg-[rgba(148,180,210,0.1)] rounded transition-colors"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <button
              title="Maximize (Desktop Shell Mock)"
              className="p-1 hover:text-white hover:bg-[rgba(148,180,210,0.1)] rounded transition-colors"
            >
              <Square className="w-3 h-3" />
            </button>
            <button
              title="Close (Desktop Shell Mock)"
              className="p-1 hover:text-[#FF647C] hover:bg-[rgba(255,100,124,0.1)] rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* MAIN 3-COLUMN CONTENT AREA (Inspired by Reference A) */}
      <main className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 my-auto py-6 items-stretch">
        {/* LEFT COLUMN: Futuristic Hand Tracking Preview */}
        <div className="lg:col-span-4 flex flex-col">
          <div className="glass rounded-2xl p-5 border border-[rgba(148,180,210,0.16)] flex-1 flex flex-col justify-between relative overflow-hidden">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#91A4B8] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#48DDF5]" />
                Spatial Neural Model
              </span>
              <Badge variant="cyan" dot>
                Simulated Preview
              </Badge>
            </div>

            <div className="flex-1 min-h-[340px] flex items-center justify-center">
              <HandTrackingVisualizer
                showDiagnostics={true}
                activeGestureName="21 Keypoint Skeletal Mesh"
                isSimulated={true}
              />
            </div>

            <div className="mt-2 pt-3 border-t border-[rgba(148,180,210,0.1)] text-[11px] text-[#91A4B8] flex items-center justify-between">
              <span>Zero-latency local processing</span>
              <span className="text-[#48DDF5] font-mono">CV2+MediaPipe</span>
            </div>
          </div>
        </div>

        {/* CENTER COLUMN: Initialization Checklist & Progress */}
        <div className="lg:col-span-4 flex flex-col justify-between">
          <div className="glass rounded-2xl p-6 border border-[rgba(148,180,210,0.18)] flex-1 flex flex-col justify-between shadow-[0_8px_32px_rgba(0,0,0,0.3)]">
            <div>
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold tracking-tight text-white mb-1">GestureFlow AI</h2>
                <p className="text-xs text-[#91A4B8]">Initializing Your Gesture Controller</p>
                <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-[rgba(68,141,255,0.1)] border border-[rgba(68,141,255,0.2)] text-[11px] text-[#448DFF]">
                  <ShieldCheck className="w-3.5 h-3.5" /> Frontend Verification Mode
                </div>
              </div>

              {/* Checklist */}
              <div className="space-y-2.5 my-4">
                {initState.steps.map((step, idx) => {
                  const isCurrent = step.state === 'in_progress';
                  const isDone = step.state === 'completed';
                  const isFailed = step.state === 'failed';

                  return (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className={`flex items-center justify-between p-2.5 rounded-xl border text-xs transition-colors ${
                        isCurrent
                          ? 'bg-[rgba(72,221,245,0.08)] border-[#48DDF5]/40 text-white shadow-[0_0_12px_rgba(72,221,245,0.1)]'
                          : isDone
                          ? 'bg-[rgba(18,29,45,0.4)] border-[rgba(66,245,165,0.2)] text-[#F1F5F9]'
                          : isFailed
                          ? 'bg-[rgba(255,100,124,0.1)] border-[#FF647C]/40 text-[#FF647C]'
                          : 'bg-[rgba(11,18,32,0.5)] border-[rgba(148,180,210,0.08)] text-[#61758B]'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-[10px] text-[#91A4B8] w-4">
                          0{idx + 1}
                        </span>
                        <span className="font-medium">{step.label}</span>
                      </div>

                      <div>
                        {isDone && <CheckCircle2 className="w-4 h-4 text-[#42F5A5]" />}
                        {isCurrent && <Loader2 className="w-4 h-4 text-[#48DDF5] animate-spin" />}
                        {isFailed && <AlertTriangle className="w-4 h-4 text-[#FF647C]" />}
                        {step.state === 'pending' && <Clock className="w-3.5 h-3.5 text-[#61758B]" />}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Glowing Progress bar & Status Indicator */}
            <div className="mt-4 pt-4 border-t border-[rgba(148,180,210,0.12)]">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-[#91A4B8] truncate max-w-[220px]">
                  {initState.statusMessage}
                </span>
                <span className="font-mono font-bold text-[#48DDF5]">
                  {initState.progressPercent}%
                </span>
              </div>

              {/* Progress bar container */}
              <div className="w-full h-2 rounded-full bg-[#0B1220] border border-[rgba(148,180,210,0.15)] overflow-hidden relative">
                <motion.div
                  className="h-full bg-gradient-to-r from-[#48DDF5] via-[#448DFF] to-[#42F5A5] rounded-full shadow-[0_0_12px_rgba(72,221,245,0.5)]"
                  initial={{ width: 0 }}
                  animate={{ width: `${initState.progressPercent}%` }}
                  transition={{ ease: 'easeOut', duration: 0.3 }}
                />
              </div>

              {/* Simulated Failure Testing Control */}
              <div className="mt-3 flex items-center justify-between text-[11px] text-[#61758B]">
                <button
                  type="button"
                  onClick={() => setMockFailure(!mockFailure)}
                  className="hover:underline cursor-pointer"
                >
                  Simulate Error: <span className={mockFailure ? 'text-[#FF647C]' : 'text-[#91A4B8]'}>{mockFailure ? 'ON' : 'OFF'}</span>
                </button>
                <span>Demo Environment</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: 2-Column Feature Cards Preview Grid */}
        <div className="lg:col-span-4 flex flex-col">
          <div className="glass rounded-2xl p-5 border border-[rgba(148,180,210,0.16)] flex-1 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#91A4B8] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#42F5A5]" />
                Capability Architecture
              </span>
              <span className="text-[11px] text-[#61758B]">8 Core Modules</span>
            </div>

            {/* 2-Column Grid */}
            <div className="grid grid-cols-2 gap-2.5 my-auto">
              {FEATURE_CARDS.map((card, idx) => {
                const Icon = card.icon;
                return (
                  <motion.div
                    key={card.name}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + idx * 0.04 }}
                    className="p-3 rounded-xl bg-[rgba(11,18,32,0.7)] border border-[rgba(148,180,210,0.12)] hover:border-[rgba(72,221,245,0.3)] transition-all flex flex-col justify-between group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="w-7 h-7 rounded-lg bg-[rgba(72,221,245,0.1)] border border-[rgba(72,221,245,0.2)] flex items-center justify-center text-[#48DDF5] group-hover:scale-105 transition-transform">
                          <Icon className="w-4 h-4" />
                        </div>
                        <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-[rgba(148,180,210,0.08)] text-[#91A4B8]">
                          {card.tag}
                        </span>
                      </div>
                      <h4 className="text-xs font-semibold text-[#F1F5F9] mb-1">{card.name}</h4>
                      <p className="text-[10px] text-[#91A4B8] leading-relaxed line-clamp-2">
                        {card.desc}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            <div className="mt-3 pt-3 border-t border-[rgba(148,180,210,0.1)] flex items-center justify-between text-[11px] text-[#91A4B8]">
              <span>Hardware Acceleration</span>
              <span className="text-[#42F5A5]">WebGL / Canvas</span>
            </div>
          </div>
        </div>
      </main>

      {/* BOTTOM CONTROLS & STATUS BAR */}
      <footer className="relative z-10 pt-4 border-t border-[rgba(148,180,210,0.12)] flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Left: Auto-start preference toggle */}
        <div className="flex items-center gap-3">
          <Switch
            checked={initState.autoStartOnComplete}
            onChange={setAutoStart}
            label="Auto-start after initialization"
            description="Automatically switch to dashboard when initialization reaches 100%"
          />
        </div>

        {/* Right: Action Buttons */}
        <div className="flex items-center gap-3">
          {initState.status === 'initializing' && (
            <Button
              variant="secondary"
              size="sm"
              onClick={cancelInitialization}
              icon={<X className="w-4 h-4" />}
            >
              Cancel Initialization
            </Button>
          )}

          {initState.status === 'failed' && (
            <Button
              variant="primary"
              size="sm"
              onClick={retryInitialization}
              icon={<RotateCcw className="w-4 h-4" />}
            >
              Retry Initialization
            </Button>
          )}

          {initState.status === 'cancelled' && (
            <Button
              variant="primary"
              size="sm"
              onClick={retryInitialization}
              icon={<RotateCcw className="w-4 h-4" />}
            >
              Restart Initialization
            </Button>
          )}

          {/* Quick jump to dashboard for testing */}
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCurrentView('dashboard')}
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            {initState.status === 'completed' ? 'Enter Dashboard' : 'Skip to Dashboard'}
          </Button>
        </div>
      </footer>
    </div>
  );
};
