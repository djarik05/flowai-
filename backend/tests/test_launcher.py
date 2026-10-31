"""
Unit tests for GestureFlow AI Unified Launcher (Phase 6A.3).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure root directory is in path to import run.py
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import run


def test_find_python_interpreter():
    """Verify launcher locates a valid Python executable."""
    py_exe = run.find_python_interpreter()
    assert py_exe is not None
    assert Path(py_exe).exists()


def test_is_port_in_use():
    """Verify port detection with open/closed ports."""
    # Test on an unlikely port
    assert run.is_port_in_use("127.0.0.1", 59999) is False


def test_check_backend_health_mock():
    """Verify check_backend_health parses health payload correctly."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"status": "ok", "application": "GestureFlow AI"}'
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        healthy, payload = run.check_backend_health("http://127.0.0.1:8000")
        assert healthy is True
        assert payload["status"] == "ok"
        assert payload["application"] == "GestureFlow AI"


def test_check_backend_health_failure():
    """Verify check_backend_health handles offline or mismatched service."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        healthy, payload = run.check_backend_health("http://127.0.0.1:8000")
        assert healthy is False
        assert payload is None


def test_check_backend_health_mismatched_app():
    """Verify check_backend_health rejects an unrelated service on port 8000."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"status": "ok", "application": "SomeOtherApp"}'
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        healthy, payload = run.check_backend_health("http://127.0.0.1:8000")
        assert healthy is False


def test_check_frontend_ready():
    """Verify check_frontend_ready with 200 and errors."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        assert run.check_frontend_ready("http://localhost:5173") is True

    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        assert run.check_frontend_ready("http://localhost:5173") is False


def test_terminate_process_tree_graceful():
    """Verify terminate_process_tree handles dead process safely."""
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 0
    # Should return cleanly without exceptions
    run.terminate_process_tree(mock_proc)
    run.terminate_process_tree(None)
