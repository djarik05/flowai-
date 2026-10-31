"""
Pytest configuration for GestureFlow AI backend tests.

Provides fixtures and configuration for the test suite.
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure backend directory is in Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    # Set test environment
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOG_DIR"] = "test_logs"

    yield

    # Cleanup test logs after tests
    test_log_dir = Path("test_logs")
    if test_log_dir.exists():
        import shutil
        shutil.rmtree(test_log_dir, ignore_errors=True)