"""
src/load_to_postgres.py
Reads JSON files from the data lake and loads them into PostgreSQL raw schema.
"""

import os
import json
import glob
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/load_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "medical_warehouse"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS raw;"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS raw.telegram_messages (
    id                BIGSERIAL PRIMARY KEY,
    message_id        BIGINT,
    channel_name      TEXT,
    message_date      TIMESTAMPTZ,
    message_text      TEXT,
    has_media         BOOLEAN,
    image_path        TEXT,
    views             INTEGER,
    forwards          INTEGER,
    raw_json          JSONB,
    loaded_at         TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_UNIQUE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_msg_channel
    ON raw.telegram_messages (message_id, channel_name);
"""


def load_json_files(data_lake_path="data/raw/telegram_messages"):
    json_files = glob.glob(f"{data_lake_path}/**/*.json", recursive=True)
    logger.info(f"Found {len(json_files)} JSON file(s) to load.")

    if not json_files:
        logger.warning("No JSON files found. Make sure scraper has run first.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(CREATE_SCHEMA)
    cur.execute(CREATE_TABLE)
    cur.execute(CREATE_UNIQUE_INDEX)
    conn.commit()
    logger.info("raw.telegram_messages table is ready.")

    total_inserted = 0
    total_skipped = 0

    for filepath in json_files:
        logger.info(f"Processing: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                records = json.load(f)

            if not isinstance(records, list):
                records = [records]

            rows = []
            for rec in records:
                rows.append((
                    rec.get("message_id"),
                    rec.get("channel_name"),
                    rec.get("message_date"),
                    rec.get("message_text"),
                    rec.get("has_media", False),
                    rec.get("image_path"),
                    rec.get("views", 0),
                    rec.get("forwards", 0),
                    json.dumps(rec),
                ))

            insert_sql = """
                INSERT INTO raw.telegram_messages
                    (message_id, channel_name, message_date, message_text,
                     has_media, image_path, views, forwards, raw_json)
                VALUES %s
                ON CONFLICT (message_id, channel_name) DO NOTHING;
            """
            psycopg2.extras.execute_values(cur, insert_sql, rows, page_size=500)
            conn.commit()

            inserted = cur.rowcount if cur.rowcount != -1 else len(rows)
            skipped = len(rows) - inserted
            total_inserted += inserted
            total_skipped += skipped
            logger.info(f"Inserted {inserted}, skipped {skipped} duplicates.")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to load {filepath}: {e}")

    cur.close()
    conn.close()
    logger.info(f"Load complete. Inserted: {total_inserted}, skipped: {total_skipped}.")


if __name__ == "__main__":
    load_json_files()