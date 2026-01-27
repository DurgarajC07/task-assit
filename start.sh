#!/bin/bash
# Startup script for Task Assistant

set -e

echo "🚀 Task Assistant - Startup Script"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your ANTHROPIC_API_KEY"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
print('✓ Database initialized')
"

# Optionally seed database
if [ "$1" == "--seed" ]; then
    echo "🌱 Seeding database with sample data..."
    python seed_database.py
fi

# Start server
echo ""
echo "✨ Starting Task Assistant API..."
echo "📍 Swagger UI: http://localhost:8000/docs"
echo "📍 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
