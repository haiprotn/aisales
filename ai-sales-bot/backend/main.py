"""AI Sales Bot - Main FastAPI Application."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from models.database import init_db
from utils.scheduler import start_scheduler, stop_scheduler
from api.product import router as product_router
from api.post import router as post_router
from api.schedule import router as schedule_router
from api.comment import router as comment_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    print("🚀 AI Sales Bot started!")
    print("📊 Dashboard: http://localhost:8000")
    print("📖 API Docs:  http://localhost:8000/docs")
    yield
    stop_scheduler()


app = FastAPI(
    title="AI Sales Bot",
    description="Hệ thống AI bán hàng tự động",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(product_router)
app.include_router(post_router)
app.include_router(schedule_router)
app.include_router(comment_router)


@app.get("/api/dashboard")
async def dashboard_stats():
    from sqlalchemy import select, func
    from models.database import async_session, Product, Post, Comment
    async with async_session() as db:
        products = await db.execute(select(func.count(Product.id)))
        posts = await db.execute(select(func.count(Post.id)))
        published = await db.execute(select(func.count(Post.id)).where(Post.status == "published"))
        scheduled = await db.execute(select(func.count(Post.id)).where(Post.status == "scheduled"))
        pending = await db.execute(select(func.count(Comment.id)).where(Comment.reply_status == "pending"))
        recent = await db.execute(select(Post).order_by(Post.created_at.desc()).limit(10))
        return {
            "total_products": products.scalar() or 0,
            "total_posts": posts.scalar() or 0,
            "published_posts": published.scalar() or 0,
            "scheduled_posts": scheduled.scalar() or 0,
            "pending_comments": pending.scalar() or 0,
            "recent_posts": [
                {"id": p.id, "platform": p.platform, "status": p.status, "created_at": str(p.created_at)}
                for p in recent.scalars().all()
            ]
        }


@app.get("/api/activity")
async def activity_log(limit: int = 20):
    from sqlalchemy import select
    from models.database import async_session, ActivityLog
    async with async_session() as db:
        result = await db.execute(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit))
        return [
            {"id": l.id, "action": l.action, "entity_type": l.entity_type,
             "details": l.details, "status": l.status, "created_at": str(l.created_at)}
            for l in result.scalars().all()
        ]


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
