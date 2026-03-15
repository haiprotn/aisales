"""Website posting service - supports WordPress REST API and custom APIs."""

import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

WEBSITE_URL = os.getenv("WEBSITE_URL", "https://your-site.com")
WEBSITE_API_KEY = os.getenv("WEBSITE_API_KEY", "")
WEBSITE_USERNAME = os.getenv("WEBSITE_USERNAME", "")
WEBSITE_PASSWORD = os.getenv("WEBSITE_PASSWORD", "")


def _auth_headers() -> dict:
    """Generate authentication headers for WordPress."""
    if WEBSITE_API_KEY:
        return {"Authorization": f"Bearer {WEBSITE_API_KEY}"}
    elif WEBSITE_USERNAME and WEBSITE_PASSWORD:
        credentials = base64.b64encode(
            f"{WEBSITE_USERNAME}:{WEBSITE_PASSWORD}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}
    return {}


async def publish_post(
    title: str,
    body: str,
    category: str = "",
    tags: list[str] = None,
    featured_image_url: str = None,
    status: str = "publish"
) -> dict:
    """Publish a post to WordPress website.

    Returns:
        dict with keys: success, post_id, url, error
    """
    endpoint = f"{WEBSITE_URL}/wp-json/wp/v2/posts"

    # Convert body to HTML paragraphs
    html_body = ""
    for paragraph in body.split("\n\n"):
        if paragraph.strip():
            html_body += f"<p>{paragraph.strip()}</p>\n"

    payload = {
        "title": title,
        "content": html_body,
        "status": status,  # "publish", "draft", "pending"
        "format": "standard"
    }

    if tags:
        # WordPress expects tag IDs; create tags if needed
        tag_ids = await _get_or_create_tags(tags)
        payload["tags"] = tag_ids

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                endpoint,
                headers={**_auth_headers(), "Content-Type": "application/json"},
                json=payload
            )
            data = response.json()

            if response.status_code in (200, 201):
                return {
                    "success": True,
                    "post_id": data["id"],
                    "url": data.get("link", ""),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "post_id": None,
                    "url": None,
                    "error": data.get("message", f"HTTP {response.status_code}")
                }
    except Exception as e:
        return {
            "success": False,
            "post_id": None,
            "url": None,
            "error": str(e)
        }


async def _get_or_create_tags(tag_names: list[str]) -> list[int]:
    """Get or create WordPress tags and return their IDs."""
    tag_ids = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            for name in tag_names[:10]:  # Limit to 10 tags
                # Search existing
                resp = await client.get(
                    f"{WEBSITE_URL}/wp-json/wp/v2/tags",
                    headers=_auth_headers(),
                    params={"search": name}
                )
                existing = resp.json()
                if existing and len(existing) > 0:
                    tag_ids.append(existing[0]["id"])
                else:
                    # Create new tag
                    resp = await client.post(
                        f"{WEBSITE_URL}/wp-json/wp/v2/tags",
                        headers={**_auth_headers(), "Content-Type": "application/json"},
                        json={"name": name}
                    )
                    if resp.status_code in (200, 201):
                        tag_ids.append(resp.json()["id"])
    except Exception:
        pass
    return tag_ids


async def update_post(post_id: int, title: str = None, body: str = None) -> dict:
    """Update an existing WordPress post."""
    endpoint = f"{WEBSITE_URL}/wp-json/wp/v2/posts/{post_id}"
    payload = {}
    if title:
        payload["title"] = title
    if body:
        html_body = "".join(f"<p>{p.strip()}</p>" for p in body.split("\n\n") if p.strip())
        payload["content"] = html_body

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.put(
                endpoint,
                headers={**_auth_headers(), "Content-Type": "application/json"},
                json=payload
            )
            return {"success": response.status_code == 200}
    except Exception as e:
        return {"success": False, "error": str(e)}
