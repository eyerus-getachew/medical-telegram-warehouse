"""
src/utils/config.py

Simple configuration for Task 1 (Telegram Scraping).

This file reads environment variables from the .env file
using Pydantic Settings.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Task 1."""

    # Read values from the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ============================
    # Telegram Credentials
    # ============================
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_PHONE: str

    # Comma-separated list of Telegram channel usernames
    TELEGRAM_CHANNELS: str

    @property
    def telegram_channels(self) -> list[str]:
        """
        Convert the comma-separated string from the .env file
        into a Python list.
        """
        return [
            channel.strip()
            for channel in self.TELEGRAM_CHANNELS.split(",")
            if channel.strip()
        ]

    # ============================
    # Project Paths
    # ============================
    RAW_DATA_PATH: Path = Path("data/raw")
    LOG_DIR: Path = Path("logs")

    # ============================
    # Logging
    # ============================
    LOG_LEVEL: str = "INFO"


# Create one settings object that can be imported anywhere
settings = Settings()