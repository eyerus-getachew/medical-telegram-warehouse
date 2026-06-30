"""
api/schemas.py
Pydantic models for request validation and response serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TopProduct(BaseModel):
    term: str = Field(..., description="The frequently mentioned word/term")
    mention_count: int = Field(..., description="Number of messages mentioning this term")


class TopProductsResponse(BaseModel):
    limit: int
    total_results: int
    products: list[TopProduct]


class ChannelActivitySummary(BaseModel):
    channel_name: str
    channel_type: str
    total_posts: int
    avg_views: float
    first_post_date: Optional[datetime]
    last_post_date: Optional[datetime]


class DailyActivity(BaseModel):
    date: str
    message_count: int
    total_views: int


class ChannelActivityResponse(BaseModel):
    channel: ChannelActivitySummary
    daily_activity: list[DailyActivity]


class MessageResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: Optional[str]
    message_date: datetime
    views: int
    forwards: int
    has_image: bool


class MessageSearchResponse(BaseModel):
    query: str
    limit: int
    total_results: int
    messages: list[MessageResult]


class ChannelVisualStats(BaseModel):
    channel_name: str
    total_messages: int
    messages_with_images: int
    image_rate_pct: float
    promotional_count: int
    product_display_count: int
    lifestyle_count: int
    other_count: int


class VisualContentResponse(BaseModel):
    channels: list[ChannelVisualStats]


class ErrorResponse(BaseModel):
    detail: str