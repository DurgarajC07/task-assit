"""Chat API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services import ChatService
from app.core import get_current_user
from app.models import User

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process natural language chat message."""
    try:
        service = ChatService(db)
        session_id = request.session_id or uuid.uuid4()

        result = await service.process_message(
            user_id=current_user.id,
            message=request.message,
            session_id=session_id,
        )

        return ChatResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            data=result.get("data"),
            error=result.get("error"),
            intent=result.get("intent"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/history")
async def get_conversation_history(
    session_id: uuid.UUID = Query(...),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation history for a session."""
    try:
        service = ChatService(db)
        result = await service.get_history(
            user_id=current_user.id,
            session_id=session_id,
            limit=limit,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
