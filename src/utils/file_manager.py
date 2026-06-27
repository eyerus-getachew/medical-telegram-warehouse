"""
src/utils/file_manager.py

Utility functions for creating directories and saving
raw Telegram data as JSON files.
"""

import json
from pathlib import Path
from typing import Any

from src.utils.config import settings


def ensure_directory(path: Path) -> None:
    """
    Create a directory if it does not already exist.

    Args:
        path (Path): Directory path.
    """
    path.mkdir(parents=True, exist_ok=True)


def save_json(data: Any, file_path: Path) -> None:
    """
    Save data as a JSON file.

    Args:
        data: Python object (list or dictionary).
        file_path (Path): Destination JSON file.
    """

    # Make sure the parent directory exists
    ensure_directory(file_path.parent)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )


def build_json_path(channel_name: str, date: str) -> Path:
    """
    Build the JSON output path.

    Example:
    data/raw/telegram_messages/2025-06-27/chemed.json

    Args:
        channel_name (str): Telegram channel name.
        date (str): Date in YYYY-MM-DD format.

    Returns:
        Path
    """

    safe_channel_name = channel_name.replace(" ", "_").lower()

    return (
        settings.RAW_DATA_PATH
        / "telegram_messages"
        / date
        / f"{safe_channel_name}.json"
    )