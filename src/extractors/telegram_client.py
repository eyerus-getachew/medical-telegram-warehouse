"""
src/extractors/telegram_client.py

Creates and manages the Telegram client connection.
"""

from telethon import TelegramClient

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger()


def create_client() -> TelegramClient:
    """
    Create a Telegram client.

    Returns:
        TelegramClient: Configured Telethon client.
    """

    logger.info("Creating Telegram client...")

    client = TelegramClient(
        session="session_files/medical_scraper",
        api_id=settings.TELEGRAM_API_ID,
        api_hash=settings.TELEGRAM_API_HASH,
    )

    return client