"""
src/load_csv_to_postgres.py
Loads existing data/yolo_detections.csv into PostgreSQL raw.image_detections.
"""

import os
import csv
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def load_csv_to_postgres(csv_path="data/yolo_detections.csv"):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "medical_warehouse"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.image_detections (
            id                BIGSERIAL PRIMARY KEY,
            image_path        TEXT,
            message_id        BIGINT,
            channel_name      TEXT,
            detected_class    TEXT,
            confidence_score  NUMERIC(6, 4),
            image_category    TEXT,
            total_detections  INTEGER,
            processed_at      TIMESTAMPTZ,
            loaded_at         TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_detections_message_id
            ON raw.image_detections (message_id);
    """)
    conn.commit()
    print("raw.image_detections table ready.")

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append((
                r["image_path"],
                int(r["message_id"]) if r["message_id"] else None,
                r["channel_name"],
                r["detected_class"],
                float(r["confidence_score"]) if r["confidence_score"] else 0.0,
                r["image_category"],
                int(r["total_detections"]) if r["total_detections"] else 0,
                r["processed_at"],
            ))

    psycopg2.extras.execute_values(cur, """
        INSERT INTO raw.image_detections
            (image_path, message_id, channel_name, detected_class,
             confidence_score, image_category, total_detections, processed_at)
        VALUES %s;
    """, rows, page_size=500)

    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(rows)} rows into raw.image_detections.")


if __name__ == "__main__":
    load_csv_to_postgres()