import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Camera,
  CameraOff,
  Activity,
  Zap,
  Sliders,
  RefreshCw,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  Radio,
  Video,
  AlertCircle,
  ChevronDown,
  Layers,
  Sparkles,
} from 'lucide-react';
import type { HandLandmarker, HandLandmarkerResult } from '@mediapipe/tasks-vision';
import { API_BASE_URL, BACKEND_SERVER_URL } from '../../services/api/client';
import { useAppStore } from '../../store/appStore';
import { useSettingsStore } from '../../store/settingsStore';
import { useGestureStore } from '../../store/gestureStore';
import { useMouseStore } from '../../store/mouseStore';
import { useCameraStore, getPersistentMediaStream } from '../../store/cameraStore';
import { classifyHandLandmarks } from '../../services/classifier/localGestureClassifier';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

// 21 standard MediaPipe Hand Landmark connections
const HAND_CONNECTIONS: [number, number][] = [
  // Thumb
  [0, 1], [1, 2], [2, 3], [3, 4],
  // Index
  [0, 5], [5, 6], [6, 7], [7, 8],
  // Middle
  [5, 9], [9, 10], [10, 11], [11, 12],
  // Ring
  [9, 13], [13, 14], [14, 15], [15, 16],
  // Pinky
  [13, 17], [17, 18], [18, 19], [19, 20],
  // Palm base
  [0, 17],
];

export interface CameraDeviceOption {
  deviceId: string;
  label: string;
  index: number;
}

interface DetectedHandInfo {
  label: string;
  confidence: number;
  isRight: boolean;
}

interface CameraSectionProps {
  className?: string;
}

