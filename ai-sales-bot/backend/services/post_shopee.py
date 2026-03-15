"""Shopee Open Platform API service for product listing."""

import os
import time
import hmac
import hashlib
import httpx
from dotenv import load_dotenv

load_dotenv()

SHOPEE_PARTNER_ID = int(os.getenv("SHOPEE_PARTNER_ID", "0"))
SHOPEE_PARTNER_KEY = os.getenv("SHOPEE_PARTNER_KEY", "")
SHOPEE_SHOP_ID = int(os.getenv("SHOPEE_SHOP_ID", "0"))
SHOPEE_ACCESS_TOKEN = os.getenv("SHOPEE_ACCESS_TOKEN", "")
SHOPEE_BASE_URL = "https://partner.shopeemobile.com"


def _sign(path: str, timestamp: int) -> str:
    """Generate Shopee API signature."""
    base_string = f"{SHOPEE_PARTNER_ID}{path}{timestamp}{SHOPEE_ACCESS_TOKEN}{SHOPEE_SHOP_ID}"
    return hmac.new(
        SHOPEE_PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()


def _common_params(path: str) -> dict:
    """Generate common query parameters for Shopee API."""
    timestamp = int(time.time())
    return {
        "partner_id": SHOPEE_PARTNER_ID,
        "timestamp": timestamp,
        "access_token": SHOPEE_ACCESS_TOKEN,
        "shop_id": SHOPEE_SHOP_ID,
        "sign": _sign(path, timestamp)
    }


async def create_listing(
    name: str,
    description: str,
    price: float,
    stock: int = 999,
    category_id: int = 0,
    images: list[str] = None,
    weight: float = 0.5
) -> dict:
    """Create a product listing on Shopee.

    Returns:
        dict with keys: success, item_id, url, error
    """
    path = "/api/v2/product/add_item"
    params = _common_params(path)

    # Price in Shopee is in cents (VND doesn't use decimals, but API may require)
    payload = {
        "original_price": price,
        "description": description,
        "item_name": name[:120],  # Shopee title max 120 chars
        "normal_stock": stock,
        "weight": weight,
        "dimension": {"package_length": 10, "package_width": 10, "package_height": 10},
        "condition": "NEW",
        "item_status": "NORMAL",
        "logistic_info": [],
        "brand": {"brand_id": 0, "original_brand_name": "No Brand"},
    }

    if category_id:
        payload["category_id"] = category_id

    if images:
        payload["image"] = {"image_id_list": images}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SHOPEE_BASE_URL}{path}",
                params=params,
                json=payload
            )
            data = response.json()

            if data.get("error") == "":
                item_id = data["response"]["item_id"]
                return {
                    "success": True,
                    "item_id": item_id,
                    "url": f"https://shopee.vn/product/{SHOPEE_SHOP_ID}/{item_id}",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "item_id": None,
                    "url": None,
                    "error": data.get("message", data.get("error", "Unknown error"))
                }
    except Exception as e:
        return {
            "success": False,
            "item_id": None,
            "url": None,
            "error": str(e)
        }


async def update_listing(item_id: int, name: str = None, description: str = None, price: float = None) -> dict:
    """Update an existing Shopee listing."""
    path = "/api/v2/product/update_item"
    params = _common_params(path)

    payload = {"item_id": item_id}
    if name:
        payload["item_name"] = name[:120]
    if description:
        payload["description"] = description
    if price:
        payload["price_info"] = [{"original_price": price}]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SHOPEE_BASE_URL}{path}",
                params=params,
                json=payload
            )
            data = response.json()
            return {"success": data.get("error") == "", "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}
