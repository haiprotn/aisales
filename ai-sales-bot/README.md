# 🤖 AI Sales Bot - Hệ Thống Bán Hàng Tự Động

> Hệ thống AI tự động tạo nội dung bán hàng, đăng bài lên nhiều nền tảng, và trả lời khách hàng.

## 🏗️ Kiến Trúc Hệ Thống

```
                +-------------------+
                |   Frontend        |
                | React Dashboard   |
                +---------+---------+
                          |
                   FastAPI Backend
                          |
        +-----------------+-----------------+
        |                                   |
   Product Database                    AI Service
    PostgreSQL                      (Claude / GPT)
        |                                   |
        +-----------------+-----------------+
                          |
                    Automation Bot
                  (Playwright / API)
                          |
        +-----------------+------------------+
        |        |         |        |
      Shopee   Facebook   TikTok   Website
```

## ✨ Tính Năng

1. **Nhập sản phẩm** - từ Excel/CSV/Database
2. **AI tạo nội dung** - tiêu đề, mô tả, hashtag tự động
3. **Đăng tự động** - Facebook, Shopee, TikTok Shop, Website
4. **Lập lịch đăng bài** - cấu hình số bài/ngày
5. **Theo dõi bình luận** - AI trả lời khách tự động

## 🚀 Cài Đặt

### Yêu cầu
- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (cho frontend)
- Docker & Docker Compose

### Bước 1: Clone & Setup

```bash
git clone https://github.com/your-username/ai-sales-bot.git
cd ai-sales-bot
cp .env.example .env
# Cập nhật API keys trong .env
```

### Bước 2: Chạy với Docker

```bash
docker compose up -d
```

### Bước 3: Chạy thủ công (development)

```bash
# Backend
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload --port 8000

# Frontend (tab khác)
cd frontend
# Mở file index.html hoặc serve
```

### Bước 4: Truy cập

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Cấu Trúc Project

```
ai-sales-bot/
├── backend/
│   ├── main.py              # FastAPI app chính
│   ├── requirements.txt     # Python dependencies
│   ├── api/
│   │   ├── product.py       # API quản lý sản phẩm
│   │   ├── post.py          # API tạo & đăng bài
│   │   ├── schedule.py      # API lập lịch
│   │   └── comment.py       # API theo dõi bình luận
│   ├── services/
│   │   ├── ai_writer.py     # AI viết nội dung
│   │   ├── post_facebook.py # Đăng Facebook
│   │   ├── post_shopee.py   # Đăng Shopee
│   │   ├── post_tiktok.py   # Đăng TikTok
│   │   └── post_website.py  # Đăng Website
│   ├── models/
│   │   ├── database.py      # Database connection
│   │   └── schemas.py       # Pydantic models
│   └── utils/
│       ├── file_parser.py   # Đọc Excel/CSV
│       └── scheduler.py     # Background scheduler
├── automation/
│   └── playwright_bot.py    # Browser automation
├── frontend/
│   └── index.html           # Dashboard SPA
├── docker/
│   └── docker-compose.yml
├── data/                    # Upload folder
├── scripts/
│   └── init_db.sql          # Database schema
├── .env.example
└── README.md
```

## ⚙️ Cấu Hình (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_sales
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
FB_ACCESS_TOKEN=your-token
SHOPEE_API_KEY=your-key
TIKTOK_API_KEY=your-key
```

## 📄 License

MIT
