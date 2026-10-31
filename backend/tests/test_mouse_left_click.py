"""
Automated Unit Tests for Phase 6B.1 Gesture-Based Left Click.

All tests utilize MockMouseDriver to guarantee that actual OS desktop clicks
are NEVER executed during automated test suites.
"""

import math
import time
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.mouse_controller import (
    MouseController,
    MockMouseDriver,
    get_mouse_controller,
)
from app.schemas.mouse import MouseSettings


@pytest.fixture
def mock_driver():
    """Mock mouse driver tracking movements and simulated clicks."""
    return MockMouseDriver(screen_width=1920, screen_height=1080)


@pytest.fixture
def controller(mock_driver):
    """Clean controller instance for testing with mock driver."""
    ctrl = MouseController(driver=mock_driver)
    ctrl.initialize()
    yield ctrl
    ctrl.stop()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as c:
        yield c


def test_left_click_defaults_and_settings(controller):
    """Verify Phase 6B.1 default settings for gesture left click."""
    status = controller.get_status()
    assert status.left_click_enabled is True
    assert status.pinch_activation_threshold == 0.05
    assert status.pinch_release_threshold == 0.08
    assert status.click_cooldown_ms == 400.0
    assert status.pinch_state == "disabled"  # Controller disabled by default
    assert status.click_count == 0
    assert status.last_click_time is None
    assert status.last_click_position is None


def test_pinch_detection_triggers_left_click(controller, mock_driver):
    """Pinch distance below activation threshold triggers exactly one left click."""
    controller.start()
    assert controller.is_enabled is True

    # Feed index fingertip at screen center with pinch distance 0.03 (<= 0.05)
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03)

    assert clicked is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "left"
    status = controller.get_status()
    assert status.click_count == 1
    assert status.last_click_time is not None
    assert status.pinch_state == "pinched"
    assert status.pinch_distance == 0.03


def test_activation_threshold_boundary(controller, mock_driver):
    """Click only triggers when pinch distance <= activation_threshold (0.05)."""
    controller.start()

    # Distance 0.051 (> 0.050) -> No click
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.051)
    assert clicked is False
    assert len(mock_driver.clicks) == 0

    # Distance 0.050 (<= 0.050) -> Click triggers
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.050)
    assert clicked is True
    assert len(mock_driver.clicks) == 1


def test_hysteresis_and_release_threshold(controller, mock_driver):
    """
    Hysteresis test:
    After pinch triggers at <= 0.05, hand must open past release threshold (>= 0.08)
    before another click can be triggered.
    """
    controller.start()
    # Click 1 triggered
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 1

    # Distance increases to 0.065 (between activation 0.05 and release 0.08 - deadband)
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.065)
    assert clicked is False
    assert len(mock_driver.clicks) == 1

    # Hand pinches again to 0.03 WITHOUT having released past 0.08 -> NO click
    # Simulating time passage past cooldown
    controller._last_click_time = time.time() - 1.0  # Cooldown elapsed
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03)
    assert clicked is False
    assert len(mock_driver.clicks) == 1

    # Hand releases past release threshold (>= 0.08)
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.10)
    assert clicked is False
    assert controller._awaiting_pinch_release is False

    # Now pinch again at 0.03 -> Click 2 triggers!
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03)
    assert clicked is True
    assert len(mock_driver.clicks) == 2


def test_one_click_per_pinch_no_repeated_clicks_while_holding(controller, mock_driver):
    """
    Safety Rule: Holding the pinch must NEVER trigger repeated clicks.
    Exactly one click per pinch action.
    """
    controller.start()

    # Initial pinch triggers click 1
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.02) is True
    assert len(mock_driver.clicks) == 1

    # Hold pinch for 50 subsequent frames over simulated time
    for i in range(50):
        # Even if cooldown has passed, holding pinch must not trigger
        controller._last_click_time = time.time() - 1.0
        clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.02)
        assert clicked is False

    assert len(mock_driver.clicks) == 1
    assert controller.get_status().click_count == 1


def test_click_cooldown_debouncing(controller, mock_driver):
    """Rapid pinches within cooldown window (< 400ms) are debounced."""
    controller.start()

    # Click 1 at t=0
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 1

    # Release hand past 0.08 immediately
    controller.on_landmark_point(0.5, 0.5, pinch_distance=0.12)

    # Immediately pinch again within 50ms (< 400ms cooldown)
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03)
    assert clicked is False
    assert len(mock_driver.clicks) == 1
    assert controller.get_status().pinch_state == "cooldown"

    # Simulate passage of 450ms (> 400ms cooldown)
    controller._last_click_time = time.time() - 0.45
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03)
    assert clicked is True
    assert len(mock_driver.clicks) == 2


def test_invalid_landmarks_and_distance_rejection(controller, mock_driver):
    """Invalid coordinates (NaN, Inf, negative) are safely rejected without clicks."""
    controller.start()

    # NaN coordinates
    assert controller.on_landmark_point(float("nan"), 0.5, pinch_distance=0.02) is False
    # Infinite coordinates
    assert controller.on_landmark_point(0.5, float("inf"), pinch_distance=0.02) is False
    # Negative pinch distance
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=-0.5) is False

    assert len(mock_driver.clicks) == 0


