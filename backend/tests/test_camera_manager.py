"""
Tests for camera manager with mocked OpenCV.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from app.services.camera_manager import CameraManager, CameraState, CameraInfo, CameraStatus


@pytest.fixture
def mock_cv2():
    """Mock OpenCV VideoCapture."""
    with patch('app.services.camera_manager.cv2') as mock_cv2:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.side_effect = lambda prop: {
            3: 640,   # CAP_PROP_FRAME_WIDTH
            4: 480,   # CAP_PROP_FRAME_HEIGHT
            5: 30.0,  # CAP_PROP_FPS
            6: 1400,  # CAP_PROP_BACKEND
        }.get(prop, 0)
        mock_cap.release.return_value = None
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.flip = lambda frame, code: frame
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BACKEND = 6
        mock_cv2.CAP_DSHOW = 1400
        mock_cv2.CAP_V4L2 = 200
        mock_cv2.CAP_MSMF = 1400
        mock_cv2.CAP_ANY = 0
        yield mock_cv2


def test_camera_manager_initialization():
    """Test camera manager initializes correctly."""
    manager = CameraManager()
    assert manager is not None
    status = manager.get_status()
    assert status.state == CameraState.DISCONNECTED
    assert not status.is_capturing


def test_camera_discovery(mock_cv2):
    """Test camera discovery with mocked OpenCV."""
    manager = CameraManager()
    devices = manager.discover_cameras(max_index=3)
    
    assert len(devices) == 3
    for i, device in enumerate(devices):
        assert device.index == i
        assert device.available is True
        assert device.width == 640
        assert device.height == 480
        assert device.fps == 30.0


def test_camera_start_success(mock_cv2):
    """Test successful camera start."""
    manager = CameraManager()
    success = manager.start(camera_index=0)
    
    assert success is True
    assert manager.get_status().state == CameraState.CAPTURING
    assert manager.get_status().is_capturing is True
    assert manager.get_status().actual_width == 640
    assert manager.get_status().actual_height == 480
    assert manager.get_status().actual_fps == 30.0


def test_camera_start_failure(mock_cv2):
    """Test camera start failure handling."""
    mock_cv2.VideoCapture.return_value.isOpened.return_value = False
    
    manager = CameraManager()
    success = manager.start(camera_index=999)
    
    assert success is False
    assert manager.get_status().state == CameraState.ERROR
    assert manager.get_status().last_error is not None


def test_camera_stop(mock_cv2):
    """Test camera stop."""
    manager = CameraManager()
    manager.start()
    assert manager.get_status().is_capturing is True
    
    success = manager.stop()
    
    assert success is True
    assert manager.get_status().state == CameraState.DISCONNECTED
    assert not manager.get_status().is_capturing


def test_camera_stop_idempotent(mock_cv2):
    """Test repeated stop calls don't crash."""
    manager = CameraManager()
    manager.start()
    manager.stop()
    success = manager.stop()  # Second stop
    
    assert success is True


def test_camera_invalid_config():
    """Test invalid camera configuration handling."""
    # Test with invalid camera index in config (handled by validator)
    from app.core.config import Settings
    import os
    
    # Test camera backend validation
    os.environ['CAMERA_BACKEND'] = 'INVALID'
    try:
        with pytest.raises(Exception):
            Settings()
    finally:
        del os.environ['CAMERA_BACKEND']


def test_get_latest_frame(mock_cv2):
    """Test getting latest frame."""
    manager = CameraManager()
    manager.start()
    
    # Wait a bit for frame capture
    import time
    time.sleep(0.2)
    
    frame = manager.get_latest_frame()
    assert frame is not None
    assert frame.shape == (480, 640, 3)
    
    manager.stop()


def test_wait_for_frame(mock_cv2):
    """Test waiting for frame."""
    manager = CameraManager()
    manager.start()
    
    frame = manager.wait_for_frame(timeout=1.0)
    assert frame is not None
    
    manager.stop()


def test_camera_health_check(mock_cv2):
    """Test camera health check."""
    manager = CameraManager()
    assert not manager.is_healthy()
    
    manager.start()
    assert manager.is_healthy()
    
    manager.stop()
    assert not manager.is_healthy()


def test_camera_failure_recovery(mock_cv2):
    """Test camera failure during capture."""
    manager = CameraManager()
    manager.start()
    
    # Simulate camera disconnection
    mock_cv2.VideoCapture.return_value.isOpened.return_value = False
    
    # Try to get frame - should handle gracefully
    frame = manager.get_latest_frame()
    # Frame might still be available from before disconnection
    
    manager.stop()