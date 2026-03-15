"""Database connection and SQLAlchemy models."""

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean,
    DateTime, ForeignKey, JSON, ARRAY, create_engine
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import (
    DeclarativeBase, relationship, sessionmaker
)
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aisales:aisales123@localhost:5432/ai_sales_db"
)

# Convert sync URL to async if needed
if "postgresql://" in DATABASE_URL and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    category = Column(String(200))
    price = Column(Numeric(15, 2))
    original_price = Column(Numeric(15, 2))
    description = Column(Text)
    specifications = Column(JSON, default={})
    images = Column(ARRAY(Text), default=[])
    status = Column(String(50), default="active")
    source = Column(String(100), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contents = relationship("AIContent", back_populates="product", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="product")


class AIContent(Base):
    __tablename__ = "ai_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    platform = Column(String(50), nullable=False)
    title = Column(String(500))
    body = Column(Text)
    hashtags = Column(ARRAY(Text), default=[])
    cta = Column(String(300))
    tone = Column(String(100), default="professional")
    language = Column(String(10), default="vi")
    generated_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="contents")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    content_id = Column(Integer, ForeignKey("ai_content.id"))
    platform = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)
    platform_post_id = Column(String(200))
    platform_url = Column(Text)
    engagement = Column(JSON, default={"likes": 0, "comments": 0, "shares": 0})
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="posts")
    content = relationship("AIContent")
    comments = relationship("Comment", back_populates="post")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200))
    platforms = Column(ARRAY(Text), default=[])
    posts_per_day = Column(Integer, default=10)
    start_hour = Column(Integer, default=8)
    end_hour = Column(Integer, default=22)
    days_of_week = Column(ARRAY(Integer), default=[1, 2, 3, 4, 5, 6, 7])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    platform = Column(String(50))
    platform_comment_id = Column(String(200))
    author_name = Column(String(200))
    author_id = Column(String(200))
    content = Column(Text)
    ai_reply = Column(Text)
    reply_status = Column(String(50), default="pending")
    replied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100))
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(JSON, default={})
    status = Column(String(50), default="success")
    created_at = Column(DateTime, default=datetime.utcnow)


async def get_db():
    """Dependency: get async database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
