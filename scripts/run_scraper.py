"""
scripts/run_scraper.py

Entry point for running the Telegram scraper.
"""
"""
scripts/run_scraper.py

Entry point for the Telegram scraper.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python's path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.scraper import run_scraper


if __name__ == "__main__":
    print("Starting Telegram scraper...")
    asyncio.run(run_scraper())
    print("Scraping completed!")
import asyncio

from src.scraper import run_scraper


if __name__ == "__main__":
    print("Starting Telegram scraper...")
    asyncio.run(run_scraper())
    print("Scraping completed!")