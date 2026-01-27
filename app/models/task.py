"""Task model."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Enum,
    JSON,
    ForeignKey,
    Index,
)
from enum import Enum as PyEnum
from app.database import Base
from app.database_utils import GUID


class TaskStatus(str, PyEnum):
    """Task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, PyEnum):
    """Task priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    """Task model for task assistant."""

    __tablename__ = "tasks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    due_date = Column(DateTime, nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        nullable=False
    )
    completed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)

    __table_args__ = (
        Index("idx_user_id_status", "user_id", "status"),
        Index("idx_user_id_due_date", "user_id", "due_date"),
        Index("idx_user_id_priority", "user_id", "priority"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task(id={self.id}, title={self.title}, user_id={self.user_id})>"
