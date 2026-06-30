"""
pipeline.py
Task 5: Dagster orchestration for the medical Telegram data pipeline.

Run with:
    dagster dev -f pipeline.py
UI available at:
    http://localhost:3000
"""

import subprocess
import sys
from pathlib import Path

from dagster import (
    op, job, OpExecutionContext, Definitions,
    ScheduleDefinition, DefaultScheduleStatus,
    Failure, RetryPolicy,
)

PROJECT_ROOT = Path(__file__).parent
DBT_PROJECT_DIR = PROJECT_ROOT / "medical_warehouse"


def _run_subprocess(context: OpExecutionContext, cmd: list[str], cwd: Path = None):
    context.log.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        context.log.info(result.stdout)
    if result.stderr:
        context.log.info(result.stderr)

    if result.returncode != 0:
        raise Failure(
            description=f"Command failed with exit code {result.returncode}: {' '.join(cmd)}",
            metadata={"stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]},
        )
    return result


@op(
    name="scrape_telegram_data",
    description="Connects to Telegram via Telethon and scrapes configured channels into the data lake.",
    retry_policy=RetryPolicy(max_retries=1, delay=10),
)
def scrape_telegram_data(context: OpExecutionContext) -> bool:
    _run_subprocess(context, [sys.executable, "-m", "src.scraper"])
    context.log.info("Telegram scraping complete.")
    return True


@op(
    name="load_raw_to_postgres",
    description="Reads JSON files from the data lake and loads them into raw.telegram_messages.",
)
def load_raw_to_postgres(context: OpExecutionContext, upstream_ok: bool) -> bool:
    _run_subprocess(context, [sys.executable, "src/load_to_postgres.py"])
    context.log.info("Raw data loaded into PostgreSQL.")
    return True


@op(
    name="run_yolo_enrichment",
    description="Runs YOLOv8 object detection on downloaded images and loads results into raw.image_detections.",
)
def run_yolo_enrichment(context: OpExecutionContext, upstream_ok: bool) -> bool:
    _run_subprocess(context, [sys.executable, "src/yolo_detect.py"])
    context.log.info("YOLO enrichment complete.")
    return True


@op(
    name="run_dbt_transformations",
    description="Runs dbt models (staging + marts) and dbt tests against the warehouse.",
)
def run_dbt_transformations(context: OpExecutionContext, raw_ok: bool, yolo_ok: bool) -> bool:
    _run_subprocess(context, ["dbt", "run"], cwd=DBT_PROJECT_DIR)
    _run_subprocess(context, ["dbt", "test"], cwd=DBT_PROJECT_DIR)
    context.log.info("dbt transformations and tests complete.")
    return True


@job(
    name="medical_telegram_pipeline",
    description=(
        "End-to-end ELT pipeline: scrape Telegram -> load raw data -> "
        "enrich with YOLO -> transform with dbt."
    ),
)
def medical_telegram_pipeline():
    scraped = scrape_telegram_data()
    raw_loaded = load_raw_to_postgres(scraped)
    yolo_done = run_yolo_enrichment(scraped)
    run_dbt_transformations(raw_loaded, yolo_done)


daily_schedule = ScheduleDefinition(
    job=medical_telegram_pipeline,
    cron_schedule="0 6 * * *",
    name="daily_medical_telegram_pipeline",
    default_status=DefaultScheduleStatus.STOPPED,
    description="Runs the full pipeline daily at 6:00 AM.",
)


defs = Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_schedule],
)