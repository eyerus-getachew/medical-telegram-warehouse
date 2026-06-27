"""
src/utils/logger.py

This module configures the project's logging system.

It creates:
- A log file: logs/scraper.log
- Console output so you can see logs while running the scraper

All other modules can import this logger.
"""

import logging
from pathlib import Path

from src.utils.config import settings


def setup_logger(name: str = "medical_scraper") -> logging.Logger:
    """
    Create and configure a logger.

    Args:
        name (str): Name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """

    # Ensure the logs directory exists
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = settings.LOG_DIR / "scraper.log"

    logger = logging.getLogger(name)

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    # Format for log messages
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Write logs to a file
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Print logs to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger