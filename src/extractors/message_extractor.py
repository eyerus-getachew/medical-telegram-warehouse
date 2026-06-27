"""
src/extractors/message_extractor.py

Extract messages from a Telegram channel.

Responsibilities:
- Read messages from a Telegram channel
- Extract the required fields
- Download images (if present)
- Return a list of dictionaries

This module DOES NOT:
- Save JSON files
- Save data to a database
"""

from telethon import TelegramClient

from src.loaders.image_downloader import download_image
from src.utils.logger import setup_logger

logger = setup_logger()


async def extract_messages(
    client: TelegramClient,
    channel: str,
    limit: int = 100,
) -> list[dict]:
    """
    Extract messages from a Telegram channel.

    Args:
        client: Connected Telethon client.
        channel: Telegram channel username.
        limit: Number of latest messages to retrieve.

    Returns:
        List of dictionaries containing message information.
    """

    logger.info(f"Started scraping channel: {channel}")

    messages = []

    async for message in client.iter_messages(channel, limit=limit):

        # Default image path
        image_path = None

        # Download image if the message contains a photo
        if message.photo:
            image_path = await download_image(
                client=client,
                message=message,
                channel_name=channel,
            )

        # Store only the required fields
        messages.append(
            {
                "message_id": message.id,
                "channel_name": channel,
                "message_date": (
                    message.date.isoformat()
                    if message.date
                    else None
                ),
                "message_text": message.text,
                "has_media": message.photo is not None,
                "image_path": image_path,
                "views": message.views,
                "forwards": message.forwards,
            }
        )

    logger.info(
        f"Collected {len(messages)} messages from {channel}"
    )

    return messages