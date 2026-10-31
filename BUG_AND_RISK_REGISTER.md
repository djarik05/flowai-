# Bug & Risk Register

**Project:** GestureFlow AI  
**Audit Date:** October 30, 2026  
**Total Items:** 16

---

## Severity Definitions

| Severity | Definition | SLA |
|----------|------------|-----|
| **CRITICAL** | Application-breaking, data loss, security vulnerability, complete feature failure | Fix immediately |
| **HIGH** | Core functionality broken, incorrect behavior, resource leak, blocking issue | Fix within 1 sprint |
| **MEDIUM** | Important feature degraded, workaround exists, technical debt | Fix within 2 sprints |
| **LOW** | Minor issue, cosmetic, documentation, nice-to-have | Fix when convenient |
| **INFORMATIONAL** | Observation, best practice, future consideration | Track for future |

---

## Bug & Risk Register

| ID | Issue | Severity | Impact | File/Module | Root Cause | Recommended Fix | Status |
|----|-------|----------|--------|-------------|------------|-----------------|--------|
| **BUG-001** | Camera ownership conflict between browser WASM and Python OpenCV | **CRITICAL** | Camera cannot be used by both frontend and backend simultaneously; second opener fails with `NotReadableError` | `src/components/camera/CameraSection.tsx` + `backend/app/services/camera_manager.py` | Both browser `getUserMedia()` and Python `cv2.VideoCapture()` attempt exclusive access to same camera device | Implement camera ownership protocol: 1) Backend `/camera/start` signals frontend to release; 2) Frontend detects backend usage and auto-releases; 3) Single ownership model with explicit handoff | 🔴 Open |
| **BUG-002** | Missing `.env` file prevents backend startup | **CRITICAL** | Backend fails with `ModuleNotFoundError` or configuration errors without manual `.env` creation | `backend/.env` (missing) | No `.env` file created from `.env.example`; defaults work but MediaPipe model path may fail | 1) Document `.env` creation in README; 2) Add startup check with helpful error message; 3) Consider generating `.env` from `.env.example` on first run | 🔴 Open |
| **BUG-003** | MediaPipe executor shutdown crash during tracking stop | **HIGH** | "cannot schedule new futures after shutdown" error logged during tracking stop; caught but pollutes logs | `backend/app/services/hand_tracking.py:806-817` | MediaPipe Tasks executor still processing when `landmarker.close()` called; frame processing continues during shutdown | 1) Set `_stop_event` before closing landmarker; 2) Add graceful wait for processing queue to drain; 3) Check `_stop_event` before submitting new frames | 🔴 Open |
| **BUG-004** | Hardcoded backend URLs in CameraSection | **HIGH** | Frontend won't work in non-localhost deployments (Docker, LAN, production) | `src/components/camera/CameraSection.tsx:194,198,455,469` | Direct string literals `http://localhost:8000` used for API calls and MJPEG stream | Replace with `import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000/api/v1'` | 🔴 Open |
| **BUG-005** | No session resume after backend restart | **MEDIUM** | Partial collection sessions lost on backend restart; session_id and collected samples not recoverable | `backend/app/services/dataset_collector.py` | Collection state stored only in memory (`_collector` singleton); no persistence of session state | 1) Persist session state to disk (`session_state.json`); 2) On startup, restore active sessions; 3) Add "Resume Session" API endpoint | 🟡 Open |
| **BUG-006** | Temporal gesture model training not implemented | **MEDIUM** | Dynamic gesture recognition is rule-based only; no ML model training pipeline for temporal sequences | `backend/app/services/temporal/` | Only rule-based `GestureRuleMatcher` implemented; no sequence classifier training | 1) Add `TemporalSequenceClassifier` (LSTM/Transformer); 2) Implement sequence dataset preparation; 2) Add training endpoint in `temporal.py` | 🟡 Open |
| **BUG-007** | No OS input hooks for Phase 6 mouse/keyboard control | **MEDIUM** | Controller settings UI exists but no actual OS-level input simulation | `src/features/live-control/LiveControlView.tsx`, `src/store/settingsStore.ts` | No `pynput`/`pyautogui` integration; controller settings only stored in Zustand | 1) Add `pynput` to requirements; 2) Implement `ControllerService` with gesture→action mapping; 3) Wire `LiveControlView` toggles to backend | 🟡 Open |
| **BUG-008** | MediaPipe shutdown error during tracking stop | **MEDIUM** | "cannot schedule new futures after shutdown" error caught but logs error trace | `hand_tracking.py:806-817` | Same as BUG-003 but specifically during stop | Same fix as BUG-003 | 🟡 Open |
| **BUG-009** | CameraSection.tsx too large (1240 lines) | **LOW** | Difficult to maintain, test, and review; violates single responsibility | `src/components/camera/CameraSection.tsx` | All camera logic, UI, detection, telemetry, overlays in one component | Split into: `CameraControls`, `CameraViewport`, `CameraTelemetry`, `CameraOverlays`, `CameraStandby` | 🟢 Open |
| **BUG-010** | ApplicationService dynamic import in shutdown | **LOW** | Circular import workaround creates fragile dependency | `backend/app/services/application_service.py:102` | Import inside function to avoid circular import with `collection.py` | Refactor module structure to eliminate circular dependency | 🟢 Open |
| **BUG-011** | Module-level singleton globals in routes | **LOW** | Global `_collector`, `_camera_manager`, `_tracking_service` create hidden dependencies and test isolation issues | `backend/app/api/routes/collection.py`, `camera.py`, `tracking.py` | Module-level `_collector: Optional[DatasetCollector] = None` pattern | Use FastAPI `app.state` for singleton services; dependency injection via `Depends()` | 🟢 Open |
| **BUG-012** | No temporal ML model training pipeline | **INFORMATIONAL** | Only rule-based temporal recognition; no sequence classifier for improved accuracy | `backend/app/services/temporal/` | Phase 5 scope focused on rule-based recognition | Add LSTM/Transformer temporal classifier; sequence dataset preparation; training endpoint | 🔵 Open |
| **BUG-013** | Browser and backend MediaPipe models may drift | **INFORMATIONAL** | Two independent MediaPipe pipelines (WASM + Python Tasks) may produce different results | `CameraSection.tsx` (WASM) vs `hand_tracking.py` (Python Tasks) | Separate model files: `/public/models/hand_landmarker.task` vs `backend/models/hand_landmarker.task` | Single source of truth for model; version sync check on startup | 🔵 Open |
| **BUG-014** | Collection session not persisted across restarts | **INFORMATIONAL** | Partial progress lost if backend restarts mid-collection | `dataset_collector.py` | Session state in memory only | Persist session state; resume capability | 🔵 Open |
| **BUG-015** | Temporal gesture ML model not implemented | **INFORMATIONAL** | Only rule-based recognition; no sequence classifier for complex gestures | `temporal/` services | Phase 5 scope was rule-based | Future: LSTM/Transformer temporal classifier | 🔵 Open |
| **BUG-016** | Missing Phase 8 background runtime & packaging | **INFORMATIONAL** | No system tray, executable packaging, background service | Project root | Phase 8 not started | Implement Phase 8 when Phases 1-7 stable | 🔵 Open |

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 2 |
| INFORMATIONAL | 6 |
| **TOTAL** | **16** |

---

## Priority Fix Order

| Priority | Bug IDs | Rationale |
|----------|---------|-----------|
| 1 | BUG-001, BUG-002 | Blockers for basic operation |
| 2 | BUG-003, BUG-004 | High-impact reliability/usability issues |
| 3 | BUG-005, BUG-006, BUG-007 | Core feature gaps for next phases |
| 4 | BUG-009, BUG-010, BUG-011 | Code quality/maintainability |
| 5 | BUG-012 through BUG-016 | Future enhancements |

---

## Risk Heat Map

| | Low Impact | Medium Impact | High Impact | Critical Impact |
|---|---|---|---|---|
| **High Likelihood** | BUG-009, BUG-010, BUG-011 | BUG-005, BUG-006, BUG-007 | BUG-003, BUG-004 | BUG-001, BUG-002 |
| **Medium Likelihood** | BUG-012, BUG-013, BUG-014, BUG-015, BUG-016 | | BUG-006 | |
| **Low Likelihood** | | | | |

---

## Mitigation Tracking

| Bug ID | Mitigation | Owner | Target Date | Verification |
|--------|------------|-------|-------------|--------------|
| BUG-001 | Camera ownership protocol | - | - | Manual test: start backend camera, verify frontend releases |
| BUG-002 | Document `.env` creation | - | - | Fresh clone → follow README → backend starts |
| BUG-003 | Graceful MediaPipe shutdown | - | - | Start/stop tracking 10x, verify no executor errors |
| BUG-004 | Replace hardcoded URLs | - | - | Deploy to LAN IP, verify frontend works |
| BUG-005 | Session persistence | - | - | Restart backend mid-collection, verify resume |
| BUG-006 | Temporal ML pipeline | - | - | Train temporal model, verify accuracy > rule-based |
| BUG-007 | OS input hooks | - | - | Toggle controller, verify mouse moves |