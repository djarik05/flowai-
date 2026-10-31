# Project Architecture

**Project:** GestureFlow AI  
**Date:** October 30, 2026

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GESTUREFLOW AI ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    HTTP/WS     ┌──────────────────────────────────────┐  │
│  │   FRONTEND   │ ◄─────────────► │           BACKEND (FastAPI)           │  │
│  │  (React 19)  │                 │            (Python 3.12)              │  │
│  └──────────────┘                 └──────────────────────────────────────┘  │
│        ▲                                    ▲                                 │
│        │                                    │                                 │
│        │ WebRTC/HTTP                       │ MJPEG/HTTP                        │
│        │                                    │                                 │
│  ┌─────┴─────┐                     ┌───────┴────────┐                        │
│  │  BROWSER  │                     │  PYTHON PROCESS │                        │
│  │  MEDIAPIPE│                     │  MEDIAPIPE TASKS│                        │
│  │   (WASM)  │                     │    (CPU/GPU)    │                        │
│  └───────────┘                     └────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND (React 19)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        App.tsx / AppLayout.tsx                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│         ┌──────────────────────────┼──────────────────────────┐              │
│         ▼                          ▼                          ▼              │
│  ┌───────────────┐         ┌───────────────┐         ┌───────────────┐     │
│  │  Dashboard    │         │ GestureManager│         │ LiveControl   │     │
│  │  View         │         │ View (5 tabs) │         │ View          │     │
│  └───────────────┘         └───────────────┘         └───────────────┘     │
│                                    │                                          │
│                    ┌───────────────┼───────────────┐                         │
│                    ▼               ▼               ▼                         │
│           ┌─────────────────┐ ┌───────────┐ ┌───────────────┐               │
│           │ CollectionStudio│ │ Dataset   │ │ ModelTraining │               │
│           │ Tab             │ │ Overview  │ │ View          │               │
│           └─────────────────┘ └───────────┘ └───────────────┘               │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                         │
│                    ▼               ▼               ▼                         │
│           ┌─────────────────────────────────────────────────────┐           │
│           │                  CameraSection.tsx                   │           │
│           │  ┌──────────────┐ ┌──────────────┐ ┌────────────┐   │           │
│           │  │ Browser WASM │ │ Backend MJPEG│ │ Overlays/  │   │           │
│           │  │ HandLandmarker│ │ Stream       │ │ Telemetry  │   │           │
│           │  └──────────────┘ └──────────────┘ └────────────┘   │           │
│           └─────────────────────────────────────────────────────┘           │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼              │
│  ┌───────────────┐         ┌───────────────┐         ┌───────────────┐     │
│  │ Zustand Stores│         │ API Clients   │         │ Local Classifier│    │
│  │ (7 stores)    │         │ (typed fetch) │         │ (optional)     │     │
│  └───────────────┘         └───────────────┘         └───────────────┘     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST + WebSocket
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                                BACKEND (FastAPI)                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         app/main.py (FastAPI)                           │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│         ┌──────────────────────────┼──────────────────────────┐              │
│         ▼                          ▼                          ▼              │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐        │
│  │ Core        │           │ Services    │           │ API Routes  │        │
│  │ (config,    │           │ (14 services)           │ (9 routers) │        │
│  │  logging,   │           │                         │             │        │
│  │  lifecycle) │           │                         │             │        │
│  └─────────────┘           └─────────────┘           └─────────────┘        │
│                                    │                                          │
│         ┌──────────────────────────┼──────────────────────────┐              │
│         ▼                          ▼                          ▼              │
│  ┌──────────────────┐      ┌─────────────────┐      ┌──────────────────┐   │
│  │ CameraManager    │      │ HandTrackingSvc │      │ ClassifierSvc    │   │
│  │ - Frame capture  │      │ - MediaPipe     │      │ - MLP Inference  │   │
│  │ - Thread pool    │      │ - VIDEO mode    │      │ - Model hot-reload│   │
│  │ - Frame queue    │      │ - Landmarks     │      │ - Thresholding   │   │
│  └──────────────────┘      └─────────────────┘      └──────────────────┘   │
│                                    │                                          │
│                    ┌───────────────┼───────────────┐                         │
│                    ▼               ▼               ▼                         │
│           ┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐         │
│           │ DatasetService  │ │ GestureService │ │ TemporalEngine  │        │
│           │ - JSON storage  │ │ - Registry     │ │ - TemporalBuffer│         │
│           │ - Atomic writes │ │ - CRUD         │ │ - MovementTracker│        │
│           │ - Validation    │ │ - Default 7    │ │ - StateMachine  │        │
│           │ - Export CSV/JSON             │     │ - Rule Matcher  │        │
│           └─────────────────┘ └───────────────┘ └─────────────────┘         │
│                                    │                                        │
│                                    ▼                                        │
│                    ┌─────────────────────────────────────┐                  │
│                    │         Persistence Layer            │                  │
│                    │  backend/datasets/                   │                  │
│                    │  ├─ samples/{gesture_id}/*.json     │                  │
│                    │  ├─ gestures/gesture_registry.json  │                  │
│                    │  ├─ exports/*.csv, *.json           │                  │
│                    │  ├─ models/classifiers/registry.json│                  │
│                    │  └─ models/classifiers/*/weights.npz│                  │
│                    └─────────────────────────────────────┘                  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Camera Frame Pipeline (Backend)

