"""
Common utilities for the PDF to EPUB Converter project.
Contains logging helpers, path manipulation, and global constants.
"""

import logging
import os
from pathlib import Path

# Global Constants
VERSION = "0.1.0"
DEFAULT_ENCODING = "utf-8"
DEFAULT_CHUNK_SIZE = 600
DEFAULT_OVERLAP = 100


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    The log level is determined by the LOG_LEVEL environment variable (default: INFO).
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        # Fallback to INFO if invalid level provided
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes this file is located in <root>/claude-skill/core/utils.py
    """
    # utils.py -> core -> claude-skill -> root
    return Path(__file__).resolve().parent.parent.parent


def ensure_dir(path: Path) -> None:
    """
    Ensures that a directory exists at the given path.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        get_logger(__name__).info(f"Created directory: {path}")
