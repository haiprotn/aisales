"""AI Content Writer Service - Generates sales content for multiple platforms."""

import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


PLATFORM_PROMPTS = {
    "facebook": """Bạn là chuyên gia viết content bán hàng trên Facebook.
Viết bài đăng bán sản phẩm hấp dẫn, có emoji, thu hút tương tác.
Bài viết phải có: hook mở đầu gây tò mò, mô tả lợi ích sản phẩm, call-to-action mạnh.
Độ dài: 150-300 từ. Phong cách: thân thiện, gần gũi.""",

    "shopee": """Bạn là chuyên gia viết mô tả sản phẩm trên Shopee.
Viết tiêu đề SEO tốt (tối đa 120 ký tự) và mô tả chi tiết sản phẩm.
Bao gồm: thông số kỹ thuật, lợi ích, cam kết chất lượng, chính sách đổi trả.
Dùng bullet points rõ ràng. Tối ưu cho tìm kiếm.""",

    "tiktok": """Bạn là chuyên gia viết content TikTok Shop.
Viết caption ngắn gọn, bắt trend, dùng nhiều emoji.
Tập trung vào 1-2 điểm nổi bật nhất của sản phẩm.
Độ dài: 50-100 từ. Phải có hashtag trending.""",

    "website": """Bạn là chuyên gia viết content website bán hàng.
Viết mô tả sản phẩm chuyên nghiệp, SEO-friendly.
Bao gồm: giới thiệu, tính năng nổi bật, lợi ích, thông số kỹ thuật.
Tone: chuyên nghiệp, đáng tin cậy. Dùng heading và paragraph rõ ràng."""
}


async def generate_content(
    product_name: str,
    product_description: str,
    product_price: float,
    product_category: str,
    platform: str,
    tone: str = "professional",
    language: str = "vi"
) -> dict:
    """Generate sales content for a specific platform."""

    platform_guide = PLATFORM_PROMPTS.get(platform, PLATFORM_PROMPTS["facebook"])

    prompt = f"""{platform_guide}

THÔNG TIN SẢN PHẨM:
- Tên: {product_name}
- Mô tả gốc: {product_description or 'Không có'}
- Giá: {product_price:,.0f}đ
- Danh mục: {product_category or 'Chung'}

YÊU CẦU:
- Ngôn ngữ: {'Tiếng Việt' if language == 'vi' else 'English'}
- Tone: {tone}
- Platform: {platform}

Trả về JSON với format:
{{
    "title": "Tiêu đề bài đăng",
    "body": "Nội dung chính",
    "hashtags": ["hashtag1", "hashtag2", ...],
    "cta": "Call to action"
}}

CHỈ trả về JSON, KHÔNG có text khác."""

    if AI_PROVIDER == "anthropic":
        return await _call_anthropic(prompt)
    else:
        return await _call_openai(prompt)


async def generate_reply(
    comment_text: str,
    product_name: str,
    platform: str
) -> str:
    """Generate AI reply to a customer comment."""

    prompt = f"""Bạn là nhân viên CSKH thân thiện, chuyên nghiệp.
Trả lời bình luận của khách hàng về sản phẩm "{product_name}" trên {platform}.

Bình luận khách: "{comment_text}"

Quy tắc:
- Luôn lịch sự, thân thiện
- Trả lời ngắn gọn (1-3 câu)
- Nếu hỏi giá → cung cấp và mời inbox
- Nếu hỏi ship → mời inbox để tư vấn
- Nếu khen → cảm ơn và mời mua thêm
- Nếu chê → xin lỗi và đề nghị hỗ trợ

CHỈ trả về câu trả lời, KHÔNG giải thích."""

    if AI_PROVIDER == "anthropic":
        result = await _call_anthropic_text(prompt)
    else:
        result = await _call_openai_text(prompt)
    return result


async def _call_anthropic(prompt: str) -> dict:
    """Call Anthropic Claude API and parse JSON response."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        text = data["content"][0]["text"]
        # Extract JSON from response
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)


async def _call_anthropic_text(prompt: str) -> str:
    """Call Anthropic Claude API and return plain text."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        return data["content"][0]["text"].strip()


async def _call_openai(prompt: str) -> dict:
    """Call OpenAI API and parse JSON response."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)


async def _call_openai_text(prompt: str) -> str:
    """Call OpenAI API and return plain text."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
