"""Comment API - monitor comments and AI auto-reply."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from models.database import get_db, Comment, Post, Product, ActivityLog
from models.schemas import CommentResponse
from services.ai_writer import generate_reply
from services.post_facebook import get_comments as fb_get_comments, reply_comment as fb_reply

router = APIRouter(prefix="/api/comments", tags=["Comments"])


@router.get("/", response_model=list[CommentResponse])
async def list_comments(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(Comment).order_by(Comment.created_at.desc())
    if status:
        query = query.where(Comment.reply_status == status)
    if platform:
        query = query.where(Comment.platform == platform)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def comment_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Comment.id)))
    pending = await db.execute(
        select(func.count(Comment.id)).where(Comment.reply_status == "pending")
    )
    replied = await db.execute(
        select(func.count(Comment.id)).where(Comment.reply_status == "replied")
    )
    return {
        "total": total.scalar() or 0,
        "pending": pending.scalar() or 0,
        "replied": replied.scalar() or 0
    }


@router.post("/fetch/{post_id}")
async def fetch_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch new comments from a platform post."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng")

    if not post.platform_post_id:
        return {"fetched": 0, "message": "Bài chưa được đăng lên platform"}

    new_comments = []
    if post.platform == "facebook":
        raw_comments = await fb_get_comments(post.platform_post_id)
        for c in raw_comments:
            # Check if already exists
            existing = await db.execute(
                select(Comment).where(Comment.platform_comment_id == c["id"])
            )
            if not existing.scalar_one_or_none():
                comment = Comment(
                    post_id=post.id,
                    platform="facebook",
                    platform_comment_id=c["id"],
                    author_name=c.get("from", {}).get("name", "Unknown"),
                    author_id=c.get("from", {}).get("id", ""),
                    content=c.get("message", "")
                )
                db.add(comment)
                new_comments.append(comment)

    await db.commit()
    return {"fetched": len(new_comments)}


@router.post("/auto-reply/{comment_id}")
async def auto_reply(comment_id: int, db: AsyncSession = Depends(get_db)):
    """Generate and send AI reply to a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Không tìm thấy bình luận")

    # Get product name
    post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
    post = post_result.scalar_one_or_none()
    product_name = ""
    if post and post.product_id:
        prod_result = await db.execute(select(Product).where(Product.id == post.product_id))
        product = prod_result.scalar_one_or_none()
        product_name = product.name if product else ""

    # Generate AI reply
    ai_reply = await generate_reply(
        comment_text=comment.content,
        product_name=product_name,
        platform=comment.platform
    )
    comment.ai_reply = ai_reply

    # Send reply to platform
    if comment.platform == "facebook" and comment.platform_comment_id:
        reply_result = await fb_reply(comment.platform_comment_id, ai_reply)
        if reply_result.get("success"):
            comment.reply_status = "replied"
            comment.replied_at = datetime.utcnow()
        else:
            comment.reply_status = "failed"
    else:
        comment.reply_status = "draft"

    await db.commit()
    await db.refresh(comment)

    db.add(ActivityLog(
        action="comment_replied", entity_type="comment",
        entity_id=comment.id,
        details={"reply": ai_reply[:100], "status": comment.reply_status}
    ))
    await db.commit()
    return {"reply": ai_reply, "status": comment.reply_status}


@router.post("/auto-reply-all")
async def auto_reply_all(db: AsyncSession = Depends(get_db)):
    """Auto-reply to all pending comments."""
    result = await db.execute(
        select(Comment).where(Comment.reply_status == "pending").limit(20)
    )
    pending = result.scalars().all()

    replied = 0
    for comment in pending:
        try:
            post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
            post = post_result.scalar_one_or_none()
            product_name = ""
            if post and post.product_id:
                prod_result = await db.execute(select(Product).where(Product.id == post.product_id))
                product = prod_result.scalar_one_or_none()
                product_name = product.name if product else ""

            ai_reply = await generate_reply(comment.content, product_name, comment.platform)
            comment.ai_reply = ai_reply
            comment.reply_status = "draft"
            replied += 1
        except Exception:
            continue

    await db.commit()
    return {"processed": replied, "total_pending": len(pending)}
