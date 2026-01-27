"""Task audit log model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum, JSON, ForeignKey, DateTime, Index

from enum import Enum as PyEnum
from app.database import Base
from app.database_utils import GUID


class AuditAction(str, PyEnum):
    """Audit action enum."""

    CREATED = "created"
    UPDATED = "updated"
    COMPLETED = "completed"
    DELETED = "deleted"


class TaskAuditLog(Base):
    """Task audit log model."""

    __tablename__ = "task_audit_log"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(
        GUID,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action = Column(Enum(AuditAction), nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_audit_task_action", "task_id", "action"),
        Index("idx_audit_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TaskAuditLog(id={self.id}, action={self.action})>"
