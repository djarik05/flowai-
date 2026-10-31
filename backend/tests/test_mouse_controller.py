"""
Unit tests for Phase 6A Hand-Controlled Mouse Movement.
All tests use MockMouseDriver to guarantee that actual OS desktop cursor
is never moved during automated test suites.
"""

import time
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.mouse_controller import (
    MouseController,
    MockMouseDriver,
    MouseDriver,
    get_mouse_controller,
)
from app.schemas.mouse import MouseSettings


@pytest.fixture
def mock_driver():
    return MockMouseDriver(screen_width=1920, screen_height=1080)


@pytest.fixture
def controller(mock_driver):
    ctrl = MouseController(driver=mock_driver)
    ctrl.initialize()
    yield ctrl
    ctrl.stop()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_mouse_controller_disabled_by_default(controller):
    """Safety Rule: Controller must be OFF by default."""
    assert controller.is_enabled is False
    assert controller.is_running is False
    status = controller.get_status()
    assert status.enabled is False
    assert status.state == "disabled"
    assert status.hand_detected is False


def test_mouse_controller_start_stop_idempotent(controller):
    """Repeated start/stop must be safe and idempotent."""
    assert controller.start() is True
    assert controller.is_enabled is True
    assert controller.is_running is True

    # Second start is idempotent
    assert controller.start() is True
    assert controller.is_enabled is True

    # Stop
    assert controller.stop() is True
    assert controller.is_enabled is False
    assert controller.is_running is False

    # Second stop is idempotent
    assert controller.stop() is True
    assert controller.is_enabled is False


def test_coordinate_mapping_center(controller, mock_driver):
    """Center normalized coordinate (0.5, 0.5) maps to screen midpoint."""
    screen_x, screen_y = controller.map_coordinates(0.5, 0.5)
    assert screen_x == 1920 // 2
    assert screen_y == 1080 // 2


def test_coordinate_mapping_boundaries_and_clamping(controller, mock_driver):
    """Coordinates outside active box or screen range must clamp strictly to [0, screen-1]."""
    # Far beyond left/top
    x_min, y_min = controller.map_coordinates(-0.5, -0.5)
    assert x_min == 0
    assert y_min == 0

    # Far beyond right/bottom
    x_max, y_max = controller.map_coordinates(1.5, 1.5)
    assert x_max == 1919
    assert y_max == 1079

    # Exactly within margins (margin = 0.15)
    x_margin_left, y_margin_top = controller.map_coordinates(0.15, 0.15)
    assert x_margin_left == 0
    assert y_margin_top == 0

    x_margin_right, y_margin_bottom = controller.map_coordinates(0.85, 0.85)
    assert x_margin_right == 1919
    assert y_margin_bottom == 1079


def test_sensitivity_scaling(controller, mock_driver):
    """Higher sensitivity expands range around screen center."""
    controller.update_settings(sensitivity=1.0)
    x_normal, _ = controller.map_coordinates(0.6, 0.5)

    controller.update_settings(sensitivity=2.0)
    x_amplified, _ = controller.map_coordinates(0.6, 0.5)

    center_x = 1919 / 2.0
    # Displacement from center with sensitivity 2.0 must be greater than with 1.0
    assert (x_amplified - center_x) > (x_normal - center_x)


def test_smoothing_calculation_and_jump_prevention(controller, mock_driver):
    """When tracking begins or resumes, initial target is not smoothed to prevent cursor snap."""
    controller.start()
    controller.update_settings(smoothing_alpha=0.5)

    # First point: tracking begins
    controller.on_landmark_point(0.5, 0.5)
    # Wait for worker iteration
    time.sleep(0.04)

    assert mock_driver.current_x == 960
    assert mock_driver.current_y == 540

    # Second point with smoothing
    controller.on_landmark_point(0.7, 0.5)
    time.sleep(0.04)

    # Position should move towards target but smoothed
    assert mock_driver.current_x > 960


def test_tracking_loss_and_stale_rejection(controller, mock_driver):
    """Tracking loss or stale timestamp halts movement immediately."""
    controller.start()
    controller.update_settings(tracking_timeout_ms=50.0)

    # Feed a point
    controller.on_landmark_point(0.5, 0.5)
    time.sleep(0.02)
    assert controller.get_status().hand_detected is True

    # Wait past timeout
    time.sleep(0.08)
    status = controller.get_status()
    assert status.hand_detected is False
    assert status.state == "waiting_for_hand"

    # Explicit tracking loss
    controller.on_landmark_point(0.5, 0.5)
    assert controller.get_status().hand_detected is True
    controller.on_tracking_loss()
    assert controller.get_status().hand_detected is False


