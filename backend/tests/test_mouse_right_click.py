"""
Automated Unit Tests for Phase 6B.2 Gesture-Based Right Click.

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


def test_right_click_defaults_and_settings(controller):
    """Verify Phase 6B.2 default settings for gesture right click."""
    status = controller.get_status()
    assert status.right_click_enabled is True
    assert status.right_pinch_activation_threshold == 0.05
    assert status.right_pinch_release_threshold == 0.08
    assert status.right_click_cooldown_ms == 500.0
    assert status.right_pinch_state == "disabled"  # Controller disabled by default
    assert status.right_click_count == 0
    assert status.last_right_click_time is None
    assert status.last_right_click_position is None


def test_right_pinch_detection_triggers_right_click(controller, mock_driver):
    """Middle-finger pinch distance below activation threshold triggers exactly one right click."""
    controller.start()
    assert controller.is_enabled is True

    # Feed index fingertip at screen center with middle-finger right pinch distance 0.03 (<= 0.05)
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.03)

    assert clicked is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"
    status = controller.get_status()
    assert status.right_click_count == 1
    assert status.last_right_click_time is not None
    assert status.right_pinch_state == "pinched"
    assert status.right_pinch_distance == 0.03


def test_right_activation_threshold_boundary(controller, mock_driver):
    """Right click only triggers when middle-finger pinch distance <= right_pinch_activation_threshold (0.05)."""
    controller.start()

    # Distance 0.051 (> 0.050) -> No click
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.051)
    assert clicked is False
    assert len(mock_driver.clicks) == 0

    # Distance 0.050 (<= 0.050) -> Click triggers
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.050)
    assert clicked is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"


def test_right_hysteresis_and_release_threshold(controller, mock_driver):
    """
    Hysteresis test for right click:
    After right pinch triggers at <= 0.05, middle finger must open past release threshold (>= 0.08)
    before another right click can be triggered.
    """
    controller.start()
    # Click 1 triggered
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 1

    # Distance increases to 0.065 (between activation 0.05 and release 0.08 - deadband)
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.065)
    assert clicked is False
    assert len(mock_driver.clicks) == 1

    # Hand pinches again to 0.03 WITHOUT having released past 0.08 -> NO click
    # Simulating time passage past cooldown
    controller._last_right_click_time = time.time() - 1.0  # Cooldown elapsed
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.03)
    assert clicked is False
    assert len(mock_driver.clicks) == 1

    # Hand releases past release threshold (>= 0.08)
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.10)
    assert clicked is False
    assert controller._awaiting_right_pinch_release is False

    # Now pinch again at 0.03 -> Click 2 triggers!
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.03)
    assert clicked is True
    assert len(mock_driver.clicks) == 2
    assert mock_driver.clicks[1]["button"] == "right"


def test_one_click_per_right_pinch_no_repeated_clicks_while_holding(controller, mock_driver):
    """Holding middle-finger pinch continuously across multiple frames must NOT spam right clicks."""
    controller.start()

    # Frame 1: Pinch down -> Click 1
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02) is True
    assert len(mock_driver.clicks) == 1

    # Frames 2-5: Hold pinch down across multiple frames (simulate holding for 1s)
    for _ in range(5):
        time.sleep(0.01)
        controller._last_right_click_time = time.time() - 2.0  # Even past cooldown
        assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02) is False

    # Still exactly one click
    assert len(mock_driver.clicks) == 1
    assert controller.get_status().right_click_count == 1
    assert controller.get_status().right_pinch_state == "pinched"


def test_right_click_cooldown_debouncing(controller, mock_driver):
    """Rapid right pinch releases and re-activations within 500ms cooldown window are debounced."""
    controller.start()
    controller.update_settings(right_click_cooldown_ms=500.0)

    # Click 1
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02) is True
    assert len(mock_driver.clicks) == 1

    # Immediate release
    controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.15)
    assert controller._awaiting_right_pinch_release is False

    # Attempt second click immediately (cooldown NOT elapsed)
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02)
    assert clicked is False
    assert len(mock_driver.clicks) == 1
    assert controller.get_status().right_pinch_state == "cooldown"

    # Fast forward past cooldown (500ms)
    controller._last_right_click_time = time.time() - 0.6
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02)
    assert clicked is True
    assert len(mock_driver.clicks) == 2


def test_mutual_exclusion_between_left_and_right_pinch(controller, mock_driver):
    """
    Mutual Exclusion:
    If both index pinch (L4+L8) and middle pinch (L4+L12) are activated simultaneously (e.g. closing into a fist),
    NEITHER click should fire, preventing accidental double-clicks or spurious triggers.
    """
    controller.start()

    # Both pinches active simultaneously (e.g. fist gesture: pinch=0.03, right_pinch=0.03)
    clicked = controller.on_landmark_point(
        0.5,
        0.5,
        pinch_distance=0.03,
        right_pinch_distance=0.03,
    )

    assert clicked is False
    assert len(mock_driver.clicks) == 0
    assert controller._awaiting_pinch_release is True
    assert controller._awaiting_right_pinch_release is True

    # Releasing both past release threshold resets both latches
    controller.on_landmark_point(0.5, 0.5, pinch_distance=0.12, right_pinch_distance=0.12)
    assert controller._awaiting_pinch_release is False
    assert controller._awaiting_right_pinch_release is False

    # Now activating ONLY right pinch triggers right click cleanly
    clicked = controller.on_landmark_point(0.5, 0.5, pinch_distance=0.12, right_pinch_distance=0.03)
    assert clicked is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"


def test_independent_left_and_right_click_enabling(controller, mock_driver):
    """Left click and Right click can be toggled independently."""
    controller.start()

    # Disable left click, keep right click enabled
    controller.update_settings(left_click_enabled=False, right_click_enabled=True)
    assert controller.get_status().left_click_enabled is False
    assert controller.get_status().right_click_enabled is True

    # Index pinch does NOT fire
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is False
    assert len(mock_driver.clicks) == 0

    # Middle pinch DOES fire
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"

    # Now disable right click, enable left click
    controller.update_settings(left_click_enabled=True, right_click_enabled=False)
    assert controller.get_status().left_click_enabled is True
    assert controller.get_status().right_click_enabled is False

    # Middle pinch does NOT fire
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02) is False
    assert len(mock_driver.clicks) == 1

    # Index pinch DOES fire
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is True
    assert len(mock_driver.clicks) == 2
    assert mock_driver.clicks[1]["button"] == "left"


def test_invalid_landmarks_and_right_distance_rejection(controller, mock_driver):
    """Invalid, NaN, infinite, or negative coordinates/distances are safely rejected."""
    controller.start()

    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=-0.05) is False
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=float("nan")) is False
    assert controller.on_landmark_point(0.5, 0.5, right_pinch_distance=float("inf")) is False
    assert controller.on_landmark_point(float("nan"), 0.5, right_pinch_distance=0.03) is False
    assert len(mock_driver.clicks) == 0


def test_stale_tracking_and_loss_protection(controller, mock_driver):
    """Tracking loss resets right pinch and requires gesture release before re-triggering."""
    controller.start()

    # Tracking drops
    controller.on_tracking_loss()
    status = controller.get_status()
    assert status.hand_detected is False
    assert controller._awaiting_right_pinch_release is True

    # Hand reappears in an already pinched pose (distance 0.02) -> Must NOT trigger immediate click!
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.02)
    assert clicked is False
    assert len(mock_driver.clicks) == 0

    # Hand opens (releases)
    controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.12)
    assert controller._awaiting_right_pinch_release is False

    # Intentional pinch now triggers click
    clicked = controller.on_landmark_point(0.5, 0.5, right_pinch_distance=0.03)
    assert clicked is True
    assert len(mock_driver.clicks) == 1


def test_derive_right_pinch_from_thumb_and_middle_coordinates(controller, mock_driver):
    """Pinch distance is accurately calculated from raw thumb and middle fingertip coordinates."""
    controller.start()

    # Index finger extended at (0.80, 0.80); Thumb at (0.50, 0.50), Middle at (0.52, 0.50) -> Distance = 0.02 (<= 0.05)
    clicked = controller.on_landmark_point(
        0.8,
        0.8,
        thumb_x=0.50,
        thumb_y=0.50,
        middle_x=0.52,
        middle_y=0.50,
    )
    assert clicked is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"
    assert pytest.approx(controller.get_status().right_pinch_distance, 0.001) == 0.02


def test_api_cursor_point_with_right_pinch(client):
    """FastAPI cursor-point endpoint accepts right pinch distance and middle finger coordinates."""
    ctrl = get_mouse_controller()
    mock_drv = MockMouseDriver()
    ctrl.set_driver(mock_drv)
    ctrl.start()
    ctrl.update_settings(right_click_enabled=True)

    try:
        # Feed point with right pinch distance
        res = client.post(
            "/api/v1/mouse/cursor-point",
            json={
                "x": 0.5,
                "y": 0.5,
                "right_pinch_distance": 0.03,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(mock_drv.clicks) == 1
        assert mock_drv.clicks[0]["button"] == "right"
    finally:
        ctrl.stop()


def test_api_explicit_right_click_endpoint(client):
    """FastAPI click-right endpoint triggers right click immediately."""
    ctrl = get_mouse_controller()
    mock_drv = MockMouseDriver()
    ctrl.set_driver(mock_drv)
    ctrl.start()
    ctrl.update_settings(right_click_enabled=True)
    ctrl._last_right_click_time = 0.0

    try:
        res = client.post("/api/v1/mouse/click-right")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["right_click_count"] >= 1
        assert len(mock_drv.clicks) == 1
        assert mock_drv.clicks[0]["button"] == "right"
    finally:
        ctrl.stop()


def test_api_mouse_settings_update_right_click(client):
    """PUT /api/v1/mouse/settings updates Phase 6B.2 configuration."""
    ctrl = get_mouse_controller()
    try:
        res = client.put(
            "/api/v1/mouse/settings",
            json={
                "right_click_enabled": False,
                "right_pinch_activation_threshold": 0.06,
                "right_pinch_release_threshold": 0.09,
                "right_click_cooldown_ms": 600.0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["right_click_enabled"] is False
        assert data["right_pinch_activation_threshold"] == 0.06
        assert data["right_pinch_release_threshold"] == 0.09
        assert data["right_click_cooldown_ms"] == 600.0
    finally:
        # Reset settings
        ctrl.update_settings(
            right_click_enabled=True,
            right_pinch_activation_threshold=0.05,
            right_pinch_release_threshold=0.08,
            right_click_cooldown_ms=500.0,
        )