```
Webcam Hardware
      │
      ▼
cv2.VideoCapture (CameraManager._capture_loop)
      │
      ▼ 640x480@30fps BGR frames
Thread-safe frame queue (latest-frame-wins)
      │
      ▼ wait_for_frame()
HandTrackingService._tracking_loop
      │
      ▼ cv2.cvtColor(BGR→RGB) + mp.Image
MediaPipe HandLandmarker.detect_for_video()
      │
      ▼ 21 landmarks × N hands
Landmark extraction + normalization
      │
      ▼
┌──────────────────────────────────────┐
│ ClassifierService.predict_landmarks() │
│   FeaturePreprocessor.transform()     │
│   MLPClassifierModel.predict_proba()  │
└──────────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────────┐
│ TemporalEngine.process_hand()         │
│   TemporalFrameBuffer.append()        │
│   MovementTracker.extract_features()  │
│   GestureStateMachine.update()        │
│   GestureRuleMatcher.evaluate()       │
└──────────────────────────────────────┘
      │
      ▼ TrackingResult (landmarks + gestures + temporal events)
      │
      ▼ annotate_frame() → MJPEG stream
      ▼ Latest result cache (thread-safe)
```

### Dataset Collection Pipeline

```
User clicks "Start Collection"
      │
      ▼ POST /api/v1/collection/start
DatasetCollector.start_collection()
      │
      ▼ Creates session_id, starts tracking
      ▼
Background thread: _run_collection()
      │
      ▼ wait_for_next_result() (monotonic seq)
      ▼
Hand detected? ──No──► Continue
      │Yes
      ▼
Validate 21 landmarks, finite coords
      │
      ▼ Valid ──No──► Continue
      │Yes
      ▼
Rate limit (sample_interval_ms)
      │
      ▼ Ready ──No──► Continue
      │Yes
      ▼
Create DatasetSample (21 LandmarkCoord)
      │
      ▼ DatasetService.save_sample() (atomic .tmp → os.replace)
      ▼
collected_samples += 1
      │
      ▼ Target reached? ──No──► Loop
      │Yes
      ▼
Status = "completed"
```

---

## Threading Model

```
Main Process (FastAPI)
│
├── Main Thread (FastAPI event loop)
│   ├── HTTP request handling
│   ├── API route handlers
│   └── Lifespan management
│
├── Camera Capture Thread (CameraManager._capture_loop)
│   ├── cv2.VideoCapture.read()
│   ├── Frame mirroring (if enabled)
│   ├── Frame queue (latest-frame-wins)
│   └── Frame ready event signal
│
├── Hand Tracking Thread (HandTrackingService._tracking_loop)
│   ├── wait_for_frame() from CameraManager
│   ├── MediaPipe detect_for_video()
│   ├── Landmark extraction
│   ├── ClassifierService hook
│   ├── TemporalEngine hook
│   ├── Frame annotation (OpenCV)
│   └── Result cache update + signal
│
├── Collection Thread (DatasetCollector._run_collection)
│   ├── wait_for_next_result() from HandTracking
│   ├── Landmark validation
│   ├── Rate limiting
│   └── DatasetService.save_sample()
│
├── Training Thread (TrainingEngine._run_training_job)
│   ├── Data loading + feature extraction
│   ├── Session-aware train/val/test split
│   ├── Epoch loop (forward + backward + Adam)
│   ├── Validation evaluation
│   ├── Test set evaluation
│   └── Model serialization + registry
│
└── Temporal Collection Thread (TemporalDatasetService)
    ├── Frame recording (landmarks + timestamp)
    ├── Sequence commit (validation + save)
    └── Sequence stop
```

---

## State Management

### Backend (Python)