export const CameraSection: React.FC<CameraSectionProps> = ({ className = '' }) => {
  const { setCurrentView } = useAppStore();
  const { settings, updateController } = useSettingsStore();

  // Persistent Camera & Tracking Lifecycle State (Phase 6A.2)
  const {
    isCameraActive,
    isStarting,
    streamSource,
    availableDevices,
    selectedDeviceId,
    backendCameraIndex,
    backendDevices,
    isMirrored,
    showOverlays,
    selectedResolution,
    cameraResolution,
    backendAvailable,
    cameraError,
    telemetry,
    detectedHandsCount,
    startWebcam,
    stopWebcam,
    setStreamSource,
    refreshDevices,
    syncOwnershipFromBackend,
    setIsMirrored,
    setShowOverlays,
    setSelectedDeviceId,
    setSelectedResolution,
    setBackendCameraIndex,
    setDetectedHandsCount,
    setTelemetry,
    setCameraError,
  } = useCameraStore();

  // Local UI-only State
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [measuredFps, setMeasuredFps] = useState<number>(30.0);
  const [detectedHandsInfo, setDetectedHandsInfo] = useState<DetectedHandInfo[]>([]);
  const [targetCoords, setTargetCoords] = useState<{ x: number; y: number } | null>(null);
  const [isModelLoading, setIsModelLoading] = useState<boolean>(false);
  const [modelReady, setModelReady] = useState<boolean>(false);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const landmarkerRef = useRef<HandLandmarker | null>(null);
  const lastDetectedResultRef = useRef<HandLandmarkerResult | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const lastVideoTimeRef = useRef<number>(-1);

  // High-performance non-blocking telemetry & queue refs
  const isDetectingRef = useRef<boolean>(false);
  const droppedFramesCountRef = useRef<number>(0);
  const inferenceTimesRef = useRef<number[]>([]);
  const inferenceFramesCountRef = useRef<number>(0);
  const cameraFramesCountRef = useRef<number>(0);
  const lastTelemetryTickRef = useRef<number>(performance.now());
  const latestHandCountRef = useRef<number>(0);
  const lastTimestampMsRef = useRef<number>(0);
  const lastInferenceTimeRef = useRef<number>(0);
  const lastDetectionTimeRef = useRef<number>(0);
  const videoFrameCallbackIdRef = useRef<number | null>(null);
  const lastCursorFeedRef = useRef<number>(0);
  const hasTriggeredIndexClickRef = useRef<boolean>(false);
  const lastIndexClickTimeRef = useRef<number>(0);
  const hasTriggeredVictoryClickRef = useRef<boolean>(false);
  const lastVictoryClickTimeRef = useRef<number>(0);

  // Initialize MediaPipe HandLandmarker in the browser using local wasm & model
  useEffect(() => {
    let isCancelled = false;

    const initLandmarker = async () => {
      try {
        setIsModelLoading(true);
        // Dynamically import @mediapipe/tasks-vision on-demand to prevent bundling
        // the heavy vision library into initial page chunks
        const { FilesetResolver, HandLandmarker } = await import('@mediapipe/tasks-vision');

        // Load vision tasks from local wasm directory (zero external network dependency)
        const vision = await FilesetResolver.forVisionTasks('/wasm');

        if (isCancelled) return;

        let landmarker: HandLandmarker;
        try {
          // Primary: Hardware-accelerated GPU delegate via WebGL2 shaders.
          // Executes inference in ~3-7ms without blocking the browser main thread,
          // delivering silky-smooth 60 FPS video playback and real-time hand tracking.
          landmarker = await HandLandmarker.createFromOptions(vision, {
            baseOptions: {
              modelAssetPath: '/models/hand_landmarker.task',
              delegate: 'GPU',
            },
            runningMode: 'VIDEO',
            numHands: 2,
            minHandDetectionConfidence: 0.5,
            minHandPresenceConfidence: 0.5,
            minTrackingConfidence: 0.5,
          });
        } catch (gpuErr) {
          console.warn('GPU delegate unavailable, falling back to CPU delegate:', gpuErr);
          // Fallback: CPU delegate with WebAssembly SIMD
          landmarker = await HandLandmarker.createFromOptions(vision, {
            baseOptions: {
              modelAssetPath: '/models/hand_landmarker.task',
              delegate: 'CPU',
            },
            runningMode: 'VIDEO',
            numHands: 2,
            minHandDetectionConfidence: 0.5,
            minHandPresenceConfidence: 0.5,
            minTrackingConfidence: 0.5,
          });
        }

        if (!isCancelled) {
          landmarkerRef.current = landmarker;
          setModelReady(true);
          setIsModelLoading(false);
        }
      } catch (err) {
        console.warn('MediaPipe browser model initialization note:', err);
        if (!isCancelled) {
          setIsModelLoading(false);
        }
      }
    };

    initLandmarker();

    return () => {
      isCancelled = true;
      if (landmarkerRef.current) {
        try {
          landmarkerRef.current.close();
        } catch {}
        landmarkerRef.current = null;
      }
    };
  }, []);

  // Persistent video binding callback ref: attaches active stream immediately upon DOM insertion
  const attachStreamToVideo = useCallback((video: HTMLVideoElement | null) => {
    videoRef.current = video;
    const stream = getPersistentMediaStream();
    if (video && stream && video.srcObject !== stream) {
      video.srcObject = stream;
      video.play().catch(() => {});
    }
  }, []);

  // Re-sync video element if stream or active state changes
  useEffect(() => {
    const video = videoRef.current;
    const stream = getPersistentMediaStream();
    if (isCameraActive && streamSource === 'webcam' && video && stream) {
      if (video.srcObject !== stream) {
        video.srcObject = stream;
      }
      video.play().catch(() => {});
    }
  }, [isCameraActive, streamSource]);

  // Initial device probe & backend ownership sync
  useEffect(() => {
    refreshDevices();
    syncOwnershipFromBackend();

    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
      const handleDeviceChange = () => {
        refreshDevices();
      };
      navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange);
      return () => {
        navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange);
      };
    }
  }, [refreshDevices, syncOwnershipFromBackend]);

  // SPA Tab Persistence: Component unmount cleanup cancels animation and callbacks
  // NOTE: Does NOT kill persistentMediaStream tracks so camera and tracking stay alive on tab navigation!
  useEffect(() => {
    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      if (videoRef.current && videoFrameCallbackIdRef.current !== null && 'cancelVideoFrameCallback' in videoRef.current) {
        (videoRef.current as any).cancelVideoFrameCallback(videoFrameCallbackIdRef.current);
        videoFrameCallbackIdRef.current = null;
      }
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
    };
  }, []);

  // Handle switching camera device
  const handleSelectCameraDevice = (newDeviceId: string) => {
    setSelectedDeviceId(newDeviceId);
    if (isCameraActive && streamSource === 'webcam') {
      startWebcam(newDeviceId, selectedResolution);
    }
  };

  // Handle switching resolution
  const handleSelectResolution = (newRes: '640x480' | '320x240' | '1280x720') => {
    setSelectedResolution(newRes);
    if (isCameraActive && streamSource === 'webcam') {
      startWebcam(selectedDeviceId, newRes);
    }
  };

  // Poll backend telemetry and live gesture recognition when streamSource is 'backend'
  useEffect(() => {
    if (!isCameraActive || streamSource !== 'backend') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/tracking/status`);
        if (res.ok) {
          const data = await res.json();
          setDetectedHandsCount(data.hands_detected || 0);
          setTelemetry({
            cameraFps: data.camera_fps || 30.0,
            inferenceFps: data.actual_inference_fps || 0.0,
            avgInferenceMs: data.avg_processing_time_ms || 0.0,
            endToEndLatencyMs: data.end_to_end_latency_ms || 0.0,
            droppedFrames: data.frames_dropped || 0,
            resolution: '640x480',
          });
        }

        const resResult = await fetch(`${API_BASE_URL}/tracking/result`);
        if (resResult.ok) {
          const resultData = await resResult.json();
          if (resultData.hands && resultData.hands.length > 0) {
            useAppStore.getState().setHandDetected(true);
            const primary = resultData.hands[0];
            if (primary.landmarks && primary.landmarks.length > 8) {
              const l8 = primary.landmarks[8];
              setTargetCoords({
                x: Math.round(l8.x * 640),
                y: Math.round(l8.y * 480),
              });
            }
            if (primary.gesture_name) {
              const allGestures = useGestureStore.getState().gestures;
              const match = allGestures.find(
                (g: any) =>
                  g.id === primary.gesture_id ||
                  g.name.toLowerCase() === primary.gesture_name.toLowerCase() ||
                  (g.id === 'fist' && primary.gesture_name.toLowerCase().includes('fist')) ||
                  (g.id === 'index_finger' && primary.gesture_name.toLowerCase().includes('point')) ||
                  (g.id === 'two_fingers' && (primary.gesture_name.toLowerCase().includes('victory') || primary.gesture_name.toLowerCase().includes('peace')))
              );
              useAppStore.getState().setDetectedGesture({
                gestureId: primary.gesture_id || (match ? match.id : 'detected'),
                name: primary.gesture_name,
                confidence: primary.gesture_confidence || 0.9,
                timestamp: Date.now(),
                action: match ? (match.action as any) : 'no_action',
              });
              useAppStore.getState().setRecognitionState('recognized');
            } else {
              useAppStore.getState().setDetectedGesture(null);
              useAppStore.getState().setRecognitionState('unknown');
            }
          } else {
            useAppStore.getState().setHandDetected(false);
            useAppStore.getState().setDetectedGesture(null);
            useAppStore.getState().setRecognitionState('no_hand');
          }
        }
      } catch {}
    }, 400);

    return () => clearInterval(interval);
  }, [isCameraActive, streamSource]);

  // Toggle Camera Button
  const handleToggleCamera = () => {
    if (isCameraActive) {
      stopWebcam();
      if (videoRef.current) {
        try {
          videoRef.current.srcObject = null;
        } catch {}
      }
    } else {
      startWebcam(selectedDeviceId, selectedResolution);
    }
  };

  // Anatomical & Confidence Validator: Rejects phantom detections on faces, backgrounds, or shadows
  const isValidHandDetection = (
    landmarks: { x: number; y: number; z?: number }[],
    handednessCategory?: { categoryName?: string; score?: number }
  ): boolean => {
    if (!landmarks || landmarks.length !== 21) return false;

    // Only reject if handedness/presence confidence score is explicitly present and too low (< 45%)
    if (handednessCategory && typeof handednessCategory.score === 'number' && handednessCategory.score < 0.45) {
      return false;
    }

    // Check wrist (0) and middle finger MCP (9) distance (palm length)
    // A real hand in normalized coordinates has a wrist-to-middle MCP distance between 0.03 and 0.70
    const wrist = landmarks[0];
    const middleMcp = landmarks[9];
    if (!wrist || !middleMcp) return false;
    const palmDist = Math.hypot(middleMcp.x - wrist.x, middleMcp.y - wrist.y);
    if (palmDist < 0.03 || palmDist > 0.70) return false;

    // Check bounding box dimensions
    let minX = 1;
    let maxX = 0;
    let minY = 1;
    let maxY = 0;
    for (let i = 0; i < landmarks.length; i++) {
      const p = landmarks[i];
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }
    const width = maxX - minX;
    const height = maxY - minY;

    // Real hand bounding box should have reasonable span
    if (width < 0.03 || height < 0.03 || width > 0.98 || height > 0.98) return false;

    return true;
  };

  // REAL MediaPipe Hand Detection & High-Performance Canvas Drawing Loop
  useEffect(() => {
    if (!isCameraActive || streamSource !== 'webcam') {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      if (videoRef.current && videoFrameCallbackIdRef.current !== null && 'cancelVideoFrameCallback' in videoRef.current) {
        (videoRef.current as any).cancelVideoFrameCallback(videoFrameCallbackIdRef.current);
        videoFrameCallbackIdRef.current = null;
      }
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
      lastDetectedResultRef.current = null;
      lastDetectionTimeRef.current = 0;
      setDetectedHandsCount(0);
      setDetectedHandsInfo([]);
      setTargetCoords(null);
      return;
    }

    let isRunning = true;

    // Real-time inference worker: executes when new camera frame is ready
    const runInference = () => {
      const video = videoRef.current;
      const landmarker = landmarkerRef.current;

      if (!video || !landmarker || isDetectingRef.current) {
        return;
      }

      if (video.paused && !video.ended) {
        video.play().catch(() => {});
      }

      if (video.readyState < 2 || video.ended || video.videoWidth === 0) {
        return;
      }

      const now = performance.now();
      // Throttle: ensure at least 16ms between inferences (~60 FPS max) to avoid redundant duplicate inferences
      if (now - lastInferenceTimeRef.current < 16) {
        return;
      }

      isDetectingRef.current = true;
      lastInferenceTimeRef.current = now;
      cameraFramesCountRef.current += 1;

      // Monotonic millisecond timestamp for MediaPipe Tasks detectForVideo
      const timestampMs = Math.max(now, (lastTimestampMsRef.current || 0) + 1);
      lastTimestampMsRef.current = timestampMs;

      try {
        const rawResult = landmarker.detectForVideo(video, timestampMs);
        const infDuration = performance.now() - now;
        inferenceTimesRef.current.push(infDuration);
        if (inferenceTimesRef.current.length > 30) inferenceTimesRef.current.shift();
        inferenceFramesCountRef.current += 1;

        if (rawResult && rawResult.landmarks && rawResult.landmarks.length > 0) {
          // Filter each detected hand by anatomical geometry and confidence
          const validIndices: number[] = [];
          for (let h = 0; h < rawResult.landmarks.length; h++) {
            const lms = rawResult.landmarks[h];
            const handCat = rawResult.handedness?.[h]?.[0] || (rawResult as any).handednesses?.[h]?.[0];
            if (isValidHandDetection(lms, handCat)) {
              validIndices.push(h);
            }
          }

          if (validIndices.length > 0) {
            lastDetectedResultRef.current = {
              ...rawResult,
              landmarks: validIndices.map((i) => rawResult.landmarks[i]),
              handedness: rawResult.handedness ? validIndices.map((i) => rawResult.handedness[i]) : [],
              handednesses: (rawResult as any).handednesses ? validIndices.map((i) => (rawResult as any).handednesses[i]) : [],
              worldLandmarks: rawResult.worldLandmarks ? validIndices.map((i) => rawResult.worldLandmarks[i]) : [],
            };
            lastDetectionTimeRef.current = performance.now();

            // Real-time gesture classification on active camera hand
            const primaryIdx = validIndices[0];
            const primaryLms = rawResult.landmarks[primaryIdx];
            const primaryHandCat = rawResult.handedness?.[primaryIdx]?.[0] || (rawResult as any).handednesses?.[primaryIdx]?.[0];
            const handSide = primaryHandCat?.categoryName || 'Right';
            const classification = classifyHandLandmarks(primaryLms, handSide);

            useAppStore.getState().setHandDetected(true);
            if (classification && classification.isRecognized) {
              useAppStore.getState().setDetectedGesture({
                gestureId: classification.gestureId,
                name: classification.name,
                confidence: classification.confidence,
                timestamp: Date.now(),
                action: classification.action,
              });
              useAppStore.getState().setRecognitionState('recognized');
            } else {
              useAppStore.getState().setDetectedGesture(null);
              useAppStore.getState().setRecognitionState('unknown');
            }

            // MOUSE CONTROL DISPATCH:
            // - Open Palm: Controls and moves the cursor
            // - Index Finger (Point) or Pinch: Triggers left click
            // - Victory Two Fingers or Middle Pinch: Triggers right click
            const mouseStatus = useMouseStore.getState().status;
            if (primaryLms && primaryLms.length > 9 && mouseStatus.enabled) {
              const thumbTip = primaryLms.length > 4 ? primaryLms[4] : undefined;
              const indexTip = primaryLms.length > 8 ? primaryLms[8] : undefined;
              const middleTip = primaryLms.length > 12 ? primaryLms[12] : undefined;

              const pinchDist = (thumbTip && indexTip)
                ? Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y)
                : undefined;
              const rightPinchDist = (thumbTip && middleTip)
                ? Math.hypot(thumbTip.x - middleTip.x, thumbTip.y - middleTip.y)
                : undefined;

              const isCursorMovingGesture = classification?.gestureId === 'open_palm' || classification?.action === 'move_cursor';

              if (isCursorMovingGesture) {
                const nowFeed = performance.now();
                if (nowFeed - lastCursorFeedRef.current >= 30) {
                  lastCursorFeedRef.current = nowFeed;
                  // Use middle MCP (landmark 9) at the center of the open palm for natural, steady steering
                  const palmPoint = primaryLms[9] || primaryLms[8];
                  const feedX = isMirrored ? (1.0 - palmPoint.x) : palmPoint.x;
                  const feedY = palmPoint.y;

                  const feedThumbX = thumbTip ? (isMirrored ? (1.0 - thumbTip.x) : thumbTip.x) : undefined;
                  const feedThumbY = thumbTip ? thumbTip.y : undefined;
                  const feedMiddleX = middleTip ? (isMirrored ? (1.0 - middleTip.x) : middleTip.x) : undefined;
                  const feedMiddleY = middleTip ? middleTip.y : undefined;

                  useMouseStore.getState().feedCursorPoint(
                    feedX,
                    feedY,
                    pinchDist,
                    feedThumbX,
                    feedThumbY,
                    rightPinchDist,
                    feedMiddleX,
                    feedMiddleY
                  );
                }
              }

              // Left Click trigger: Index Finger (Point) or Thumb+Index Pinch
              const isIndexClickGesture = classification?.gestureId === 'index_finger' || classification?.action === 'left_click';
              const isIndexPinch = pinchDist !== undefined && pinchDist <= (mouseStatus.pinch_activation_threshold || 0.05);
              const isIndexReleased = !isIndexClickGesture && (pinchDist === undefined || pinchDist >= (mouseStatus.pinch_release_threshold || 0.08));

              if (isIndexReleased) {
                hasTriggeredIndexClickRef.current = false;
              }

              if (isIndexClickGesture || isIndexPinch) {
                if (mouseStatus.left_click_enabled) {
                  const now = performance.now();
                  const cooldown = mouseStatus.click_cooldown_ms || 400;
                  if (!hasTriggeredIndexClickRef.current && (now - lastIndexClickTimeRef.current >= cooldown)) {
                    hasTriggeredIndexClickRef.current = true;
                    lastIndexClickTimeRef.current = now;
                    console.log(`[CLICK_DIAG] Frontend Left Click: ${isIndexClickGesture ? 'index_finger' : 'pinch'} (dist: ${pinchDist?.toFixed(3)})`);
                    useMouseStore.getState().triggerClick();
                  }
                }
              }

              // Right Click trigger: Two Fingers (Victory) or Thumb+Middle Pinch
              const isVictoryClickGesture = classification?.gestureId === 'two_fingers' || classification?.action === 'right_click';
              const isMiddlePinch = rightPinchDist !== undefined && rightPinchDist <= (mouseStatus.right_pinch_activation_threshold || 0.05);
              const isVictoryReleased = !isVictoryClickGesture && (rightPinchDist === undefined || rightPinchDist >= (mouseStatus.right_pinch_release_threshold || 0.08));

              if (isVictoryReleased) {
                hasTriggeredVictoryClickRef.current = false;
              }

              if (isVictoryClickGesture || isMiddlePinch) {
                if (mouseStatus.right_click_enabled) {
                  const now = performance.now();
                  const cooldown = mouseStatus.right_click_cooldown_ms || 500;
                  if (!hasTriggeredVictoryClickRef.current && (now - lastVictoryClickTimeRef.current >= cooldown)) {
                    hasTriggeredVictoryClickRef.current = true;
                    lastVictoryClickTimeRef.current = now;
                    console.log(`[CLICK_DIAG] Frontend Right Click: ${isVictoryClickGesture ? 'two_fingers' : 'middle_pinch'} (dist: ${rightPinchDist?.toFixed(3)})`);
                    useMouseStore.getState().triggerRightClick();
                  }
                }
              }
            }
          } else {
            // No anatomically valid hands: wipe detection immediately
            lastDetectedResultRef.current = null;
            hasTriggeredIndexClickRef.current = false;
            hasTriggeredVictoryClickRef.current = false;
            useAppStore.getState().setHandDetected(false);
            useAppStore.getState().setDetectedGesture(null);
            useAppStore.getState().setRecognitionState('no_hand');
          }
        } else {
          // Zero hands detected: wipe detection immediately
          lastDetectedResultRef.current = null;
          hasTriggeredIndexClickRef.current = false;
          hasTriggeredVictoryClickRef.current = false;
          useAppStore.getState().setHandDetected(false);
          useAppStore.getState().setDetectedGesture(null);
          useAppStore.getState().setRecognitionState('no_hand');
        }
      } catch {
        lastDetectedResultRef.current = null;
      } finally {
        isDetectingRef.current = false;
      }
    };

    // Hardware frame presentation synchronization using requestVideoFrameCallback
    const setupVideoFrameCallback = () => {
      const video = videoRef.current;
      if (video && 'requestVideoFrameCallback' in video) {
        const onFrame = () => {
          if (!isRunning) return;
          runInference();
          if (video && 'requestVideoFrameCallback' in video) {
            videoFrameCallbackIdRef.current = (video as any).requestVideoFrameCallback(onFrame);
          }
        };
        videoFrameCallbackIdRef.current = (video as any).requestVideoFrameCallback(onFrame);
      }
    };

    setupVideoFrameCallback();

    // Dedicated Web Worker background heartbeat:
    // Chromium pauses requestAnimationFrame and requestVideoFrameCallback when
    // a tab is in the background or the window is minimized. Dedicated Web Workers
    // run on an isolated OS thread and are NOT throttled to 1s.
    // NOTE: This worker is ONLY activated when the tab is hidden or minimized,
    // ensuring the main thread runs with zero message overhead when the camera is visible!
    let backgroundWorker: Worker | null = null;
    try {
      const workerScript = `
        let timer = null;
        self.onmessage = function(e) {
          if (e.data === 'start') {
            if (!timer) {
              timer = setInterval(function() {
                self.postMessage('tick');
              }, 30);
            }
          } else if (e.data === 'stop') {
            if (timer) {
              clearInterval(timer);
              timer = null;
            }
          }
        };
      `;
      const blob = new Blob([workerScript], { type: 'application/javascript' });
      const workerUrl = URL.createObjectURL(blob);
      backgroundWorker = new Worker(workerUrl);
      backgroundWorker.onmessage = () => {
        if (!isRunning) return;
        runInference();
      };
      // Only start worker if document is ALREADY hidden upon mount
      if (typeof document !== 'undefined' && document.hidden) {
        backgroundWorker.postMessage('start');
      }
    } catch (e) {
      console.warn('Background worker fallback:', e);
    }

    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Tab moved to background or minimized: activate Web Worker heartbeat
        if (backgroundWorker) {
          backgroundWorker.postMessage('start');
        }
      } else {
        // Tab returned to foreground: stop worker heartbeat so requestVideoFrameCallback handles frames cleanly without contention
        if (backgroundWorker) {
          backgroundWorker.postMessage('stop');
        }
        const video = videoRef.current;
        if (video && video.paused && !video.ended) {
          video.play().catch(() => {});
        }
      }
    };

    const handleWindowBlur = () => {
      // If user switches away from the window, start worker heartbeat
      if (backgroundWorker) {
        backgroundWorker.postMessage('start');
      }
    };

    const handleWindowFocus = () => {
      // If user focuses back on the tab and tab is visible, pause worker heartbeat
      if (!document.hidden && backgroundWorker) {
        backgroundWorker.postMessage('stop');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('focus', handleWindowFocus);

    // Render loop: draws landmarks onto canvas and refreshes telemetry
    const render = () => {
      if (!isRunning) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;

      // Fallback inference trigger if requestVideoFrameCallback is not available
      if (video && !('requestVideoFrameCallback' in video)) {
        runInference();
      }

      if (canvas && video && video.readyState >= 2 && video.videoWidth > 0) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
          }
          const width = canvas.width;
          const height = canvas.height;

          // Always clear canvas completely before each frame
          ctx.clearRect(0, 0, width, height);

          // Check stale detection timeout (150ms): if hand moved away or was lost, NEVER draw stale ghost hands!
          const now = performance.now();
          const isStale = (now - lastDetectionTimeRef.current) > 150;
          const results = isStale ? null : lastDetectedResultRef.current;

          if (results && results.landmarks && results.landmarks.length > 0) {
            latestHandCountRef.current = results.landmarks.length;

            for (let h = 0; h < results.landmarks.length; h++) {
              const landmarks = results.landmarks[h];
              const handednessCategory = results.handedness?.[h]?.[0] || (results as any).handednesses?.[h]?.[0];
              const isRight = handednessCategory?.categoryName === 'Right';

              // Neon Green for Right hand (#00FF66), Neon Blue for Left hand (#00B4FF)
              const jointColor = isRight ? '#00FF66' : '#00B4FF';
              const boneColor = isRight ? 'rgba(0, 255, 102, 0.85)' : 'rgba(0, 180, 255, 0.85)';

              // Draw skeleton bone connections between real hand joints
              ctx.lineWidth = 3;
              ctx.strokeStyle = boneColor;
              ctx.lineCap = 'round';
              ctx.lineJoin = 'round';

              for (const [i, j] of HAND_CONNECTIONS) {
                if (landmarks[i] && landmarks[j]) {
                  ctx.beginPath();
                  ctx.moveTo(landmarks[i].x * width, landmarks[i].y * height);
                  ctx.lineTo(landmarks[j].x * width, landmarks[j].y * height);
                  ctx.stroke();
                }
              }

              // Draw real 21 landmark joint nodes
              for (let i = 0; i < landmarks.length; i++) {
                const pt = landmarks[i];
                const px = pt.x * width;
                const py = pt.y * height;
                const isFingertip = [4, 8, 12, 16, 20].includes(i);
                const isIndexTip = i === 8;

                // Outer ring on index fingertip
                if (isIndexTip) {
                  ctx.beginPath();
                  ctx.arc(px, py, 10, 0, Math.PI * 2);
                  ctx.strokeStyle = jointColor;
                  ctx.lineWidth = 2;
                  ctx.stroke();
                }

                // Joint circular node
                ctx.beginPath();
                ctx.arc(px, py, isFingertip ? 5 : 3.5, 0, Math.PI * 2);
                ctx.fillStyle = jointColor;
                ctx.fill();

                // White core center dot
                ctx.beginPath();
                ctx.arc(px, py, isFingertip ? 2 : 1.5, 0, Math.PI * 2);
                ctx.fillStyle = '#FFFFFF';
                ctx.fill();
              }
            }
          } else {
            latestHandCountRef.current = 0;
          }
        }
      }

      // Synchronize telemetry & React state at controlled frequency (every 500ms, 2 Hz)
      const now = performance.now();
      const elapsed = now - lastTelemetryTickRef.current;
      if (elapsed >= 500) {
        const infFps = Number(((inferenceFramesCountRef.current * 1000) / elapsed).toFixed(1));
        const camFps = Number(((cameraFramesCountRef.current * 1000) / elapsed).toFixed(1));
        const avgInf = inferenceTimesRef.current.length > 0
          ? Number((inferenceTimesRef.current.reduce((a, b) => a + b, 0) / inferenceTimesRef.current.length).toFixed(1))
          : 0.0;
        const e2e = Number((avgInf + (camFps > 0 ? 1000 / camFps : 33.3)).toFixed(1));

        setMeasuredFps(camFps > 0 ? camFps : 30.0);
        setTelemetry({
          cameraFps: camFps,
          inferenceFps: infFps,
          avgInferenceMs: avgInf,
          endToEndLatencyMs: e2e,
          droppedFrames: droppedFramesCountRef.current,
          resolution: `${videoRef.current?.videoWidth || 640}x${videoRef.current?.videoHeight || 480}`,
        });

        // Batch update hand info and coords in React
        const isStale = (now - lastDetectionTimeRef.current) > 150;
        const results = isStale ? null : lastDetectedResultRef.current;
        if (results && results.landmarks && results.landmarks.length > 0) {
          setDetectedHandsCount(results.landmarks.length);
          const handsInfo: DetectedHandInfo[] = results.landmarks.map((_, h) => {
            const handednessCategory = results.handedness?.[h]?.[0] || (results as any).handednesses?.[h]?.[0];
            const isRight = handednessCategory?.categoryName === 'Right';
            const confidence = handednessCategory?.score ? Math.round(handednessCategory.score * 100) : 95;
            return {
              label: `${isRight ? 'Right' : 'Left'} (${confidence}%)`,
              confidence,
              isRight,
            };
          });
          setDetectedHandsInfo(handsInfo);

          const p = results.landmarks[0]?.[8];
          if (p) {
            setTargetCoords({ x: Number(p.x.toFixed(3)), y: Number(p.y.toFixed(3)) });
          }
        } else {
          setDetectedHandsCount(0);
          setDetectedHandsInfo([]);
          setTargetCoords(null);
        }

        inferenceFramesCountRef.current = 0;
        cameraFramesCountRef.current = 0;
        lastTelemetryTickRef.current = now;
      }

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    animFrameIdRef.current = requestAnimationFrame(render);

    return () => {
      isRunning = false;
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      window.removeEventListener('focus', handleWindowFocus);
      if (backgroundWorker) {
        backgroundWorker.postMessage('stop');
        backgroundWorker.terminate();
        backgroundWorker = null;
      }
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      if (videoRef.current && videoFrameCallbackIdRef.current !== null && 'cancelVideoFrameCallback' in videoRef.current) {
        (videoRef.current as any).cancelVideoFrameCallback(videoFrameCallbackIdRef.current);
        videoFrameCallbackIdRef.current = null;
      }
    };
  }, [isCameraActive, streamSource, showOverlays]);

  // Fullscreen toggle
  const handleToggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const activeDeviceLabel =
    availableDevices.find((d) => d.deviceId === selectedDeviceId)?.label ||
    (availableDevices.length > 0 ? `Camera 1` : 'Default Camera');

  return (
    <Card
      variant="glass-strong"
      className={`relative overflow-hidden flex flex-col ${className}`}
    >
      <div ref={containerRef} className="flex flex-col h-full">
        {/* Top Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-[rgba(148,180,210,0.14)] bg-[rgba(11,18,32,0.7)] backdrop-blur-md">
          {/* Left Title & Status */}
          <div className="flex items-center gap-3">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isCameraActive ? 'bg-[#42F5A5] animate-ping' : 'bg-[#FF647C]'
              }`}
            />
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                Camera Feed
              </span>
              <Badge variant={isCameraActive ? 'green' : 'warning'} dot>
                {isCameraActive
                  ? streamSource === 'backend'
                    ? `Python Engine (#${backendCameraIndex})`
                    : activeDeviceLabel
                  : 'Disconnected'}
              </Badge>
              {modelReady && (
                <Badge variant="cyan" className="hidden sm:inline-flex text-[10px]">
                  <Sparkles className="w-2.5 h-2.5 mr-1" />
                  AI Ready
                </Badge>
              )}
            </div>
          </div>

          {/* Right Controls Bar */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Camera Device Selector Dropdown */}
            {streamSource === 'webcam' ? (
              <div className="relative flex items-center">
                <Camera className="w-3.5 h-3.5 text-[#48DDF5] absolute left-2.5 pointer-events-none" />
                <select
                  value={selectedDeviceId}
                  onChange={(e) => handleSelectCameraDevice(e.target.value)}
                  className="pl-8 pr-7 py-1 rounded-lg bg-[rgba(11,18,32,0.9)] border border-[rgba(148,180,210,0.25)] text-xs text-white appearance-none cursor-pointer hover:border-[#48DDF5] transition-colors focus:outline-none focus:border-[#42F5A5] max-w-[180px] truncate"
                  title="Choose Camera Device"
                >
                  {availableDevices.length > 0 ? (
                    availableDevices.map((device, idx) => (
                      <option key={device.deviceId || idx} value={device.deviceId} className="bg-[#0B1220] text-white">
                        {device.label || `Camera ${idx + 1}`}
                      </option>
                    ))
                  ) : (
                    <option value="" className="bg-[#0B1220] text-white">
                      Default Webcam
                    </option>
                  )}
                </select>
                <ChevronDown className="w-3 h-3 text-[#91A4B8] absolute right-2 pointer-events-none" />
              </div>
            ) : (
              /* Backend Camera Index Selector */
              <div className="relative flex items-center">
                <Layers className="w-3.5 h-3.5 text-[#48DDF5] absolute left-2.5 pointer-events-none" />
                <select
                  value={backendCameraIndex}
                  onChange={(e) => setBackendCameraIndex(Number(e.target.value))}
                  className="pl-8 pr-7 py-1 rounded-lg bg-[rgba(11,18,32,0.9)] border border-[rgba(148,180,210,0.25)] text-xs text-white appearance-none cursor-pointer hover:border-[#48DDF5] transition-colors focus:outline-none focus:border-[#42F5A5]"
                  title="Backend Camera Index"
                >
                  {backendDevices.length > 0 ? (
                    backendDevices.map((d) => (
                      <option key={d.index} value={d.index} className="bg-[#0B1220] text-white">
                        {d.name}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value={0} className="bg-[#0B1220] text-white">Camera 0 (Name unavailable)</option>
                      <option value={1} className="bg-[#0B1220] text-white">Camera 1 (Name unavailable)</option>
                    </>
                  )}
                </select>
                <ChevronDown className="w-3 h-3 text-[#91A4B8] absolute right-2 pointer-events-none" />
              </div>
            )}

            {/* Resolution Selector Dropdown (Default: 640x480) */}
            {streamSource === 'webcam' && (
              <div className="relative flex items-center">
                <Sliders className="w-3.5 h-3.5 text-[#42F5A5] absolute left-2.5 pointer-events-none" />
                <select
                  value={selectedResolution}
                  onChange={(e) => handleSelectResolution(e.target.value as '640x480' | '320x240' | '1280x720')}
                  className="pl-8 pr-7 py-1 rounded-lg bg-[rgba(11,18,32,0.9)] border border-[rgba(148,180,210,0.25)] text-xs text-white appearance-none cursor-pointer hover:border-[#42F5A5] transition-colors focus:outline-none focus:border-[#42F5A5]"
                  title="Capture Resolution (Default: 640x480)"
                >
                  <option value="640x480" className="bg-[#0B1220] text-white">640x480 (Default)</option>
                  <option value="320x240" className="bg-[#0B1220] text-white">320x240 (Fast)</option>
                  <option value="1280x720" className="bg-[#0B1220] text-white">1280x720 (HD)</option>
                </select>
                <ChevronDown className="w-3 h-3 text-[#91A4B8] absolute right-2 pointer-events-none" />
              </div>
            )}

            {/* FPS Indicator */}
            {isCameraActive && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[rgba(18,29,45,0.8)] border border-[rgba(72,221,245,0.2)] text-xs font-mono text-[#48DDF5]">
                <Activity className="w-3.5 h-3.5 text-[#42F5A5] animate-pulse" />
                <span>{measuredFps.toFixed(1)} FPS</span>
              </div>
            )}

            {/* Stream Mode Switcher */}
            <div className="flex items-center p-0.5 rounded-lg bg-[rgba(11,18,32,0.8)] border border-[rgba(148,180,210,0.15)] text-[11px]">
              <button
                type="button"
                onClick={async () => {
                  if (streamSource === 'backend') {
                    useCameraStore.setState({ isStarting: true });
                    try {
                      await fetch(`${API_BASE_URL}/tracking/stop`, { method: 'POST' });
                      await fetch(`${API_BASE_URL}/camera/stop`, { method: 'POST' });
                    } catch {}
                  }
                  await setStreamSource('webcam');
                  if (!isCameraActive) startWebcam(selectedDeviceId);
                }}
                className={`px-2.5 py-1 rounded-md transition-all cursor-pointer font-medium flex items-center gap-1.5 ${
                  streamSource === 'webcam'
                    ? 'bg-gradient-to-r from-[#48DDF5] to-[#42F5A5] text-[#070B12] font-semibold shadow-sm'
                    : 'text-[#91A4B8] hover:text-white'
                }`}
                title="Direct Browser Webcam"
              >
                <Video className="w-3 h-3" />
                Webcam
              </button>
              <button
                type="button"
                onClick={async () => {
                  if (streamSource === 'webcam') {
                    stopWebcam();
                  }
                  useCameraStore.setState({ isStarting: true, streamSource: 'backend' });
                  try {
                    await fetch(`${API_BASE_URL}/camera/claim`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ owner: 'backend' }),
                    });
                    await fetch(`${API_BASE_URL}/camera/start`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ camera_index: backendCameraIndex }),
                    });
                    await fetch(`${API_BASE_URL}/tracking/start`, {
                      method: 'POST',
                    });
                    useCameraStore.setState({ isCameraActive: true });
                  } catch (err: any) {
                    setCameraError(`Python engine not reachable: ${err.message || 'Check server connection'}`);
                  } finally {
                    useCameraStore.setState({ isStarting: false });
                  }
                }}
                className={`px-2.5 py-1 rounded-md transition-all cursor-pointer font-medium flex items-center gap-1.5 ${
                  streamSource === 'backend'
                    ? 'bg-gradient-to-r from-[#48DDF5] to-[#42F5A5] text-[#070B12] font-semibold shadow-sm'
                    : 'text-[#91A4B8] hover:text-white'
                }`}
                title="Python FastAPI MediaPipe Stream"
              >
                <Radio className="w-3 h-3" />
                Python Engine
                {backendAvailable && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#42F5A5]" />
                )}
              </button>
            </div>

            {/* Overlay Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowOverlays(!showOverlays)}
              icon={showOverlays ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              title={showOverlays ? 'Hide Landmarks & HUD' : 'Show Landmarks & HUD'}
              className="p-2"
            />

            {/* Mirror Toggle */}
            {streamSource === 'webcam' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsMirrored(!isMirrored)}
                icon={<RefreshCw className="w-3.5 h-3.5" />}
                title={isMirrored ? 'Disable Mirroring' : 'Enable Mirroring'}
                className={`p-2 ${isMirrored ? 'text-[#48DDF5] border-[#48DDF5]/40' : ''}`}
              />
            )}

            {/* Camera Power Toggle */}
            <Button
              variant={isCameraActive ? 'danger' : 'primary'}
              size="sm"
              onClick={handleToggleCamera}
              icon={isCameraActive ? <CameraOff className="w-3.5 h-3.5" /> : <Camera className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              {isCameraActive ? 'Turn Off' : isStarting ? 'Starting...' : 'Start Camera'}
            </Button>

            {/* Fullscreen Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggleFullscreen}
              icon={isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
              className="p-2"
            />
          </div>
        </div>

        {/* Real-time Performance Telemetry Dashboard Bar (Requirement 7) */}
        {isCameraActive && (
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2 px-4 py-2 bg-[rgba(7,11,18,0.92)] border-b border-[rgba(148,180,210,0.12)] text-xs font-mono">
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">Camera FPS</span>
              <span className="font-bold text-[#48DDF5]">{telemetry.cameraFps.toFixed(1)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">Inference FPS</span>
              <span className="font-bold text-[#42F5A5]">{telemetry.inferenceFps.toFixed(1)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">Avg Inference</span>
              <span className="font-bold text-[#FFEA00]">{telemetry.avgInferenceMs.toFixed(1)} ms</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">E2E Latency</span>
              <span className="font-bold text-[#A78BFA]">{telemetry.endToEndLatencyMs.toFixed(1)} ms</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">Dropped Frames</span>
              <span className={`font-bold ${telemetry.droppedFrames > 0 ? 'text-[#FFB347]' : 'text-[#42F5A5]'}`}>
                {telemetry.droppedFrames}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">Resolution</span>
              <span className="font-bold text-white">{telemetry.resolution}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-[#91A4B8] uppercase">Hands Detected</span>
              <span className={`font-bold ${detectedHandsCount > 0 ? 'text-[#42F5A5]' : 'text-[#61758B]'}`}>
                {detectedHandsCount} {detectedHandsCount === 1 ? 'Hand' : 'Hands'}
              </span>
            </div>
          </div>
        )}

        {/* Central Camera Video Viewport */}
        <div className="relative flex-1 min-h-[460px] max-h-[580px] w-full bg-[#05080E] flex items-center justify-center overflow-hidden">
          {/* Active Camera Viewport */}
          {isCameraActive ? (
            <div className="relative w-full h-full flex items-center justify-center">
              {streamSource === 'webcam' ? (
                <>
                  <video
                    ref={attachStreamToVideo}
                    playsInline
                    autoPlay
                    muted
                    onLoadedMetadata={(e) => {
                      const v = e.currentTarget;
                      v.play().catch(() => {});
                      if (v.videoWidth && v.videoHeight) {
                        useCameraStore.setState({
                          cameraResolution: { width: v.videoWidth, height: v.videoHeight },
                        });
                      }
                    }}
                    onCanPlay={(e) => {
                      e.currentTarget.play().catch(() => {});
                    }}
                    className={`w-full h-full object-cover transition-transform duration-200 ${
                      isMirrored ? 'scale-x-[-1]' : ''
                    }`}
                  />

                  {/* Clean Canvas: Only renders real detected hand landmarks */}
                  {showOverlays && (
                    <canvas
                      ref={canvasRef}
                      className={`absolute inset-0 w-full h-full pointer-events-none object-cover ${
                        isMirrored ? 'scale-x-[-1]' : ''
                      }`}
                    />
                  )}
                </>
              ) : (
                /* Python Backend MJPEG Stream with camera_index parameter */
                <div className="relative w-full h-full flex items-center justify-center bg-black">
                  <img
                    src={`${API_BASE_URL}/tracking/stream?camera_index=${backendCameraIndex}`}
                    alt="Python MediaPipe Tracking Stream"
                    className="w-full h-full object-contain"
                    onError={() => {
                      setCameraError(
                        `Python backend stream not reachable at ${BACKEND_SERVER_URL}. Switch to "Webcam" mode above to use your browser webcam directly.`
                      );
                    }}
                  />
                </div>
              )}

              {/* Single Unified Clean HUD Overlay (Cyan & White, zero yellow/duplicate text) */}
              {showOverlays && (
                <div className="absolute top-4 left-4 bg-[rgba(11,18,32,0.85)] border border-[rgba(72,221,245,0.25)] rounded-xl p-3.5 backdrop-blur-md shadow-2xl pointer-events-none font-mono text-xs z-20 flex flex-col gap-1 min-w-[220px]">
                  <div className="text-[#48DDF5] font-bold flex items-center justify-between">
                    <span>Camera</span>
                    <span className="text-white font-normal">{telemetry.resolution} @ {telemetry.cameraFps.toFixed(0)}fps</span>
                  </div>
                  <div className="text-[#48DDF5] font-bold flex items-center justify-between">
                    <span>Inference</span>
                    <span className="text-white font-normal">{telemetry.avgInferenceMs.toFixed(1)}ms ({telemetry.inferenceFps.toFixed(1)} FPS)</span>
                  </div>
                  <div className="text-[#91A4B8] text-[11px] flex items-center justify-between">
                    <span>Latency</span>
                    <span className="text-white">{telemetry.endToEndLatencyMs.toFixed(1)}ms</span>
                  </div>
                  <div className="text-[#48DDF5] font-bold flex items-center justify-between border-t border-[rgba(72,221,245,0.15)] pt-1 mt-0.5">
                    <span>Hands Detected</span>
                    <span className={detectedHandsCount > 0 ? 'text-[#48DDF5]' : 'text-[#91A4B8]'}>
                      {detectedHandsCount > 0 ? `${detectedHandsCount} Active` : 'Searching...'}
                    </span>
                  </div>

                  {targetCoords && detectedHandsCount > 0 && (
                    <div className="text-[11px] text-[#91A4B8] flex items-center justify-between">
                      <span>Index Tip (L8)</span>
                      <span className="text-white font-semibold">X: {targetCoords.x} | Y: {targetCoords.y}</span>
                    </div>
                  )}

                  {detectedHandsInfo.map((hand, idx) => (
                    <div
                      key={`hand-${idx}`}
                      className="font-medium text-[11px] text-[#FFFFFF] mt-0.5 flex items-center justify-between"
                    >
                      <span>Hand {idx + 1} ({hand.label})</span>
                      <span className="text-[#48DDF5]">{hand.confidence}%</span>
                    </div>
                  ))}
                  {detectedHandsCount === 0 && (
                    <div className="text-[#91A4B8] text-[10px] mt-0.5 italic">
                      Hold hand in view to track
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            /* Camera Standby View with Device Selection */
            <div className="flex flex-col items-center justify-center p-8 text-center max-w-lg">
              <div className="p-4 rounded-2xl bg-[rgba(18,29,45,0.7)] border border-[rgba(148,180,210,0.18)] mb-4 text-[#91A4B8]">
                <Camera className="w-10 h-10 text-[#48DDF5] opacity-80" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">Webcam Feed Paused</h3>
              <p className="text-xs text-[#91A4B8] leading-relaxed mb-5">
                Select your camera device below and click Start to begin live hand tracking with MediaPipe AI:
              </p>

              {/* Camera Picker In Standby View */}
              {availableDevices.length > 0 && (
                <div className="w-full max-w-xs mb-3 flex flex-col gap-1.5 text-left">
                  <label className="text-[11px] font-mono text-[#91A4B8] flex items-center justify-between">
                    <span>Choose Camera ({availableDevices.length} available):</span>
                    <button
                      type="button"
                      onClick={refreshDevices}
                      className="text-[#48DDF5] hover:underline cursor-pointer"
                    >
                      Refresh
                    </button>
                  </label>
                  <div className="relative flex items-center">
                    <Camera className="w-3.5 h-3.5 text-[#48DDF5] absolute left-3 pointer-events-none" />
                    <select
                      value={selectedDeviceId}
                      onChange={(e) => setSelectedDeviceId(e.target.value)}
                      className="w-full pl-9 pr-8 py-2 rounded-xl bg-[rgba(18,29,45,0.9)] border border-[rgba(148,180,210,0.3)] text-xs text-white appearance-none cursor-pointer hover:border-[#48DDF5] transition-colors focus:outline-none focus:border-[#42F5A5]"
                    >
                      {availableDevices.map((device, idx) => (
                        <option key={device.deviceId || idx} value={device.deviceId} className="bg-[#0B1220] text-white">
                          {device.label || `Camera ${idx + 1}`}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="w-3.5 h-3.5 text-[#91A4B8] absolute right-3 pointer-events-none" />
                  </div>
                </div>
              )}

              {/* Resolution Picker in Standby View (Default 640x480) */}
              <div className="w-full max-w-xs mb-5 flex flex-col gap-1.5 text-left">
                <label className="text-[11px] font-mono text-[#91A4B8]">
                  Resolution:
                </label>
                <div className="relative flex items-center">
                  <Sliders className="w-3.5 h-3.5 text-[#42F5A5] absolute left-3 pointer-events-none" />
                  <select
                    value={selectedResolution}
                    onChange={(e) => setSelectedResolution(e.target.value as '640x480' | '320x240' | '1280x720')}
                    className="w-full pl-9 pr-8 py-2 rounded-xl bg-[rgba(18,29,45,0.9)] border border-[rgba(148,180,210,0.3)] text-xs text-white appearance-none cursor-pointer hover:border-[#42F5A5] transition-colors focus:outline-none focus:border-[#42F5A5]"
                  >
                    <option value="640x480" className="bg-[#0B1220] text-white">640x480 (Default - Balanced)</option>
                    <option value="320x240" className="bg-[#0B1220] text-white">320x240 (Ultra Fast)</option>
                    <option value="1280x720" className="bg-[#0B1220] text-white">1280x720 (HD - High Accuracy)</option>
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-[#91A4B8] absolute right-3 pointer-events-none" />
                </div>
              </div>

              {/* Start Button */}
              <Button
                variant="primary"
                size="md"
                onClick={() => startWebcam(selectedDeviceId)}
                icon={<Camera className="w-4 h-4" />}
                disabled={isStarting}
              >
                {isStarting ? 'Connecting to Camera...' : 'Start Live Camera'}
              </Button>
            </div>
          )}

          {/* Error Banner with Camera Switcher */}
          {cameraError && (
            <div className="absolute bottom-4 left-4 right-4 p-3 rounded-xl bg-[rgba(255,100,124,0.2)] border border-[rgba(255,100,124,0.4)] text-[#FF647C] text-xs flex flex-col sm:flex-row items-center justify-between gap-3 backdrop-blur-md z-30">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{cameraError}</span>
              </div>
              <div className="flex items-center gap-2">
                {availableDevices.length > 1 && (
                  <button
                    type="button"
                    onClick={() => {
                      const currentIdx = availableDevices.findIndex((d) => d.deviceId === selectedDeviceId);
                      const nextDevice = availableDevices[(currentIdx + 1) % availableDevices.length];
                      if (nextDevice) {
                        setSelectedDeviceId(nextDevice.deviceId);
                        startWebcam(nextDevice.deviceId);
                      }
                    }}
                    className="px-2.5 py-1 rounded bg-[rgba(255,255,255,0.15)] text-white text-xs hover:bg-[rgba(255,255,255,0.25)] transition-colors cursor-pointer"
                  >
                    Try Another Camera
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setCameraError(null)}
                  className="text-[11px] underline cursor-pointer text-white"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Bar: Air Controller Actions & Status */}
        <div className="p-4 border-t border-[rgba(148,180,210,0.14)] bg-[rgba(11,18,32,0.6)] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button
              variant={settings.controller.enabled ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => updateController({ enabled: !settings.controller.enabled })}
              icon={<Zap className="w-4 h-4" />}
            >
              {settings.controller.enabled ? 'Disable Air Controller' : 'Enable Air Controller'}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCurrentView('live-control')}
              icon={<Sliders className="w-4 h-4" />}
            >
              Tune Sensitivity
            </Button>
          </div>

          <p className="text-[11px] text-[#91A4B8]">
            {isCameraActive
              ? settings.controller.enabled
                ? 'Air Controller actively processing live hand gestures.'
                : 'Camera streaming live feed. Air Controller in standby.'
              : 'Camera offline. Choose your camera and click "Start Live Camera" to begin.'}
          </p>
        </div>
      </div>
    </Card>
  );
};
