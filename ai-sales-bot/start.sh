#!/bin/bash
# ═══════════════════════════════════════════════════
# AI Sales Bot - Quick Start Script (WSL/Linux)
# ═══════════════════════════════════════════════════

set -e
cd "$(dirname "$0")"

echo "🤖 AI Sales Bot - Starting..."
echo "═══════════════════════════════════════"

# 1. Start PostgreSQL
echo "📦 Starting PostgreSQL..."
if command -v pg_isready &>/dev/null; then
    if ! pg_isready -q 2>/dev/null; then
        sudo service postgresql start
        sleep 2
    fi
    echo "   ✅ PostgreSQL is running"
else
    echo "   ⚠️  PostgreSQL not found. Install it or use Docker."
fi

# 2. Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Virtual environment activated"
else
    echo "   📦 Creating virtual environment..."
    python3.11 -m venv venv || python3 -m venv venv
    source venv/bin/activate
    echo "   📦 Installing dependencies..."
    pip install --upgrade pip -q
    pip install -r backend/requirements.txt -q
    echo "   ✅ Dependencies installed"
fi

# 3. Check .env
if [ ! -f ".env" ]; then
    echo "   ⚠️  .env not found! Copying from .env.example..."
    cp .env.example .env
    echo "   📝 Please edit .env with your API keys!"
    echo "      nano .env"
fi

# 4. Run server
echo ""
echo "═══════════════════════════════════════"
echo "🚀 Starting server..."
echo "📊 Dashboard:  http://localhost:8000"
echo "📖 API Docs:   http://localhost:8000/docs"
echo "═══════════════════════════════════════"
echo ""

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