| Component | State | Persistence |
|-----------|-------|-------------|
| CameraManager | `_status` (CameraStatus), `_latest_frame`, `_frame_seq` | In-memory |
| HandTrackingService | `_status`, `_latest_result`, `_latest_annotated_frame`, `_result_seq` | In-memory |
| ApplicationService | `_backend_state`, `_components` dict | In-memory |
| DatasetCollector | `_status`, `_session_id`, `_collected_samples` | In-memory |
| TemporalEngine | Hand states, buffers, event ring buffer | In-memory |
| ClassifierService | `_active_model`, `_active_metadata_id`, `_inference_count` | In-memory |
| DatasetService | File-based (JSON) | **Persistent** |
| GestureService | Registry (JSON) | **Persistent** |
| ModelRegistryService | Registry (JSON) + model files | **Persistent** |

### Frontend (Zustand Stores)

| Store | State | Persistence |
|-------|-------|-------------|
| `appStore` | Current view, init state | SessionStorage |
| `settingsStore` | Controller/recognition settings | LocalStorage |
| `gestureStore` | Gestures list, CRUD | In-memory (synced from API) |
| `datasetStore` | Stats, samples, collection status | In-memory |
| `classifierStore` | Training jobs, model registry | In-memory |
| `temporalStore` | Engine status, sequences | In-memory |
| `activityStore` | Activity logs | In-memory |

---

## API Contracts

### Camera Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/camera/status` | - | `CameraStatusResponse` |
| GET | `/api/v1/camera/devices` | - | `{devices: CameraInfo[]}` |
| POST | `/api/v1/camera/start` | `CameraConfigRequest` | `CameraConfigResponse` |
| POST | `/api/v1/camera/stop` | - | `CameraConfigResponse` |

### Tracking Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/tracking/status` | - | `TrackingStatusResponse` |
| GET | `/api/v1/tracking/result` | - | `TrackingResult` |
| POST | `/api/v1/tracking/start` | - | `TrackingConfigResponse` |
| POST | `/api/v1/tracking/stop` | - | `TrackingConfigResponse` |
| GET | `/api/v1/tracking/stream` | `camera_index` query | MJPEG stream |

### Gesture Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/gestures` | - | `GestureListResponse` |
| POST | `/api/v1/gestures` | `GestureCreate` | `GestureResponse` |
| GET | `/api/v1/gestures/{id}` | - | `GestureResponse` |
| PUT | `/api/v1/gestures/{id}` | `GestureUpdate` | `GestureResponse` |
| DELETE | `/api/v1/gestures/{id}` | `delete_samples?` | `{success, message, samples_deleted}` |

### Dataset Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/dataset/stats` | - | `DatasetStatsResponse` |
| GET | `/api/v1/dataset/samples` | query params | `SampleListResponse` |
| GET | `/api/v1/dataset/samples/{id}` | - | `DatasetSample` |
| DELETE | `/api/v1/dataset/samples/{id}` | - | `{success, message}` |
| DELETE | `/api/v1/dataset/sessions/{id}` | - | `{success, deleted_count}` |
| GET | `/api/v1/dataset/validate` | - | `DatasetValidationReport` |
| GET | `/api/v1/dataset/export/csv` | `gesture_id?` | File download |
| GET | `/api/v1/dataset/export/json` | `gesture_id?` | File download |

### Collection Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/collection/status` | - | `CollectionStatusResponse` |
| POST | `/api/v1/collection/start` | `CollectionStartRequest` | `CollectionStatusResponse` |
| POST | `/api/v1/collection/pause` | - | `CollectionStatusResponse` |
| POST | `/api/v1/collection/resume` | - | `CollectionStatusResponse` |
| POST | `/api/v1/collection/stop` | - | `CollectionStatusResponse` |

### Classifier Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/classifier/status` | - | `ClassifierStatusResponse` |
| GET | `/api/v1/classifier/dataset-readiness` | `min_samples?` | `DatasetReadinessReport` |
| POST | `/api/v1/classifier/train` | `TrainingConfigRequest` | `TrainingJobStatus` |
| GET | `/api/v1/classifier/train/{job_id}` | - | `TrainingJobStatus` |
| POST | `/api/v1/classifier/predict` | `PredictionRequest` | `PredictionResponse` |
| POST | `/api/v1/classifier/seed-samples` | `samples_per_gesture?` | `{seeded: {...}}` |

### Model Registry Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/models` | - | `ModelMetadata[]` |
| GET | `/api/v1/models/active` | - | `ModelMetadata?` |
| GET | `/api/v1/models/compare` | `model_a, model_b` | `{comparison}` |
| GET | `/api/v1/models/{id}` | - | `ModelMetadata` |
| POST | `/api/v1/models/{id}/activate` | - | `{success, model_id, in_memory_loaded}` |
| POST | `/api/v1/models/{id}/deactivate` | - | `{success, message}` |
| DELETE | `/api/v1/models/{id}` | - | `{success, message}` |

