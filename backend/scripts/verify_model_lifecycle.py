"""
GestureFlow AI - Phase 4 Model Verification Script.

Verifies:
1. Load active model from disk (backend/models/classifiers/).
2. Inspect metadata: model_id, model_name, class labels, feature preprocessing config.
3. Simulate clean backend reload / cold start and verify active model auto-loading.
4. Verify hot reload: activating and deactivating models without crashing or interrupting state.
"""

from pathlib import Path
import json
import time

BACKEND_DIR = Path(__file__).resolve().parent.parent

def run_model_verification():
    print("=" * 70)
    print(" GESTUREFLOW AI — PHASE 4 MODEL LIFECYCLE VERIFICATION")
    print("=" * 70)

    from app.services.model_registry import ModelRegistryService
    from app.services.classifier_service import ClassifierService
    from app.services.camera_manager import CameraManager
    from app.services.hand_tracking import HandTrackingService

    # 1. Inspect Registry On Disk
    registry = ModelRegistryService()
    active_meta = registry.get_active_model()
    print(f"[1] ACTIVE MODEL ON DISK:")
    if not active_meta:
        print("  • ERROR: No active model found in registry.")
        return False
    print(f"  • Model ID:       {active_meta.model_id}")
    print(f"  • Model Name:     {active_meta.model_name}")
    print(f"  • Version:        {active_meta.version}")
    print(f"  • Feature Schema: {active_meta.feature_schema} ({active_meta.feature_dim}-D)")
    print(f"  • Classes ({len(active_meta.classes)}):   {[c['name'] for c in active_meta.classes]}")
    print(f"  • Test Accuracy:  {active_meta.metrics.accuracy * 100:.2f}%")
    print(f"  • Weights File:   {active_meta.model_file}")
    assert Path(active_meta.model_file).exists(), f"Weights file not found: {active_meta.model_file}"

    # 2. Simulate Cold Backend Start
    print("\n[2] COLD START & AUTO-LOAD INFERENCE ENGINE:")
    cls_svc = ClassifierService(registry_service=registry)
    loaded = cls_svc.load_active_model(force=True)
    status = cls_svc.get_status()
    print(f"  • Classifier Engine Loaded: {loaded}")
    print(f"  • In-Memory Active Model:   {status.active_model_name} ({status.active_model_id})")
    print(f"  • Registered Classes:       {[c['name'] for c in status.classes]}")
    print(f"  • Preprocessing Bone:       {active_meta.preprocessing_config.get('reference_bone')}")
    assert status.is_model_loaded is True
    assert status.active_model_id == active_meta.model_id

    # 3. Hot-Reload Lifecycle While Tracking Service Is Active
    print("\n[3] HOT-RELOAD LIFECYCLE VERIFICATION:")
    cam_mgr = CameraManager()
    tracking_svc = HandTrackingService(camera_manager=cam_mgr)
    tracking_svc.initialize()

    from app.services.classifier_service import get_classifier_service
    singleton_svc = get_classifier_service()

    # Deactivate model
    print("  • Deactivating model...")
    registry.deactivate_model(active_meta.model_id)
    singleton_svc.load_active_model(force=True)
    status_deact = singleton_svc.get_status()
    print(f"    - In-Memory Loaded after deactivation: {status_deact.is_model_loaded} (Expected: False)")
    assert status_deact.is_model_loaded is False

    # Reactivate model
    print("  • Reactivating model (Hot Reload)...")
    registry.activate_model(active_meta.model_id)
    singleton_svc.load_active_model(force=True)
    status_react = singleton_svc.get_status()
    print(f"    - In-Memory Loaded after reactivation: {status_react.is_model_loaded} (Expected: True)")
    print(f"    - Model ID after reactivation:         {status_react.active_model_id}")
    assert status_react.is_model_loaded is True
    assert status_react.active_model_id == active_meta.model_id

    tracking_svc.stop()
    print("\n======================================================================")
    print(" MODEL LIFECYCLE & HOT-RELOAD VERIFICATION: ALL PASSED")
    print("======================================================================")
    return True

if __name__ == "__main__":
    run_model_verification()
