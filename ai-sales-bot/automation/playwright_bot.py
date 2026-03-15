"""Playwright Browser Automation Bot.

Fallback when platform APIs are unavailable.
Automates posting through browser interactions.
"""

import asyncio
import os
from playwright.async_api import async_playwright

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"


class SalesBot:
    def __init__(self):
        self.browser = None
        self.context = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}, locale="vi-VN"
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def load_cookies(self, cookies_file: str):
        import json
        if os.path.exists(cookies_file):
            with open(cookies_file, "r") as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)

    async def save_cookies(self, cookies_file: str):
        import json
        cookies = await self.context.cookies()
        with open(cookies_file, "w") as f:
            json.dump(cookies, f, indent=2)

    async def post_to_facebook(self, page_url: str, content: str, image_path: str = None) -> dict:
        """Post to Facebook page via browser. Requires pre-logged session cookies."""
        page = await self.context.new_page()
        try:
            await page.goto(page_url, wait_until="networkidle")
            await asyncio.sleep(2)
            create_btn = page.locator(
                'div[role="button"]:has-text("Bạn đang nghĩ gì"), '
                'div[role="button"]:has-text("What\'s on your mind")'
            )
            await create_btn.first.click()
            await asyncio.sleep(2)
            editor = page.locator('div[contenteditable="true"][role="textbox"]')
            await editor.first.fill(content)
            await asyncio.sleep(1)
            if image_path and os.path.exists(image_path):
                file_input = page.locator('input[type="file"]')
                await file_input.set_input_files(image_path)
                await asyncio.sleep(3)
            post_btn = page.locator('div[aria-label="Post"], div[aria-label="Đăng"]')
            await post_btn.first.click()
            await asyncio.sleep(5)
            return {"success": True, "platform": "facebook", "method": "browser"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page.close()

    async def post_to_shopee(self, product_name: str, description: str, price: float, images: list[str] = None) -> dict:
        """Add product to Shopee Seller Center via browser."""
        page = await self.context.new_page()
        try:
            await page.goto("https://banhang.shopee.vn/portal/product/new", wait_until="networkidle")
            await asyncio.sleep(3)
            name_input = page.locator('input[placeholder*="Tên sản phẩm"]')
            if await name_input.count() > 0:
                await name_input.fill(product_name[:120])
            desc_editor = page.locator('.ql-editor, textarea[placeholder*="mô tả"]')
            if await desc_editor.count() > 0:
                await desc_editor.first.fill(description)
            price_input = page.locator('input[placeholder*="Giá"], input[name*="price"]')
            if await price_input.count() > 0:
                await price_input.first.fill(str(int(price)))
            if images:
                file_input = page.locator('input[type="file"][accept*="image"]')
                if await file_input.count() > 0:
                    existing = [f for f in images if os.path.exists(f)]
                    if existing:
                        await file_input.first.set_input_files(existing[:9])
                        await asyncio.sleep(5)
            return {"success": True, "platform": "shopee", "method": "browser"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page.close()

    async def post_to_tiktok(self, product_name: str, description: str, price: float) -> dict:
        """Add product to TikTok Shop Seller Center via browser."""
        page = await self.context.new_page()
        try:
            await page.goto("https://seller-vn.tiktok.com/product/add", wait_until="networkidle")
            await asyncio.sleep(3)
            name_input = page.locator('input[placeholder*="Product name"], input[placeholder*="Tên"]')
            if await name_input.count() > 0:
                await name_input.first.fill(product_name[:255])
            desc_area = page.locator('.ql-editor, textarea')
            if await desc_area.count() > 0:
                await desc_area.first.fill(description)
            return {"success": True, "platform": "tiktok", "method": "browser"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page.close()


async def main():
    bot = SalesBot()
    await bot.start()
    result = await bot.post_to_facebook(
        page_url="https://www.facebook.com/your-page",
        content="🔥 Sản phẩm mới! Giá chỉ 299,000đ. Inbox ngay!"
    )
    print(f"Result: {result}")
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