### Temporal Endpoints
| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/temporal/status` | - | `TemporalEngineStatusResponse` |
| GET | `/api/v1/temporal/gestures` | - | `TemporalGestureDefinition[]` |
| GET | `/api/v1/temporal/events` | `limit?` | `TemporalGestureEvent[]` |
| POST | `/api/v1/temporal/reset` | - | `{success, message}` |
| POST | `/api/v1/temporal/dataset/start` | `gesture_id, session_id?, target_sequences?` | `TemporalCollectionStatus` |
| POST | `/api/v1/temporal/dataset/commit` | - | `TemporalSequenceSample?` |
| POST | `/api/v1/temporal/dataset/stop` | - | `TemporalCollectionStatus` |
| GET | `/api/v1/temporal/dataset/status` | - | `TemporalCollectionStatus` |
| GET | `/api/v1/temporal/dataset/stats` | - | `{stats}` |

---

## Configuration

### Backend Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | "GestureFlow AI" | Application name |
| `APP_VERSION` | "1.0.0" | Application version |
| `ENVIRONMENT` | "development" | development/production/staging |
| `API_HOST` | "127.0.0.1" | API bind address |
| `API_PORT` | 8000 | API port |
| `API_PREFIX` | "/api/v1" | API version prefix |
| `LOG_LEVEL` | "INFO" | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `LOG_DIR` | "logs" | Log directory |
| `CORS_ALLOWED_ORIGINS` | "http://localhost:5173,http://127.0.0.1:5173" | CORS origins |
| `FRONTEND_DEV_URL` | "http://localhost:5173" | Frontend dev URL |
| `CAMERA_INDEX` | 0 | Camera device index |
| `CAMERA_WIDTH` | 640 | Frame width |
| `CAMERA_HEIGHT` | 480 | Frame height |
| `CAMERA_FPS` | 30 | Frame rate |
| `CAMERA_MIRROR` | true | Mirror frames |
| `CAMERA_BACKEND` | "" | OpenCV backend (CAP_DSHOW, CAP_V4L2, etc.) |
| `CAMERA_INIT_TIMEOUT` | 5.0 | Camera init timeout (seconds) |
| `TRACKING_MAX_HANDS` | 2 | Max hands to track |
| `TRACKING_DETECTION_CONFIDENCE` | 0.7 | Min detection confidence |
| `TRACKING_TRACKING_CONFIDENCE` | 0.5 | Min tracking confidence |
| `TRACKING_MODEL_COMPLEXITY` | 1 | MediaPipe model complexity (0/1/2) |
| `HAND_LANDMARKER_MODEL_PATH` | "models/hand_landmarker.task" | Model path |
| `DATASET_DIR` | "datasets" | Dataset directory |

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BACKEND_API_URL` | "http://localhost:8000/api/v1" | Backend API base URL |

---

## Deployment Architecture

### Development
```
┌─────────────┐     ┌─────────────┐
│  Frontend   │     │  Backend    │
│  (Vite Dev) │     │  (Uvicorn)  │
│  :5173      │     │  :8000      │
└─────────────┘     └─────────────┘
      │                   │
      └───────┬───────────┘
              │
      ┌───────┴───────┐
      │   Webcam      │
      │   Hardware    │
      └───────────────┘
```

### Production (Target)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │     │  Backend    │     │  Background │
│  (Static)   │     │  (Uvicorn)  │     │  Service    │
│  :80/443    │     │  :8000      │     │  (systemd)  │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      └───────────────────┼───────────────────┘
                          │
                  ┌───────┴───────┐
                  │   Webcam      │
                  │   Hardware    │
                  └───────────────┘
