"""
src/yolo_detect.py
Task 3: Object Detection with YOLOv8
"""

import os
import csv
import glob
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/yolo_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

PERSON_CLASSES = {"person"}
PRODUCT_CLASSES = {
    "bottle", "cup", "bowl", "vase",
    "book", "scissors", "toothbrush",
    "handbag", "backpack", "suitcase",
}

CONFIDENCE_THRESHOLD = 0.35


def classify_image(detected_objects):
    classes = {obj["class_name"] for obj in detected_objects}
    has_person = bool(classes & PERSON_CLASSES)
    has_product = bool(classes & PRODUCT_CLASSES)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"


def extract_message_id_from_path(image_path):
    try:
        return int(Path(image_path).stem)
    except (ValueError, AttributeError):
        return None


def extract_channel_from_path(image_path):
    try:
        parts = Path(image_path).parts
        images_idx = next(i for i, p in enumerate(parts) if p == "images")
        return parts[images_idx + 1]
    except (StopIteration, IndexError):
        return None


def run_detection(images_dir="data/raw/images"):
    from ultralytics import YOLO

    logger.info("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")

    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        image_files.extend(glob.glob(f"{images_dir}/**/{ext}", recursive=True))

    logger.info(f"Found {len(image_files)} image(s) to process.")

    if not image_files:
        logger.warning("No images found. Make sure Task 1 scraper has run.")
        return []

    all_results = []

    for image_path in image_files:
        message_id = extract_message_id_from_path(image_path)
        channel_name = extract_channel_from_path(image_path)
        logger.info(f"Processing: {image_path}")

        try:
            results = model(image_path, verbose=False)
            result = results[0]

            detections = []
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence < CONFIDENCE_THRESHOLD:
                    continue
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                detections.append({
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "class_id": class_id,
                })

            image_category = classify_image(detections)

            if detections:
                for det in detections:
                    all_results.append({
                        "image_path": image_path,
                        "message_id": message_id,
                        "channel_name": channel_name,
                        "detected_class": det["class_name"],
                        "confidence_score": det["confidence"],
                        "image_category": image_category,
                        "total_detections": len(detections),
                        "processed_at": datetime.now().isoformat(),
                    })
            else:
                all_results.append({
                    "image_path": image_path,
                    "message_id": message_id,
                    "channel_name": channel_name,
                    "detected_class": "none",
                    "confidence_score": 0.0,
                    "image_category": "other",
                    "total_detections": 0,
                    "processed_at": datetime.now().isoformat(),
                })

            logger.info(f"  -> {len(detections)} detection(s), category: {image_category}")

        except Exception as e:
            logger.error(f"  Failed to process {image_path}: {e}")

    return all_results


def save_to_csv(results, output_path="data/yolo_detections.csv"):
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = [
        "image_path", "message_id", "channel_name",
        "detected_class", "confidence_score", "image_category",
        "total_detections", "processed_at",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved {len(results)} rows to {output_path}")


def load_to_postgres(results):
    if not results:
        logger.warning("No results to load.")
        return

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
    logger.info("raw.image_detections table ready.")

    rows = [(
        r["image_path"], r["message_id"], r["channel_name"],
        r["detected_class"], r["confidence_score"], r["image_category"],
        r["total_detections"], r["processed_at"],
    ) for r in results]

    psycopg2.extras.execute_values(cur, """
        INSERT INTO raw.image_detections
            (image_path, message_id, channel_name, detected_class,
             confidence_score, image_category, total_detections, processed_at)
        VALUES %s;
    """, rows, page_size=500)

    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Loaded {len(rows)} rows into raw.image_detections.")


def print_summary(results):
    if not results:
        return
    from collections import Counter

    categories = Counter(r["image_category"] for r in results)
    classes = Counter(
        r["detected_class"] for r in results if r["detected_class"] != "none"
    )

    print("\n" + "=" * 50)
    print("YOLO DETECTION SUMMARY")
    print("=" * 50)
    print(f"Total images processed : {len(set(r['image_path'] for r in results))}")
    print(f"Total detection rows   : {len(results)}")
    print("\nImage Categories:")
    for cat, count in categories.most_common():
        print(f"  {cat:<20} {count}")
    print("\nTop Detected Objects:")
    for cls, count in classes.most_common(10):
        print(f"  {cls:<20} {count}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    logger.info("Starting YOLO detection pipeline...")
    results = run_detection("data/raw/images")
    save_to_csv(results, "data/yolo_detections.csv")
    load_to_postgres(results)
    print_summary(results)
    logger.info("YOLO detection pipeline complete.")