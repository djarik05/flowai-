# Next Development Roadmap

**Project:** GestureFlow AI  
**Date:** October 30, 2026  
**Based On:** Complete Technical Audit (October 30, 2026)

---

## Current Project Status

| Phase | Status | Blockers |
|-------|--------|----------|
| 1: Backend Foundation | ✅ Complete | - |
| 2: Webcam & Hand Tracking | ✅ Complete | Camera ownership conflict |
| 3: Dataset Collection | ✅ Complete | Session resume after restart |
| 4: Static Gesture Recognition | ✅ Complete | - |
| 5: Temporal Gesture Recognition | ✅ Complete (rule-based) | No ML model training |
| 6: Mouse/Keyboard Control | ⚠️ Partial | No OS input hooks |
| 7: Frontend-Backend Integration | ✅ Substantially Complete | Camera ownership, hardcoded URLs |
| 8: Background Runtime & Packaging | ❌ Not Started | All |

---

## Immediate Priorities (Next 2 Weeks)

### P0 - Critical Blockers

| Task ID | Task | Phase | Objective | Files | Acceptance Criteria |
|---------|------|-------|-----------|-------|---------------------|
| **T-001** | Fix camera ownership conflict | 2/7 | Enable simultaneous frontend/backend camera use | `CameraSection.tsx`, `camera_manager.py`, `camera.py` | 1) Backend `/camera/start` signals frontend to release<br>2) Frontend auto-releases on backend start<br>3) Single ownership with explicit handoff |
| **T-002** | Create `.env` from `.env.example` | 1 | Backend starts without manual config | `backend/.env.example` → `backend/.env` | Fresh clone → copy `.env.example` → `python -m uvicorn app.main:app` works |
| **T-003** | Fix MediaPipe shutdown crash | 2 | Clean tracking stop without executor errors | `hand_tracking.py:806-817` | Stop tracking 10x → no "cannot schedule new futures" errors |

### P1 - High Priority

| Task ID | Task | Phase | Objective | Files | Acceptance Criteria |
|---------|------|-------|-----------|-------|---------------------|
| **T-004** | Replace hardcoded backend URLs | 7 | Frontend works in non-localhost deployments | `CameraSection.tsx:194,198,455,469` | Deploy to LAN IP → frontend connects via `VITE_BACKEND_API_URL` |
| **T-005** | Add session persistence for collection | 3 | Resume collection after backend restart | `dataset_collector.py`, `collection.py` | Restart backend mid-collection → "Resume Session" works |
| **T-006** | Implement temporal ML model training | 5 | Train LSTM/Transformer for dynamic gestures | `temporal/` services, new `temporal_classifier.py` | Train temporal model → accuracy > rule-based baseline |
| **T-007** | Add OS input hooks (pynput) | 6 | Gesture → mouse/keyboard actions | New `controller_service.py`, `LiveControlView.tsx` | Toggle controller → mouse moves, clicks work |

---

## Short-Term Goals (Month 1-2)

### Phase 6: Mouse & Keyboard Control

| Task ID | Task | Dependencies | Description |
|---------|------|--------------|-------------|
| T-008 | Add `pynput`/`pyautogui` to requirements | T-007 | `pip install pynput pyautogui` |
| T-009 | Implement `ControllerService` | T-008 | Gesture→action mapping, sensitivity, cooldown |
| T-010 | Wire `LiveControlView` to backend | T-009 | Connect UI toggles to `/controller/*` endpoints |
| T-011 | Implement gesture→action mapping UI | T-010 | Map gestures (G001-G009) to actions |
| T-012 | Add emergency stop global hotkey | T-011 | Global hotkey (e.g., Ctrl+Shift+Esc) kills controller |

### Phase 5 Enhancement: Temporal ML Models

| Task ID | Task | Dependencies | Description |
|---------|------|--------------|-------------|
| T-013 | Design `TemporalSequenceClassifier` | T-006 | LSTM/Transformer for sequence classification |
| T-014 | Sequence dataset preparation | T-013 | Fixed-length resampling, padding, augmentation |
| T-015 | Temporal training pipeline | T-014 | Extend `TrainingEngine` for sequences |
| T-016 | Temporal model registry | T-015 | Extend `ModelRegistryService` for temporal models |
| T-017 | Temporal inference service | T-016 | Real-time sequence classification |

---

## Medium-Term Goals (Month 2-3)

### Phase 7: Complete Integration Polish

| Task ID | Task | Description |
|---------|------|-------------|
| T-018 | Fix camera ownership protocol | Single ownership with explicit handoff |
| T-019 | Replace hardcoded URLs with env var | Use `VITE_BACKEND_API_URL` |
| T-020 | Split `CameraSection.tsx` (1240 lines) | Split into sub-components |
| T-021 | Refactor singleton globals to DI | Use FastAPI `app.state` + `Depends()` |
| T-022 | Add session persistence for collection | Resume after restart |
| T-023 | Add comprehensive error boundaries | Frontend error recovery |

### Phase 7: Advanced Features

