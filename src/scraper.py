"""
src/scraper.py

Main scraper for Task 1.

Responsibilities:
- Connect to Telegram
- Scrape all configured channels
- Save raw JSON files
- Log progress
"""

import asyncio
from datetime import datetime

from src.extractors.telegram_client import create_client
from src.extractors.message_extractor import extract_messages
from src.loaders.raw_loader import save_raw_messages
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger()


async def run_scraper():
    """
    Run the complete scraping pipeline.
    """

    client = create_client()

    await client.start(phone=settings.TELEGRAM_PHONE)

    logger.info("Successfully connected to Telegram.")

    try:

        scrape_date = datetime.now().strftime("%Y-%m-%d")

        for channel in settings.telegram_channels:

            logger.info(f"Starting channel: {channel}")

            try:

                messages = await extract_messages(
                    client=client,
                    channel=channel,
                    limit=100,
                )

                save_raw_messages(
                    channel=channel,
                    scrape_date=scrape_date,
                    messages=messages,
                )

                logger.info(f"Finished channel: {channel}")

            except Exception as error:

                logger.error(
                    f"Failed to scrape {channel}: {error}"
                )

    finally:

        await client.disconnect()

        logger.info("Telegram client disconnected.")


if __name__ == "__main__":
    asyncio.run(run_scraper())