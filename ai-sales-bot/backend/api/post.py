"""Post API - AI content generation, publishing, and management."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from models.database import get_db, Product, AIContent, Post, ActivityLog
from models.schemas import ContentGenerateRequest, ContentResponse, PostCreate, PostResponse
from services.ai_writer import generate_content
from services.post_facebook import publish_post as fb_publish
from services.post_shopee import create_listing as shopee_publish
from services.post_tiktok import create_product as tiktok_publish
from services.post_website import publish_post as web_publish

router = APIRouter(prefix="/api/posts", tags=["Posts"])


# ── AI Content Generation ────────────────────────────────

@router.post("/generate", response_model=list[ContentResponse])
async def generate_ai_content(
    req: ContentGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI sales content for a product across platforms."""
    result = await db.execute(select(Product).where(Product.id == req.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    contents = []
    for platform in req.platforms:
        try:
            ai_result = await generate_content(
                product_name=product.name,
                product_description=product.description or "",
                product_price=float(product.price or 0),
                product_category=product.category or "",
                platform=platform,
                tone=req.tone,
                language=req.language
            )

            content = AIContent(
                product_id=product.id,
                platform=platform,
                title=ai_result.get("title", ""),
                body=ai_result.get("body", ""),
                hashtags=ai_result.get("hashtags", []),
                cta=ai_result.get("cta", ""),
                tone=req.tone,
                language=req.language
            )
            db.add(content)
            contents.append(content)

        except Exception as e:
            # Log error but continue with other platforms
            db.add(ActivityLog(
                action="content_generation_failed",
                entity_type="product", entity_id=product.id,
                details={"platform": platform, "error": str(e)},
                status="error"
            ))

    await db.commit()
    for c in contents:
        await db.refresh(c)

    db.add(ActivityLog(
        action="content_generated", entity_type="product",
        entity_id=product.id,
        details={"platforms": req.platforms, "count": len(contents)}
    ))
    await db.commit()
    return contents


@router.get("/content/{product_id}", response_model=list[ContentResponse])
async def get_product_content(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get all generated content for a product."""
    result = await db.execute(
        select(AIContent)
        .where(AIContent.product_id == product_id)
        .order_by(AIContent.generated_at.desc())
    )
    return result.scalars().all()


# ── Publishing ───────────────────────────────────────────

@router.post("/publish", response_model=PostResponse)
async def publish_post(data: PostCreate, db: AsyncSession = Depends(get_db)):
    """Publish content to a platform immediately or schedule it."""
    # Get the AI content
    result = await db.execute(select(AIContent).where(AIContent.id == data.content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Không tìm thấy nội dung")

    # Create post record
    post = Post(
        product_id=data.product_id,
        content_id=data.content_id,
        platform=data.platform,
        status="scheduled" if data.scheduled_at else "publishing",
        scheduled_at=data.scheduled_at
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # If no schedule, publish immediately
    if not data.scheduled_at:
        result = await _do_publish(content, data.platform)
        post.status = "published" if result["success"] else "failed"
        post.published_at = datetime.utcnow() if result["success"] else None
        post.platform_post_id = result.get("post_id") or result.get("item_id") or result.get("product_id")
        post.platform_url = result.get("url")
        post.error_message = result.get("error")
        await db.commit()
        await db.refresh(post)

    db.add(ActivityLog(
        action="post_published" if post.status == "published" else "post_scheduled",
        entity_type="post", entity_id=post.id,
        details={"platform": data.platform, "status": post.status}
    ))
    await db.commit()
    return post


async def _do_publish(content: AIContent, platform: str) -> dict:
    """Execute the actual publishing to a platform."""
    title = content.title or ""
    body = content.body or ""
    hashtags = content.hashtags or []

    try:
        if platform == "facebook":
            return await fb_publish(title=title, body=body, hashtags=hashtags)
        elif platform == "shopee":
            return await shopee_publish(
                name=title, description=body,
                price=0  # Should come from product
            )
        elif platform == "tiktok":
            return await tiktok_publish(
                name=title, description=body, price=0
            )
        elif platform == "website":
            return await web_publish(title=title, body=body, tags=hashtags)
        else:
            return {"success": False, "error": f"Platform không hỗ trợ: {platform}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/publish-all/{product_id}")
async def publish_all_platforms(product_id: int, db: AsyncSession = Depends(get_db)):
    """Publish latest content for a product to all platforms at once."""
    result = await db.execute(
        select(AIContent)
        .where(AIContent.product_id == product_id)
        .order_by(AIContent.generated_at.desc())
    )
    contents = result.scalars().all()
    if not contents:
        raise HTTPException(status_code=404, detail="Chưa có nội dung. Hãy generate trước.")

    results = []
    for content in contents:
        pub_result = await _do_publish(content, content.platform)
        post = Post(
            product_id=product_id, content_id=content.id,
            platform=content.platform,
            status="published" if pub_result["success"] else "failed",
            published_at=datetime.utcnow() if pub_result["success"] else None,
            platform_post_id=str(pub_result.get("post_id", "")),
            platform_url=pub_result.get("url"),
            error_message=pub_result.get("error")
        )
        db.add(post)
        results.append({
            "platform": content.platform,
            "success": pub_result["success"],
            "url": pub_result.get("url"),
            "error": pub_result.get("error")
        })

    await db.commit()
    return {"results": results}


# ── Post Management ──────────────────────────────────────

@router.get("/", response_model=list[PostResponse])
async def list_posts(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all posts with optional filters."""
    query = select(Post).order_by(Post.created_at.desc())
    if platform:
        query = query.where(Post.platform == platform)
    if status:
        query = query.where(Post.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def post_stats(db: AsyncSession = Depends(get_db)):
    """Get posting statistics."""
    total = await db.execute(select(func.count(Post.id)))
    by_status = await db.execute(
        select(Post.status, func.count(Post.id)).group_by(Post.status)
    )
    by_platform = await db.execute(
        select(Post.platform, func.count(Post.id)).group_by(Post.platform)
    )
    return {
        "total": total.scalar() or 0,
        "by_status": {r[0]: r[1] for r in by_status.all()},
        "by_platform": {r[0]: r[1] for r in by_platform.all()}
    }