def test_stale_tracking_and_loss_protection(controller, mock_driver):
    """Tracking loss disarms clicker and prevents accidental clicks upon hand return."""
    controller.start()

    # Establish tracking
    controller.on_landmark_point(0.5, 0.5, pinch_distance=0.15)
    assert controller.get_status().hand_detected is True

    # Tracking is lost
    controller.on_tracking_loss()
    status = controller.get_status()
    assert status.hand_detected is False
    assert status.pinch_state == "idle"

    # Hand returns ALREADY in a pinched state (e.g. hand entered frame pinching)
    # Safety Rule: must NOT click on re-entry until hand opens first
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03)
    assert clicked is False
    assert len(mock_driver.clicks) == 0

    # User opens hand
    controller.on_landmark_point(0.5, 0.5, pinch_distance=0.15)
    # Now user pinches -> click triggers safely
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 1


def test_camera_disconnect_protection(controller, mock_driver):
    """When camera disconnects or stop is called, no clicks can occur."""
    controller.start()
    controller.stop()
    assert controller.is_enabled is False

    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.02)
    assert clicked is False
    assert len(mock_driver.clicks) == 0
    assert controller.get_status().pinch_state == "disabled"


def test_left_click_disabled_independently(controller, mock_driver):
    """Left click can be disabled independently while mouse movement remains active."""
    controller.start()
    controller.update_settings(left_click_enabled=False)
    status = controller.get_status()
    assert status.enabled is True
    assert status.left_click_enabled is False
    assert status.pinch_state == "disabled"

    # Cursor movement executes normally
    controller.on_landmark_point(0.7, 0.3, pinch_distance=0.02)
    assert len(mock_driver.clicks) == 0

    # Re-enable left click
    controller.update_settings(left_click_enabled=True)
    # Release hand first
    controller.on_landmark_point(0.7, 0.3, pinch_distance=0.15)
    # Now pinch -> click triggers
    assert controller.on_landmark_point(0.7, 0.3, pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 1


def test_repeated_pinch_actions(controller, mock_driver):
    """Execute multiple full pinch-release cycles; each triggers exactly one click."""
    controller.start()

    for i in range(5):
        # Elapse cooldown
        controller._last_click_time = time.time() - 0.5
        # Pinch
        assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is True
        # Release past 0.08
        controller.on_landmark_point(0.5, 0.5, pinch_distance=0.12)

    assert len(mock_driver.clicks) == 5
    assert controller.get_status().click_count == 5


def test_derive_pinch_from_thumb_coordinates(controller, mock_driver):
    """Pinch distance is derived from index tip (L8) and thumb tip (L4) if not supplied."""
    controller.start()

    # Distance between (0.50, 0.50) and (0.52, 0.52) is sqrt(0.02^2 + 0.02^2) = 0.028 (<= 0.05)
    clicked = controller.on_landmark_point(0.50, 0.50, thumb_x=0.52, thumb_y=0.52)
    assert clicked is True
    assert len(mock_driver.clicks) == 1
    assert controller.get_status().pinch_distance is not None
    assert controller.get_status().pinch_distance < 0.035


def test_api_cursor_point_with_pinch(client):
    """Test API endpoint POST /api/v1/mouse/cursor-point with pinch telemetry."""
    # Set mock driver on global singleton for API test
    mock = MockMouseDriver()
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock)
    ctrl.start()

    res = client.post(
        "/api/v1/mouse/cursor-point",
        json={"x": 0.5, "y": 0.5, "pinch_distance": 0.03},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["clicked"] is True
    assert len(mock.clicks) == 1

    ctrl.stop()


def test_api_explicit_click_endpoint(client):
    """Test API endpoint POST /api/v1/mouse/click."""
    mock = MockMouseDriver()
    ctrl = get_mouse_controller()
    ctrl.set_driver(mock)
    ctrl.update_settings(left_click_enabled=True)
    ctrl._last_click_time = 0.0
    ctrl.start()

    res = client.post("/api/v1/mouse/click")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["click_count"] >= 1
    assert len(mock.clicks) == 1

    ctrl.stop()


def test_api_mouse_settings_update_left_click(client):
    """Test API endpoint PUT /api/v1/mouse/settings updating left click parameters."""
    res = client.put(
        "/api/v1/mouse/settings",
        json={
            "left_click_enabled": False,
            "pinch_activation_threshold": 0.04,
            "pinch_release_threshold": 0.09,
            "click_cooldown_ms": 500.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["left_click_enabled"] is False
    assert data["pinch_activation_threshold"] == 0.04
    assert data["pinch_release_threshold"] == 0.09
    assert data["click_cooldown_ms"] == 500.0

    # Reset for other tests
    client.put("/api/v1/mouse/settings", json={"left_click_enabled": True})
