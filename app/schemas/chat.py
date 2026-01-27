"""Chat schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[uuid.UUID] = None


class IntentEntity(BaseModel):
    """Intent entity schema."""

    intent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    clarification_needed: bool = False
    clarification_question: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response schema."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(BaseModel):
    """Conversation message schema."""

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    message: str
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ConversationHistory(BaseModel):
    """Conversation history schema."""

    messages: List[ConversationMessage]
    session_id: uuid.UUID
    total_messages: int
