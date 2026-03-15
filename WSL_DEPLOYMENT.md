# 🚀 Hướng Dẫn Triển Khai AI Sales Bot trên WSL

## Mục lục
1. [Cài đặt WSL](#1-cài-đặt-wsl)
2. [Cài đặt công cụ cần thiết](#2-cài-đặt-công-cụ)
3. [Clone và cấu hình project](#3-clone-project)
4. [Cách 1: Chạy trực tiếp (Development)](#4-chạy-trực-tiếp)
5. [Cách 2: Chạy bằng Docker](#5-chạy-docker)
6. [Kiểm tra hoạt động](#6-kiểm-tra)
7. [Xử lý lỗi thường gặp](#7-xử-lý-lỗi)

---

## 1. Cài đặt WSL

### Mở PowerShell (Admin) trên Windows:

```powershell
# Cài WSL với Ubuntu (chỉ cần chạy 1 lần)
wsl --install -d Ubuntu-22.04

# Sau khi cài xong, restart máy
# Mở Ubuntu từ Start Menu, tạo username/password
```

### Kiểm tra WSL đã cài đúng:

```bash
# Trong terminal Ubuntu/WSL
lsb_release -a
# Phải hiện: Ubuntu 22.04
```

---

## 2. Cài đặt công cụ

### Chạy lần lượt trong WSL terminal:

```bash
# ══════════════════════════════════════════════
# BƯỚC 2.1: Cập nhật hệ thống
# ══════════════════════════════════════════════
sudo apt update && sudo apt upgrade -y

# ══════════════════════════════════════════════
# BƯỚC 2.2: Cài Python 3.11
# ══════════════════════════════════════════════
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Kiểm tra
python3.11 --version
# → Python 3.11.x

# ══════════════════════════════════════════════
# BƯỚC 2.3: Cài PostgreSQL
# ══════════════════════════════════════════════
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Khởi động PostgreSQL
sudo service postgresql start

# Tạo database và user
sudo -u postgres psql -c "CREATE USER aisales WITH PASSWORD 'aisales123';"
sudo -u postgres psql -c "CREATE DATABASE ai_sales_db OWNER aisales;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_sales_db TO aisales;"

# Kiểm tra kết nối
psql -h localhost -U aisales -d ai_sales_db -c "SELECT 1;"
# Nhập password: aisales123

# ══════════════════════════════════════════════
# BƯỚC 2.4: Cài Git
# ══════════════════════════════════════════════
sudo apt install -y git

# ══════════════════════════════════════════════
# BƯỚC 2.5: (Tùy chọn) Cài Docker
# ══════════════════════════════════════════════
# Nếu muốn chạy bằng Docker thay vì trực tiếp:
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Cho phép user chạy docker không cần sudo
sudo usermod -aG docker $USER
newgrp docker

# Kiểm tra
docker --version
docker compose version
```

---

## 3. Clone và cấu hình project

```bash
# ══════════════════════════════════════════════
# BƯỚC 3.1: Clone project
# ══════════════════════════════════════════════
cd ~
git clone https://github.com/YOUR_USERNAME/ai-sales-bot.git
cd ai-sales-bot

# Hoặc nếu chưa push lên GitHub, copy thủ công:
# Từ Windows Explorer, project nằm ở: \\wsl$\Ubuntu-22.04\home\YOUR_USER\

# ══════════════════════════════════════════════
# BƯỚC 3.2: Tạo file .env
# ══════════════════════════════════════════════
cp .env.example .env
nano .env

# Sửa các giá trị trong .env:
# - DATABASE_URL=postgresql://aisales:aisales123@localhost:5432/ai_sales_db
# - ANTHROPIC_API_KEY=sk-ant-xxxxx  (lấy từ console.anthropic.com)
# - Hoặc OPENAI_API_KEY nếu dùng OpenAI
# 
# Lưu: Ctrl+O, Enter, Ctrl+X

# ══════════════════════════════════════════════
# BƯỚC 3.3: Khởi tạo database schema
# ══════════════════════════════════════════════
psql -h localhost -U aisales -d ai_sales_db -f scripts/init_db.sql
# Nhập password: aisales123
```

---

## 4. Chạy trực tiếp (Development)

**Cách này phù hợp để dev/test. Không cần Docker.**

```bash
cd ~/ai-sales-bot

# ══════════════════════════════════════════════
# BƯỚC 4.1: Tạo virtual environment
# ══════════════════════════════════════════════
python3.11 -m venv venv
source venv/bin/activate

# Kiểm tra đang dùng đúng Python
which python
# → /home/YOUR_USER/ai-sales-bot/venv/bin/python

# ══════════════════════════════════════════════
# BƯỚC 4.2: Cài dependencies
# ══════════════════════════════════════════════
pip install --upgrade pip
pip install -r backend/requirements.txt

# Cài Playwright browser (cho automation)
playwright install chromium
playwright install-deps

# ══════════════════════════════════════════════
# BƯỚC 4.3: Đảm bảo PostgreSQL đang chạy
# ══════════════════════════════════════════════
sudo service postgresql start

# ══════════════════════════════════════════════
# BƯỚC 4.4: Chạy server
# ══════════════════════════════════════════════
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Output sẽ hiện:
# 🚀 AI Sales Bot started!
# 📊 Dashboard: http://localhost:8000
# 📖 API Docs:  http://localhost:8000/docs
```

### Truy cập từ Windows:

Mở trình duyệt Windows, vào:
- **Dashboard**: http://localhost:8000
- **API Docs** : http://localhost:8000/docs

### Script khởi động nhanh:

```bash
# Tạo file start.sh để chạy nhanh mỗi lần
cat > ~/ai-sales-bot/start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting AI Sales Bot..."

# Start PostgreSQL
sudo service postgresql start

# Activate venv
cd ~/ai-sales-bot
source venv/bin/activate

# Run server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF

chmod +x ~/ai-sales-bot/start.sh

# Từ giờ chỉ cần chạy:
~/ai-sales-bot/start.sh
```

---

## 5. Chạy bằng Docker

**Cách này phù hợp cho production. Đơn giản hơn, không cần cài PostgreSQL thủ công.**

```bash
cd ~/ai-sales-bot

# ══════════════════════════════════════════════
# BƯỚC 5.1: Đảm bảo Docker đang chạy
# ══════════════════════════════════════════════
sudo service docker start

# ══════════════════════════════════════════════
# BƯỚC 5.2: Build và chạy
# ══════════════════════════════════════════════
cd docker
docker compose up -d --build

# Kiểm tra containers
docker compose ps

# Xem logs
docker compose logs -f backend

# Output:
# aisales-db       | ... database system is ready
# aisales-backend  | 🚀 AI Sales Bot started!

# ══════════════════════════════════════════════
# BƯỚC 5.3: Dừng / Khởi động lại
# ══════════════════════════════════════════════
docker compose stop      # Dừng
docker compose start     # Chạy lại
docker compose down      # Dừng và xóa containers
docker compose down -v   # Dừng, xóa containers VÀ database
```

### Truy cập từ Windows:
- **Dashboard**: http://localhost:8000
- **API Docs** : http://localhost:8000/docs

---

## 6. Kiểm tra hoạt động

### Test API nhanh bằng curl:

```bash
# ── Kiểm tra server ─────────────────────────
curl http://localhost:8000/api/dashboard
# → {"total_products":0, "total_posts":0, ...}

# ── Thêm sản phẩm thủ công ──────────────────
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Áo thun nam cao cấp",
    "price": 299000,
    "category": "Thời trang",
    "description": "Áo thun 100% cotton, nhiều màu, size S-XXL"
  }'

# ── Xem danh sách sản phẩm ──────────────────
curl http://localhost:8000/api/products/

# ── AI tạo nội dung bán hàng ────────────────
curl -X POST http://localhost:8000/api/posts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "platforms": ["facebook", "shopee", "tiktok"],
    "tone": "friendly",
    "language": "vi"
  }'
# → AI sẽ tạo content cho từng platform

# ── Import sản phẩm từ Excel ────────────────
curl -X POST http://localhost:8000/api/products/import \
  -F "file=@/path/to/products.xlsx"

# ── Tạo lịch đăng bài ───────────────────────
curl -X POST http://localhost:8000/api/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lịch đăng hàng ngày",
    "platforms": ["facebook", "shopee"],
    "posts_per_day": 10,
    "start_hour": 8,
    "end_hour": 22
  }'

# ── Xem API docs đầy đủ ─────────────────────
# Mở browser: http://localhost:8000/docs
```

### Test import file Excel:

Tạo file `test_products.csv`:
```csv
Tên sản phẩm,Giá,Danh mục,Mô tả
Áo thun nam,299000,Thời trang,Áo thun cotton cao cấp
Quần jean nữ,450000,Thời trang,Quần jean co giãn
Giày sneaker,650000,Giày dép,Giày sneaker nam nữ unisex
```

```bash
curl -X POST http://localhost:8000/api/products/import \
  -F "file=@test_products.csv"
# → {"success":true, "imported":3, ...}
```

---

## 7. Xử lý lỗi thường gặp

### ❌ Lỗi: "PostgreSQL connection refused"
```bash
# PostgreSQL chưa chạy
sudo service postgresql start

# Kiểm tra
sudo service postgresql status
```

### ❌ Lỗi: "Port 8000 already in use"
```bash
# Tìm process đang dùng port
lsof -i :8000

# Kill process
kill -9 <PID>

# Hoặc dùng port khác
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### ❌ Lỗi: "ModuleNotFoundError"
```bash
# Đảm bảo đang trong venv
source ~/ai-sales-bot/venv/bin/activate

# Cài lại dependencies
pip install -r backend/requirements.txt
```

### ❌ Lỗi: "localhost không truy cập được từ Windows"
```bash
# Kiểm tra IP của WSL
hostname -I
# Ví dụ: 172.25.123.45

# Truy cập từ Windows bằng IP đó:
# http://172.25.123.45:8000
```

### ❌ Lỗi: Docker "permission denied"
```bash
sudo usermod -aG docker $USER
# Đóng terminal, mở lại
newgrp docker
```

### ❌ Lỗi: "psql: FATAL: password authentication failed"
```bash
# Reset password PostgreSQL
sudo -u postgres psql -c "ALTER USER aisales PASSWORD 'aisales123';"
```

### ❌ WSL quá chậm / hết RAM
```powershell
# Tạo file C:\Users\YOUR_USER\.wslconfig trong Windows:
# Nội dung:
[wsl2]
memory=4GB
processors=2
swap=2GB
```

---

## 📌 Lệnh hàng ngày (cheat sheet)

```bash
# Mở WSL
wsl

# Chạy server (dev mode)
~/ai-sales-bot/start.sh

# Chạy server (docker mode)
cd ~/ai-sales-bot/docker && docker compose up -d

# Xem logs docker
docker compose logs -f backend

# Restart server
docker compose restart backend

# Backup database
pg_dump -h localhost -U aisales ai_sales_db > backup_$(date +%Y%m%d).sql

# Restore database
psql -h localhost -U aisales ai_sales_db < backup_20260315.sql
```

---

## 🔧 Tự động khởi động khi mở WSL

```bash
# Thêm vào ~/.bashrc
echo '
# Auto-start PostgreSQL
if ! pg_isready -q 2>/dev/null; then
    sudo service postgresql start 2>/dev/null
fi
' >> ~/.bashrc

# Cho phép start postgresql không cần password
sudo visudo
# Thêm dòng cuối:
# YOUR_USER ALL=(ALL) NOPASSWD: /usr/sbin/service postgresql start
```