def test_mouse_api_endpoints(client, mock_driver):
    """Verify REST API routes for mouse control."""
    # Ensure test uses mock driver
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)
    ctrl.stop()

    # GET /status
    res = client.get("/api/v1/mouse/status")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is False
    assert data["state"] == "disabled"

    # POST /enable
    res = client.post("/api/v1/mouse/enable")
    assert res.status_code == 200
    assert res.json()["enabled"] is True

    # PUT /settings
    res = client.put(
        "/api/v1/mouse/settings",
        json={"sensitivity": 1.5, "smoothing_alpha": 0.4, "active_margin_x": 0.1},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["sensitivity"] == 1.5
    assert data["smoothing_alpha"] == 0.4
    assert data["active_margin_x"] == 0.1

    # POST /cursor-point
    res = client.post(
        "/api/v1/mouse/cursor-point",
        json={"x": 0.5, "y": 0.5},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # POST /disable
    res = client.post("/api/v1/mouse/disable")
    assert res.status_code == 200
    assert res.json()["enabled"] is False
    assert res.json()["state"] == "disabled"


def test_mouse_enable_and_disable_independent_of_camera(client, mock_driver):
    """Verify mouse control enable/disable operates independently without altering camera ownership."""
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)
    ctrl.stop()

    from app.api.routes.camera import get_camera_manager
    camera_mgr = get_camera_manager()
    initial_owner = camera_mgr.get_owner()

    # Initial state
    assert ctrl.is_enabled is False

    # POST /api/v1/mouse/enable
    res = client.post("/api/v1/mouse/enable")
    assert res.status_code == 200
    assert res.json()["enabled"] is True
    assert camera_mgr.get_owner() == initial_owner

    # POST /api/v1/mouse/disable
    res = client.post("/api/v1/mouse/disable")
    assert res.status_code == 200
    assert res.json()["enabled"] is False
    assert camera_mgr.get_owner() == initial_owner


def test_mouse_emergency_stop_endpoint(client, mock_driver):
    """Phase 6A.3: Emergency stop endpoint immediately halts cursor movement and disables control."""
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)
    ctrl.start()
    assert ctrl.is_enabled is True

    res = client.post("/api/v1/mouse/emergency-stop")
    assert res.status_code == 200
    assert res.json()["enabled"] is False
    assert res.json()["state"] == "disabled"
    assert ctrl.is_enabled is False


def test_camera_stop_auto_disables_mouse(client, mock_driver):
    """Phase 6A.3 (Scenario D): Turning camera off automatically disables mouse control."""
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)
    ctrl.start()
    assert ctrl.is_enabled is True

    # POST /api/v1/camera/stop
    res = client.post("/api/v1/camera/stop")
    assert res.status_code == 200
    # Mouse controller must be automatically disabled
    assert ctrl.is_enabled is False


def test_camera_release_auto_disables_mouse(client, mock_driver):
    """Phase 6A.3: Releasing camera ownership automatically disables mouse control."""
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)
    ctrl.start()
    assert ctrl.is_enabled is True

    res = client.post("/api/v1/camera/release")
    assert res.status_code == 200
    assert ctrl.is_enabled is False


def test_mouse_controller_backend_hand_tracking_feed(mock_driver):
    """Phase 6A.2: Verify hand tracking landmark 8 feeds directly to mouse controller."""
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)
    ctrl.stop()
    ctrl.start()

    from app.schemas.tracking import DetectedHand, Landmark

    # Create 21 test landmarks with index tip (landmark 8) at (0.4, 0.4)
    landmarks = [
        Landmark(
            index=i,
            x=0.4 if i == 8 else 0.5,
            y=0.4 if i == 8 else 0.5,
            z=0.0,
            pixel_x=256 if i == 8 else 320,
            pixel_y=192 if i == 8 else 240,
        )
        for i in range(21)
    ]
    test_hand = DetectedHand(
        hand_id=0,
        landmarks=landmarks,
        handedness="Right",
        handedness_confidence=0.95,
    )

    # Feed landmark point into controller
    index_tip = test_hand.landmarks[8]
    ctrl.on_landmark_point(index_tip.x, index_tip.y, capture_time=time.time())

    # Wait briefly for worker to process movement
    time.sleep(0.05)

    status = ctrl.get_status()
    assert status.enabled is True
    assert status.hand_detected is True
    assert status.control_point is not None
    assert status.control_point["x"] == 0.4
    assert status.control_point["y"] == 0.4

    # Simulate tracking loss (no hands detected)
    ctrl.on_tracking_loss()
    time.sleep(0.02)
    # Controller halts movement and resets smoothing
    assert ctrl._prev_smoothed_x is None

    ctrl.stop()


def test_mouse_controller_repeated_enable_disable_safety(client, mock_driver):
    """Phase 6A.2: Rapid repeated toggle of mouse control must be idempotent and crash-free."""
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock_driver)

    for _ in range(5):
        res_en = client.post("/api/v1/mouse/enable")
        assert res_en.status_code == 200
        assert res_en.json()["enabled"] is True

        res_dis = client.post("/api/v1/mouse/disable")
        assert res_dis.status_code == 200
        assert res_dis.json()["enabled"] is False

    assert ctrl.is_enabled is False

