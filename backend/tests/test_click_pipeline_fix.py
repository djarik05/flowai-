"""
Tests for Left Click and Right Click Pipeline Bug Fix.
Verifies:
1. Mock OS mouse driver safety (never triggers real clicks during tests).
2. Worker thread queue execution of left and right clicks.
3. Explicit click triggering and cooldown latching.
4. Independent enable/disable states for left and right click.
5. Protection against stale landmarks, loss of tracking, and mutual exclusion.
"""

import time
import pytest
from app.services.mouse_controller import (
    MouseController,
    MockMouseDriver,
    MouseDriver,
)


@pytest.fixture
def mock_driver() -> MockMouseDriver:
    return MockMouseDriver(screen_width=1920, screen_height=1080)


@pytest.fixture
def controller(mock_driver: MockMouseDriver) -> MouseController:
    ctrl = MouseController(driver=mock_driver)
    ctrl.initialize()
    return ctrl


def test_click_pipeline_left_click_execution(controller: MouseController, mock_driver: MockMouseDriver):
    """Verify left click triggers cleanly through controller."""
    controller.start()
    assert controller.is_enabled is True

    # Initial position feed
    controller.on_landmark_point(0.5, 0.5)
    assert len(mock_driver.clicks) == 0

    # Explicit left click
    success = controller.trigger_left_click()
    assert success is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "left"
    assert mock_driver.clicks[0]["pos"] == (960, 540)

    # Cooldown blocks immediate re-click
    assert controller.trigger_left_click() is False
    assert len(mock_driver.clicks) == 1


def test_click_pipeline_right_click_execution(controller: MouseController, mock_driver: MockMouseDriver):
    """Verify right click triggers cleanly through controller."""
    controller.start()
    assert controller.is_enabled is True

    # Initial position feed
    controller.on_landmark_point(0.3, 0.4)
    assert len(mock_driver.clicks) == 0

    # Explicit right click
    success = controller.trigger_right_click()
    assert success is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"

    # Cooldown blocks immediate re-click
    assert controller.trigger_right_click() is False
    assert len(mock_driver.clicks) == 1


def test_click_pipeline_independent_enable_disable(controller: MouseController, mock_driver: MockMouseDriver):
    """Verify left and right clicks respect their independent enable/disable settings."""
    controller.start()

    # Disable left click only
    controller.update_settings(left_click_enabled=False, right_click_enabled=True)
    assert controller.trigger_left_click() is False
    assert controller.trigger_right_click() is True
    assert len(mock_driver.clicks) == 1
    assert mock_driver.clicks[0]["button"] == "right"

    # Reset cooldown and swap settings
    controller._last_right_click_time = time.time() - 1.0
    controller.update_settings(left_click_enabled=True, right_click_enabled=False)
    assert controller.trigger_right_click() is False
    assert controller.trigger_left_click() is True
    assert len(mock_driver.clicks) == 2
    assert mock_driver.clicks[1]["button"] == "left"


def test_click_pipeline_tracking_loss_disarms_click(controller: MouseController, mock_driver: MockMouseDriver):
    """Verify tracking loss immediately halts and disarms click triggering."""
    controller.start()
    controller.on_landmark_point(0.5, 0.5, pinch_distance=0.15)
    assert controller.get_status().hand_detected is True

    controller.on_tracking_loss()
    assert controller.get_status().hand_detected is False

    # Attempt pinch while tracking is lost
    assert controller.on_landmark_point(0.5, 0.5, pinch_distance=0.03) is False
    assert len(mock_driver.clicks) == 0


def test_click_pipeline_mutual_exclusion(controller: MouseController, mock_driver: MockMouseDriver):
    """Simultaneous left and right pinches must be suppressed to prevent accidental triggers."""
    controller.start()

    # Both below 0.05 simultaneously (e.g. closed fist)
    triggered = controller.on_landmark_point(
        0.5, 0.5,
        pinch_distance=0.03,
        right_pinch_distance=0.03
    )
    assert triggered is False
    assert len(mock_driver.clicks) == 0
