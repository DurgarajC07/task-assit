"""Conversation and message models (refactored for multi-tenant)."""
from sqlalchemy import Column, String, Text, Index, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum
from app.models.base import TenantModel, BaseModel, GUID


class ConversationStatus(str, enum.Enum):
    """Conversation status enum."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(TenantModel):
    """Conversation model for chat history."""
    
    __tablename__ = "conversations"
    
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(500), nullable=True)  # Auto-generated or user-provided
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False, index=True)
    
    # Statistics
    message_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    # user = relationship("User", back_populates="conversations")
    # agent = relationship("Agent")
    # messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_conversations_tenant_user", "tenant_id", "user_id"),
        Index("idx_conversations_agent", "agent_id"),
        Index("idx_conversations_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, messages={self.message_count})>"


class MessageRole(str, enum.Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"


class Message(BaseModel):
    """Individual message within a conversation."""
    
    __tablename__ = "messages"
    
    conversation_id = Column(GUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(SQLEnum(MessageRole), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # For function/tool calls
    function_call = Column(JSON, nullable=True)  # Function call details
    tool_calls = Column(JSON, nullable=True)  # Multiple tool calls
    
    # Additional info
    message_metadata = Column(JSON, default=dict, nullable=False)
    # Can store: model, temperature, tokens, cost, etc.
    
    # Relationships
    # conversation = relationship("Conversation", back_populates="messages")
    
    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created", "created_at"),
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
