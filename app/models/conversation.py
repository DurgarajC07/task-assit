"""Conversation history model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, JSON, ForeignKey, Index

from enum import Enum as PyEnum
from app.database import Base
from app.database_utils import GUID


class MessageRole(str, PyEnum):
    """Message role enum."""

    USER = "user"
    ASSISTANT = "assistant"


class ConversationHistory(Base):
    """Conversation history model."""

    __tablename__ = "conversation_history"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(GUID, nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    message = Column(Text, nullable=False)
    intent = Column(String(255), nullable=True)
    entities = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_user_session", "user_id", "session_id"),
        Index("idx_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConversationHistory(id={self.id}, role={self.role})>"