| Task ID | Task | Description |
|---------|------|-------------|
| T-024 | Multi-hand gesture composition | Two-hand gestures (e.g., pinch+swipe) |
| T-025 | Gesture recording/playback | Record gesture sequences for macros |
| T-026 | Application-specific profiles | Per-app gesture mappings |
| T-027 | Cloud sync for gestures/models | Optional cloud backup |

---

## Long-Term Goals (Month 3-6)

### Phase 8: Background Runtime & Packaging

| Task ID | Task | Description |
|---------|------|-------------|
| T-028 | System tray integration | Windows: `pystray`, macOS: `rumps`, Linux: `libappindicator` |
| T-029 | Global hotkey registration | System-wide emergency stop, toggle |
| T-030 | Background service mode | Run as daemon/service, auto-start on login |
| T-031 | Executable packaging | PyInstaller (Windows), py2app (macOS), AppImage (Linux) |
| T-032 | Auto-update mechanism | Check for updates, silent install |
| T-033 | Settings persistence | User preferences, calibration data |

### Phase 9: Advanced ML & Production

| Task ID | Task | Description |
|---------|------|-------------|
| T-034 | ONNX export for models | Faster inference, cross-platform |
| T-035 | TensorRT optimization | GPU-accelerated inference on NVIDIA |
| T-036 | Active learning loop | User corrections → retrain |
| T-037 | Gesture personalization | Per-user adaptation |
| T-038 | Multi-user support | Profiles, guest mode |
| T-039 | Analytics dashboard | Usage stats, accuracy trends |

---

## Dependency Graph

```
T-001 (Camera Ownership)
    ├─→ T-004 (Hardcoded URLs)
    └─→ T-018 (Ownership Protocol)

T-002 (Env File) ─────────────────────→ All backend tasks

T-003 (MediaPipe Shutdown) ──────────→ T-018

T-005 (Session Persistence) ─────────→ T-022

T-006 (Temporal ML) ─────────────────→ T-013 → T-014 → T-015 → T-016 → T-017

T-007 (OS Input Hooks)
    ├─→ T-008 → T-009 → T-010 → T-011 → T-012

T-018 (Ownership Protocol) ──────────→ T-020 (Split CameraSection)

T-020 ────────────────────────────────→ T-021 (DI Refactor)

T-028..T-033 (Phase 8) ──────────────→ Require T-001, T-002, T-003, T-018, T-021
```

---

## Resource Requirements

| Resource | Current | Needed |
|----------|---------|--------|
| **Backend Dev** | 1 | 1-2 |
| **Frontend Dev** | 1 | 1 |
| **ML Engineer** | 0 | 0.5 (for T-006, T-013-017) |
| **QA/Testing** | 0 | 0.5 (for HW testing) |
| **DevOps** | 0 | 0.5 (for T-028-033) |
| **Hardware** | 1 webcam | 2+ webcams (multi-cam testing) |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Camera ownership unsolvable | Medium | High | Fallback: single-mode only (browser OR backend) |
| MediaPipe version drift | High | Medium | Pin versions, sync check on startup |
| OS input hooks blocked by OS | Medium | High | Test early on target OS; fallback to accessibility API |
| Model accuracy insufficient | Medium | High | Collect more data, try larger model, ensemble |
| Packaging complexity | High | Medium | Start packaging early; test on all 3 OSes |

---

## Recommended Sprint Plan

### Sprint 1 (Week 1-2): Critical Fixes
- [ ] T-001: Camera ownership protocol
- [ ] T-002: Create `.env` documentation
- [ ] T-003: MediaPipe shutdown fix
- [ ] T-004: Replace hardcoded URLs

### Sprint 2 (Week 3-4): Phase 6 Foundation
- [ ] T-005: Session persistence
- [ ] T-007: Add pynput/pyautogui
- [ ] T-008: ControllerService implementation
- [ ] T-009: Wire LiveControlView

### Sprint 3 (Week 5-6): Phase 6 Completion
- [ ] T-010: Wire LiveControlView to backend
- [ ] T-011: Gesture→action mapping UI
- [ ] T-011: Emergency stop hotkey
- [ ] T-006: Temporal ML design

### Sprint 4 (Week 7-8): Polish & Phase 8 Prep
- [ ] T-018: Camera ownership protocol v2
- [ ] T-019: Replace hardcoded URLs
- [ ] T-020: Split CameraSection
- [ ] T-021: DI refactor
- [ ] T-022: Session persistence

### Sprint 5+ (Month 3+): Advanced Features
- T-013 through T-039 per roadmap above

---

## Definition of Done for Phase 6 (Minimum Viable)

| Criterion | Metric |
|-----------|--------|
| Controller toggles on/off | UI toggle → backend `enabled` state changes |
| Mouse movement | Open Palm (G001) → cursor moves smoothly |
| Left click | Closed Fist (G002) → left click fires |
| Right click | Peace Sign (G004) → right click fires |
| Scroll | Swipe Up/Down → scroll fires |
| Emergency stop | Global hotkey → all input stops immediately |
| Settings persist | Restart app → settings restored |
| No crashes | 1 hour continuous use → no exceptions |

---

## Recommended Next Step

**Start with T-001 (Camera Ownership Protocol)** — this is the single biggest blocker preventing reliable end-to-end testing of the full pipeline. Once resolved, the rest of the pipeline can be validated end-to-end with real hardware.