```

### Packaging (Phase 8 Target)
- **Windows:** PyInstaller → `.exe` + NSIS installer
- **macOS:** py2app → `.app` bundle + DMG
- **Linux:** PyInstaller → AppImage + systemd service

---

## Security Considerations

| Layer | Measures |
|-------|----------|
| **Transport** | CORS restricted to frontend origin; HTTPS in production |
| **Input Validation** | Pydantic schemas on all endpoints; strict typing |
| **File Operations** | Atomic writes (`.tmp` → `os.replace`); path traversal protection in ZIP extraction |
| **Model Loading** | `allow_pickle=True` only for trusted `.npz` files; registry validates structure |
| **Error Handling** | Sanitized error responses (no stack traces in production); detailed logging server-side |
| **CORS** | Restricted to configured origins; credentials allowed |
| **Dependencies** | Pinned versions; no unpinned `>=` or `*` |

---

## Monitoring & Observability

### Logging
- **Structured logging** with `extra` fields for context
- **Log levels:** DEBUG/INFO/WARNING/ERROR/CRITICAL
- **Rotation:** `RotatingFileHandler` (10MB, 5 backups)
- **Output:** Console + `logs/gestureflow.log`

### Telemetry (Built-in)
| Metric | Source | Availability |
|--------|--------|--------------|
| Camera FPS | `CameraManager._fps_window` | `/camera/status`, `/tracking/status` |
| Inference FPS | `HandTrackingService._inference_fps_window` | `/tracking/status` |
| Avg Inference Latency | `HandTrackingService._avg_inference_ms` | `/tracking/status` |
| End-to-End Latency | `HandTrackingService._latest_latency_ms` | `/tracking/status` |
| Dropped Frames | `CameraManager._dropped_frames`, `HandTrackingService._dropped_frames` | `/camera/status`, `/tracking/status` |
| Collection Progress | `DatasetCollector._collected_samples` | `/collection/status` |
| Training Progress | `TrainingEngine._jobs[job_id]` | `/classifier/train/{job_id}` |

---

## Extensibility Points

| Extension Point | Interface | Example Use |
|-----------------|-----------|-------------|
| **Custom Gestures** | `GestureService.create()` + dataset collection | Add "Vulcan Salute" gesture |
| **New Static Classifier** | `MLPClassifierModel` + `FeaturePreprocessor` | Replace MLP with CNN |
| **New Temporal Gesture** | `GestureRuleMatcher` + `TEMPORAL_GESTURE_CATALOG` | Add "Pinch Zoom" |
| **New Export Format** | `DatasetService.export_*()` | Export TFRecords, COCO JSON |
| **New Public Dataset** | `HagridParser` + `DatasetCombiner` | Add EgoHands, FreiHAND |
| **Custom Controller Action** | `ControllerService` + `settingsStore` | Map gesture to macro |
| **New Temporal Model** | Extend `TemporalEngine` + `TrainingEngine` | LSTM for complex sequences |

---

## Version Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.12+ | 3.12.10 tested |
| FastAPI | 0.115.0 | |
| Uvicorn | 0.32.0 | |
| MediaPipe | 0.10.35 | Tasks API (HandLandmarker) |
| OpenCV | 4.10.0.84 | |
| NumPy | 2.5.4 | |
| React | 19.3.1 | |
| Vite | 8.3.5 | |
| TypeScript | 7.0.2 | |
| Tailwind CSS | 4.3.3 | |
| Zustand | 5.0.16 | |
| Framer Motion | 14.7.1 | |
| MediaPipe Tasks Vision | 0.10.35 | WASM + model in `/public` |

---

## Directory Structure Summary

```
flowai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry
│   │   ├── core/                   # Config, logging, lifecycle
│   │   ├── api/
│   │   │   ├── router.py           # Central router
│   │   │   └── routes/             # 9 route modules
│   │   ├── services/               # 14 service modules
│   │   ├── schemas/                # Pydantic models
│   │   ├── exceptions/             # Global exception handlers
│   │   └── __init__.py
│   ├── tests/                      # 124 tests
│   ├── datasets/                   # Persistent storage
│   ├── models/                     # MediaPipe model + trained classifiers
│   ├── scripts/                    # Verification scripts
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── camera/CameraSection.tsx    # Dual-mode camera
│   │   ├── ui/                         # Reusable UI
│   │   ├── layout/                     # Header, AppLayout
│   │   └── visuals/
│   ├── features/
│   │   ├── gesture-manager/            # 5-tab studio
│   │   ├── model-training/             # Training UI
│   │   ├── live-control/               # Controller UI
│   │   ├── dashboard/                  # Overview
│   │   └── ...
│   ├── store/                          # 7 Zustand stores
│   ├── services/api/                   # Typed API clients
│   ├── types/                          # TypeScript types
│   └── ...
│
├── public/
│   ├── models/hand_landmarker.task     # Browser MediaPipe model
│   └── wasm/                           # MediaPipe WASM
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## Conclusion

The GestureFlow AI architecture is **modular, well-tested, and production-ready for Phases 1-5**. The dual-mode camera architecture (browser WASM + Python backend) provides flexibility but requires camera ownership resolution. The backend services are cleanly separated with clear interfaces, and the frontend follows modern React patterns with Zustand for state management. All 124 backend tests pass, and the frontend builds without errors.

**Primary architectural risk:** Camera device ownership conflict between browser and Python processes. **Recommended mitigation:** Implement explicit camera ownership protocol with API-level coordination.