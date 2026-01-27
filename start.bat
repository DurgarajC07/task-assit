@echo off
REM Startup script for Task Assistant (Windows)

echo 🚀 Task Assistant - Startup Script
echo ==================================

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env and add your ANTHROPIC_API_KEY
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo ✓ Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q -r requirements.txt

REM Initialize database
echo 🗄️  Initializing database...
python -c "^
import asyncio^
from app.database import init_db^
asyncio.run(init_db())^
print('✓ Database initialized')^
"

REM Check for seed flag
if "%1"=="--seed" (
    echo 🌱 Seeding database with sample data...
    python seed_database.py
)

REM Start server
echo.
echo ✨ Starting Task Assistant API...
echo 📍 Swagger UI: http://localhost:8000/docs
echo 📍 ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
