"""
Structured logging configuration for GestureFlow AI backend.

Provides console and file logging with rotation, configurable levels,
and structured formatting.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from app.core.config import settings


# Default log format with module name, level, timestamp
DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: Optional[str] = None, log_dir: Optional[Path] = None) -> None:
    """
    Configure application-wide logging.

    Args:
        log_level: Override log level (defaults to settings.log_level)
        log_dir: Override log directory (defaults to settings.log_dir_path)
    """
    level = getattr(logging, (log_level or settings.log_level).upper())
    log_directory = log_dir or settings.log_dir_path

    # Ensure log directory exists
    log_directory.mkdir(parents=True, exist_ok=True)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to prevent duplicates on re-initialization
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (10MB max, keep 5 backups)
    log_file = log_directory / "gestureflow.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized", extra={"log_level": level, "log_file": str(log_file)})


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)