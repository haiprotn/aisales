"""TikTok Shop API service for product listing and content posting."""

import os
import hmac
import hashlib
import time
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

TIKTOK_APP_KEY = os.getenv("TIKTOK_APP_KEY", "")
TIKTOK_APP_SECRET = os.getenv("TIKTOK_APP_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_SHOP_CIPHER = os.getenv("TIKTOK_SHOP_CIPHER", "")
TIKTOK_BASE_URL = "https://open-api.tiktokglobalshop.com"


def _sign_request(path: str, params: dict, body: str = "") -> str:
    """Generate TikTok API request signature."""
    sorted_params = sorted(params.items())
    param_str = "".join(f"{k}{v}" for k, v in sorted_params)
    base_string = f"{TIKTOK_APP_SECRET}{path}{param_str}{body}{TIKTOK_APP_SECRET}"
    return hmac.new(
        TIKTOK_APP_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()


def _common_params() -> dict:
    """Common query parameters for TikTok Shop API."""
    timestamp = int(time.time())
    return {
        "app_key": TIKTOK_APP_KEY,
        "timestamp": str(timestamp),
        "access_token": TIKTOK_ACCESS_TOKEN,
        "shop_cipher": TIKTOK_SHOP_CIPHER,
        "version": "202309"
    }


async def create_product(
    name: str,
    description: str,
    price: float,
    category_id: str = "",
    images: list[str] = None,
    stock: int = 999
) -> dict:
    """Create a product on TikTok Shop.

    Returns:
        dict with keys: success, product_id, url, error
    """
    path = "/product/202309/products"
    params = _common_params()

    payload = {
        "title": name[:255],
        "description": description,
        "category_id": category_id,
        "brand_id": "",
        "is_cod_allowed": True,
        "skus": [{
            "sales_attributes": [],
            "stock_infos": [{"warehouse_id": "", "available_stock": stock}],
            "price": {"amount": str(int(price * 100)), "currency": "VND"},
            "seller_sku": f"SKU-{int(time.time())}"
        }],
        "package_dimensions": {
            "length": "10", "width": "10", "height": "10", "unit": "CM"
        },
        "package_weight": {"value": "500", "unit": "GRAM"}
    }

    if images:
        payload["main_images"] = [{"uri": img} for img in images[:9]]

    body_str = json.dumps(payload)
    params["sign"] = _sign_request(path, params, body_str)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{TIKTOK_BASE_URL}{path}",
                params=params,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            data = response.json()

            if data.get("code") == 0:
                product_id = data["data"]["product_id"]
                return {
                    "success": True,
                    "product_id": product_id,
                    "url": f"https://shop.tiktok.com/product/{product_id}",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "product_id": None,
                    "url": None,
                    "error": data.get("message", "Unknown error")
                }
    except Exception as e:
        return {
            "success": False,
            "product_id": None,
            "url": None,
            "error": str(e)
        }


async def post_video_caption(video_id: str, caption: str, hashtags: list[str] = None) -> dict:
    """Update video caption with sales content (for TikTok content posting)."""
    # TikTok Content Posting API requires video upload first
    # This is a simplified version for caption management
    full_caption = caption
    if hashtags:
        full_caption += " " + " ".join(f"#{h}" for h in hashtags)

    return {
        "success": True,
        "caption": full_caption[:2200],
        "note": "Video upload must be done separately via TikTok Content Posting API"
    }
