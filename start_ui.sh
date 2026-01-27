#!/bin/bash

# Task Assistant UI Setup Script

echo "========================================="
echo "Task Assistant UI - Professional Setup"
echo "========================================="
echo ""

# Check if running from correct directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "✓ Project structure verified"
echo ""

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Display startup information
echo "========================================="
echo "PROFESSIONAL UI FEATURES"
echo "========================================="
echo ""
echo "✓ Modular JavaScript Architecture"
echo "  - auth.js: Authentication & form switching"
echo "  - tasks.js: Task management operations"
echo "  - chat.js: AI chat functionality"
echo "  - ui.js: Shared UI utilities"
echo "  - api.js: Backend API client"
echo "  - websocket.js: Real-time communication"
echo "  - app.js: Main initialization"
echo ""
echo "✓ Professional UI Components"
echo "  - Single-page application"
echo "  - Login/Register with form switching"
echo "  - Task dashboard with stats"
echo "  - AI chat assistant"
echo "  - Task management (create, update, delete)"
echo "  - Real-time updates via WebSocket"
echo ""
echo "✓ Security Features"
echo "  - Bearer token authentication"
echo "  - Secure password handling"
echo "  - XSS prevention (HTML escaping)"
echo "  - CORS enabled"
echo ""
echo "========================================="
echo "STARTING SERVER"
echo "========================================="
echo ""
echo "Server will start on: http://localhost:8000"
echo "Access UI at: http://localhost:8000"
echo ""
echo "Demo credentials:"
echo "  Username: demo_user"
echo "  Password: demo_password_123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd /home/anvex/workspace/multiagent
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
