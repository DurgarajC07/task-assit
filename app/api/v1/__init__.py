"""
API v1 Router
=============

Consolidated router for all v1 API endpoints.
"""

from fastapi import APIRouter
from app.api import auth, tasks, chat, websocket

# Create v1 router
api_v1_router = APIRouter()

# Include all endpoint routers
api_v1_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_v1_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"]
)

api_v1_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

api_v1_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)

__all__ = ["api_v1_router"]
