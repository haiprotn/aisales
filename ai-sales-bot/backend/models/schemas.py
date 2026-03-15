"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Product ──────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    category: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    description: Optional[str] = None
    specifications: Optional[dict] = {}
    images: Optional[list[str]] = []

class ProductResponse(ProductCreate):
    id: int
    status: str = "active"
    source: str = "manual"
    created_at: datetime

    class Config:
        from_attributes = True


# ── AI Content ───────────────────────────────────────────

class ContentGenerateRequest(BaseModel):
    product_id: int
    platforms: list[str] = ["facebook", "shopee", "tiktok", "website"]
    tone: str = "professional"
    language: str = "vi"

class ContentResponse(BaseModel):
    id: int
    product_id: int
    platform: str
    title: Optional[str]
    body: Optional[str]
    hashtags: list[str] = []
    cta: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


# ── Post ─────────────────────────────────────────────────

class PostCreate(BaseModel):
    product_id: int
    content_id: int
    platform: str
    scheduled_at: Optional[datetime] = None

class PostResponse(BaseModel):
    id: int
    product_id: int
    content_id: int
    platform: str
    status: str
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    platform_url: Optional[str]
    engagement: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


# ── Schedule ─────────────────────────────────────────────

class ScheduleCreate(BaseModel):
    name: str
    platforms: list[str] = ["facebook"]
    posts_per_day: int = 10
    start_hour: int = 8
    end_hour: int = 22
    days_of_week: list[int] = [1, 2, 3, 4, 5, 6, 7]

class ScheduleResponse(ScheduleCreate):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Comment ──────────────────────────────────────────────

class CommentResponse(BaseModel):
    id: int
    post_id: int
    platform: str
    author_name: Optional[str]
    content: Optional[str]
    ai_reply: Optional[str]
    reply_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard Stats ──────────────────────────────────────

class DashboardStats(BaseModel):
    total_products: int = 0
    total_posts: int = 0
    published_posts: int = 0
    scheduled_posts: int = 0
    pending_comments: int = 0
    total_engagement: dict = {"likes": 0, "comments": 0, "shares": 0}
