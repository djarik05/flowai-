"""
Tests for configuration management.
"""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_settings() -> None:
    """Test default configuration values."""
    # Clear environment to test defaults
    env_backup = dict(os.environ)
    for key in list(os.environ.keys()):
        if key.startswith(("APP_", "API_", "LOG_", "CORS_", "FRONTEND_")):
            del os.environ[key]

    try:
        settings = Settings()

        assert settings.app_name == "GestureFlow AI"
        assert settings.app_version == "1.0.0"
        assert settings.environment == "development"
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 8000
        assert settings.api_prefix == "/api/v1"
        assert settings.log_level == "INFO"
        assert settings.log_dir == "logs"
        assert "http://localhost:5173" in settings.cors_allowed_origins
        assert settings.frontend_dev_url == "http://localhost:5173"
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_environment_variable_override() -> None:
    """Test that environment variables override defaults."""
    env_backup = dict(os.environ)
    os.environ.clear()
    os.environ.update({
        "APP_NAME": "Test App",
        "APP_VERSION": "2.0.0",
        "ENVIRONMENT": "production",
        "API_HOST": "0.0.0.0",
        "API_PORT": "9000",
        "API_PREFIX": "/api/v2",
        "LOG_LEVEL": "DEBUG",
        "LOG_DIR": "/custom/logs",
        "CORS_ALLOWED_ORIGINS": "http://example.com,http://test.com",
        "FRONTEND_DEV_URL": "http://example.com",
    })

    try:
        settings = Settings()

        assert settings.app_name == "Test App"
        assert settings.app_version == "2.0.0"
        assert settings.environment == "production"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 9000
        assert settings.api_prefix == "/api/v2"
        assert settings.log_level == "DEBUG"
        assert settings.log_dir == "/custom/logs"
        assert settings.cors_allowed_origins == ["http://example.com", "http://test.com"]
        assert settings.frontend_dev_url == "http://example.com"
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_invalid_environment_rejected() -> None:
    """Test that invalid environment values are rejected."""
    env_backup = dict(os.environ)
    os.environ.clear()
    os.environ["ENVIRONMENT"] = "invalid"

    try:
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "environment" in str(exc_info.value).lower()
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_invalid_log_level_rejected() -> None:
    """Test that invalid log level values are rejected."""
    env_backup = dict(os.environ)
    os.environ.clear()
    os.environ["LOG_LEVEL"] = "INVALID"

    try:
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "log_level" in str(exc_info.value).lower()
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_invalid_port_rejected() -> None:
    """Test that invalid port values are rejected."""
    env_backup = dict(os.environ)
    os.environ.clear()
    os.environ["API_PORT"] = "99999"

    try:
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "api_port" in str(exc_info.value).lower()
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_cors_origins_parsing() -> None:
    """Test CORS origins parsing from string and list."""
    env_backup = dict(os.environ)
    os.environ.clear()

    # Test string parsing
    os.environ["CORS_ALLOWED_ORIGINS"] = "http://a.com, http://b.com ,http://c.com"
    try:
        settings = Settings()
        assert settings.cors_allowed_origins == ["http://a.com", "http://b.com", "http://c.com"]
    finally:
        os.environ.clear()
        os.environ.update(env_backup)

    # Test empty string handling
    os.environ.clear()
    os.environ["CORS_ALLOWED_ORIGINS"] = ""
    try:
        settings = Settings()
        assert settings.cors_allowed_origins == []
    finally:
        os.environ.clear()
        os.environ.update(env_backup)

    # Test default value
    os.environ.clear()
    try:
        settings = Settings()
        assert "http://localhost:5173" in settings.cors_allowed_origins
        assert "http://127.0.0.1:5173" in settings.cors_allowed_origins
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_api_url_property() -> None:
    """Test api_url property constructs correct URL."""
    env_backup = dict(os.environ)
    os.environ.clear()
    os.environ.update({
        "API_HOST": "127.0.0.1",
        "API_PORT": "8000",
        "API_PREFIX": "/api/v1",
    })

    try:
        settings = Settings()
        assert settings.api_url == "http://127.0.0.1:8000/api/v1"
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_log_dir_path_property() -> None:
    """Test log_dir_path returns Path object."""
    env_backup = dict(os.environ)
    os.environ.clear()
    os.environ["LOG_DIR"] = "custom_logs"

    try:
        settings = Settings()
        assert isinstance(settings.log_dir_path, Path)
        assert settings.log_dir_path.name == "custom_logs"
    finally:
        os.environ.clear()
        os.environ.update(env_backup)