"""
api/main.py
Task 4: Analytical API exposing the dbt-built data warehouse marts.

Run with:
    uvicorn api.main:app --reload
Docs available at:
    http://127.0.0.1:8000/docs
"""

import re
from collections import Counter

from fastapi import FastAPI, Depends, HTTPException, Query, Path
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import (
    TopProduct, TopProductsResponse,
    ChannelActivitySummary, DailyActivity, ChannelActivityResponse,
    MessageResult, MessageSearchResponse,
    ChannelVisualStats, VisualContentResponse,
)

app = FastAPI(
    title="Ethiopian Medical Telegram Analytics API",
    description=(
        "Analytical REST API exposing insights from the medical_warehouse "
        "data warehouse, built on top of Telegram-scraped data from Ethiopian "
        "medical, pharmaceutical, and cosmetics channels."
    ),
    version="1.0.0",
)

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "for", "of", "in",
    "on", "at", "and", "or", "with", "this", "that", "it", "as", "by",
    "from", "be", "we", "you", "your", "our", "us", "have", "has", "will",
    "available", "price", "etb", "call", "now", "new", "please", "contact",
    "more", "info", "information", "order", "free", "delivery",
}


@app.get(
    "/api/reports/top-products",
    response_model=TopProductsResponse,
    summary="Top mentioned products/terms",
    description="Returns the most frequently mentioned terms/products across all channels.",
    tags=["Reports"],
)
def top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top terms to return"),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT message_text
        FROM public_marts.fct_messages
        WHERE message_text IS NOT NULL
    """)).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No message data found.")

    word_counts = Counter()
    for (text_content,) in rows:
        words = re.findall(r"[a-zA-Z]{3,}", text_content.lower())
        for w in words:
            if w not in STOPWORDS:
                word_counts[w] += 1

    top = word_counts.most_common(limit)
    products = [TopProduct(term=term, mention_count=count) for term, count in top]

    return TopProductsResponse(limit=limit, total_results=len(products), products=products)


@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=ChannelActivityResponse,
    summary="Channel posting activity",
    description="Returns summary statistics and daily posting activity trends for a specific channel.",
    tags=["Channels"],
    responses={404: {"description": "Channel not found"}},
)
def channel_activity(
    channel_name: str = Path(..., description="Telegram channel handle, e.g. tikvahpharma"),
    db: Session = Depends(get_db),
):
    summary_row = db.execute(text("""
        SELECT channel_name, channel_type, total_posts, avg_views,
               first_post_date, last_post_date
        FROM public_marts.dim_channels
        WHERE channel_name = :channel_name
    """), {"channel_name": channel_name}).fetchone()

    if not summary_row:
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found.")

    summary = ChannelActivitySummary(
        channel_name=summary_row.channel_name,
        channel_type=summary_row.channel_type,
        total_posts=summary_row.total_posts,
        avg_views=float(summary_row.avg_views or 0),
        first_post_date=summary_row.first_post_date,
        last_post_date=summary_row.last_post_date,
    )

    daily_rows = db.execute(text("""
        SELECT
            d.full_date::text AS date,
            COUNT(f.message_id) AS message_count,
            COALESCE(SUM(f.views), 0) AS total_views
        FROM public_marts.fct_messages f
        JOIN public_marts.dim_dates d ON d.date_key = f.date_key
        WHERE f.channel_name = :channel_name
        GROUP BY d.full_date
        ORDER BY d.full_date
    """), {"channel_name": channel_name}).fetchall()

    daily_activity = [
        DailyActivity(date=r.date, message_count=r.message_count, total_views=r.total_views)
        for r in daily_rows
    ]

    return ChannelActivityResponse(channel=summary, daily_activity=daily_activity)


@app.get(
    "/api/search/messages",
    response_model=MessageSearchResponse,
    summary="Search messages by keyword",
    description="Searches message text across all channels for a given keyword (case-insensitive).",
    tags=["Search"],
)
def search_messages(
    query: str = Query(..., min_length=2, description="Keyword to search for, e.g. 'paracetamol'"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT message_id, channel_name, message_text, message_date,
               views, forwards, has_image
        FROM public_marts.fct_messages
        WHERE message_text ILIKE :pattern
        ORDER BY message_date DESC
        LIMIT :limit
    """), {"pattern": f"%{query}%", "limit": limit}).fetchall()

    messages = [
        MessageResult(
            message_id=r.message_id,
            channel_name=r.channel_name,
            message_text=r.message_text,
            message_date=r.message_date,
            views=r.views,
            forwards=r.forwards,
            has_image=r.has_image,
        )
        for r in rows
    ]

    return MessageSearchResponse(query=query, limit=limit, total_results=len(messages), messages=messages)


@app.get(
    "/api/reports/visual-content",
    response_model=VisualContentResponse,
    summary="Visual content statistics by channel",
    description="Returns image usage statistics for each channel, including YOLO-detected category breakdown.",
    tags=["Reports"],
)
def visual_content_stats(db: Session = Depends(get_db)):
    base_rows = db.execute(text("""
        SELECT
            channel_name,
            COUNT(*) AS total_messages,
            SUM(CASE WHEN has_image THEN 1 ELSE 0 END) AS messages_with_images
        FROM public_marts.fct_messages
        GROUP BY channel_name
    """)).fetchall()

    category_rows = db.execute(text("""
        SELECT
            channel_name,
            image_category,
            COUNT(DISTINCT message_id) AS cnt
        FROM public_marts.fct_image_detections
        GROUP BY channel_name, image_category
    """)).fetchall()

    category_map = {}
    for r in category_rows:
        category_map.setdefault(r.channel_name, {})[r.image_category] = r.cnt

    channels = []
    for r in base_rows:
        cats = category_map.get(r.channel_name, {})
        total = r.total_messages or 1
        channels.append(ChannelVisualStats(
            channel_name=r.channel_name,
            total_messages=r.total_messages,
            messages_with_images=r.messages_with_images,
            image_rate_pct=round(100 * r.messages_with_images / total, 1),
            promotional_count=cats.get("promotional", 0),
            product_display_count=cats.get("product_display", 0),
            lifestyle_count=cats.get("lifestyle", 0),
            other_count=cats.get("other", 0),
        ))

    channels.sort(key=lambda c: c.messages_with_images, reverse=True)

    return VisualContentResponse(channels=channels)


@app.get("/", tags=["Health"], summary="API health check")
def root():
    return {"status": "ok", "message": "Medical Telegram Analytics API is running."}