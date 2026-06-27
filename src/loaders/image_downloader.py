"""
src/loaders/image_downloader.py

Download images from Telegram messages.

Responsibilities:
- Download photos from Telegram
- Save them to:
  data/raw/images/{channel_name}/{message_id}.jpg

This module DOES NOT:
- Extract messages
- Save JSON
"""

from pathlib import Path

from telethon import TelegramClient

from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger()


async def download_image(
    client: TelegramClient,
    message,
    channel_name: str,
) -> str | None:
    """
    Download an image from a Telegram message.

    Args:
        client: Connected Telegram client.
        message: Telethon Message object.
        channel_name: Telegram channel username.

    Returns:
        Image path if downloaded, otherwise None.
    """

    # Skip messages without media
    if message.photo is None:
        return None

    # Create channel folder
    image_dir = (
        settings.RAW_DATA_PATH
        / "images"
        / channel_name
    )

    image_dir.mkdir(parents=True, exist_ok=True)

    image_path = image_dir / f"{message.id}.jpg"

    try:
        await client.download_media(
            message,
            file=image_path,
        )

        logger.info(f"Downloaded image: {image_path}")

        return str(image_path)

    except Exception as error:
        logger.error(
            f"Failed to download image "
            f"{message.id}: {error}"
        )

        return None