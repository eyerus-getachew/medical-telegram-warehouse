"""
src/loaders/raw_loader.py

Save extracted Telegram messages into the raw data lake.

Responsibilities:
- Build the correct file path
- Save messages as JSON

This module DOES NOT:
- Connect to Telegram
- Download images
- Clean the data
"""

from src.utils.file_manager import (
    build_json_path,
    save_json,
)
from src.utils.logger import setup_logger

logger = setup_logger()


def save_raw_messages(
    channel: str,
    scrape_date: str,
    messages: list[dict],
) -> None:
    """
    Save raw Telegram messages as JSON.

    Args:
        channel: Telegram channel username.
        scrape_date: Date partition (YYYY-MM-DD).
        messages: List of extracted messages.
    """

    file_path = build_json_path(channel, scrape_date)

    save_json(messages, file_path)

    logger.info(f"Saved {len(messages)} messages to {file_path}")