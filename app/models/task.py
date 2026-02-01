"""Task model with multi-tenant support."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
    JSON,
    ForeignKey,
    Index,
)
from enum import Enum as PyEnum
from app.models.base import TenantModel, GUID


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


class Task(TenantModel):
    """Task model for task assistant with tenant isolation."""

    __tablename__ = "tasks"

    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        GUID,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority = Column(
        SQLEnum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    
    due_date = Column(DateTime, nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)
    
    # Assignment
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Completion tracking
    completed_at = Column(DateTime, nullable=True)
    
    # Additional info
    task_metadata = Column(JSON, default=dict, nullable=False)
    # Can store: source="ai", parent_task_id, etc.
    
    # Relationships
    # user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    # project = relationship("Project", back_populates="tasks")
    # assigned_user = relationship("User", foreign_keys=[assigned_to])

    __table_args__ = (
        Index("idx_tasks_tenant_user", "tenant_id", "user_id"),
        Index("idx_tasks_tenant_status", "tenant_id", "status"),
        Index("idx_tasks_tenant_priority", "tenant_id", "priority"),
        Index("idx_tasks_tenant_due_date", "tenant_id", "due_date"),
        Index("idx_tasks_assigned", "assigned_to"),
        Index("idx_tasks_project", "project_id"),
        Index("idx_tasks_composite", "tenant_id", "user_id", "status", "priority"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task(id={self.id}, title={self.title}, user_id={self.user_id}, tenant_id={self.tenant_id})>"
