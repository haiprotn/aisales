"""Facebook posting service via Graph API."""

import os
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")
FB_API_VERSION = "v19.0"
FB_BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"


async def publish_post(title: str, body: str, hashtags: list[str], image_url: str = None) -> dict:
    """Publish a post to Facebook Page.
    
    Returns:
        dict with keys: success, post_id, url, error
    """
    message = f"{title}\n\n{body}"
    if hashtags:
        message += "\n\n" + " ".join(f"#{h}" for h in hashtags)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if image_url:
                # Post with image
                endpoint = f"{FB_BASE_URL}/{FB_PAGE_ID}/photos"
                payload = {
                    "message": message,
                    "url": image_url,
                    "access_token": FB_ACCESS_TOKEN
                }
            else:
                # Text-only post
                endpoint = f"{FB_BASE_URL}/{FB_PAGE_ID}/feed"
                payload = {
                    "message": message,
                    "access_token": FB_ACCESS_TOKEN
                }

            response = await client.post(endpoint, data=payload)
            data = response.json()

            if "id" in data:
                post_id = data["id"]
                return {
                    "success": True,
                    "post_id": post_id,
                    "url": f"https://facebook.com/{post_id}",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "post_id": None,
                    "url": None,
                    "error": data.get("error", {}).get("message", "Unknown error")
                }

    except Exception as e:
        return {
            "success": False,
            "post_id": None,
            "url": None,
            "error": str(e)
        }


async def get_comments(post_id: str) -> list[dict]:
    """Fetch comments on a Facebook post."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{FB_BASE_URL}/{post_id}/comments",
                params={"access_token": FB_ACCESS_TOKEN, "limit": 100}
            )
            data = response.json()
            return data.get("data", [])
    except Exception:
        return []


async def reply_comment(comment_id: str, message: str) -> dict:
    """Reply to a comment on Facebook."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{FB_BASE_URL}/{comment_id}/comments",
                data={
                    "message": message,
                    "access_token": FB_ACCESS_TOKEN
                }
            )
            data = response.json()
            return {"success": "id" in data, "reply_id": data.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}
