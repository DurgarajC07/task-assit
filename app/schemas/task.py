"""Task schemas."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid
from typing import Optional, List
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base task schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list, max_items=20)

    @field_validator('priority', mode='before')
    @classmethod
    def normalize_priority(cls, v):
        """Normalize priority to lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator('due_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date strings - accept both date-only and datetime formats."""
        if isinstance(v, str):
            # If it's a date-only string like "2026-01-29", add time
            if 'T' not in v and ' ' not in v and len(v) == 10:
                v = f"{v}T00:00:00"
            return datetime.fromisoformat(v)
        return v


class TaskCreate(TaskBase):
    """Task creation schema."""

    pass


class TaskUpdate(BaseModel):
    """Task update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    status: Optional[TaskStatus] = None

    @field_validator('priority', 'status', mode='before')
    @classmethod
    def normalize_enums(cls, v):
        """Normalize enum values to lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator('due_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date strings - accept both date-only and datetime formats."""
        if isinstance(v, str):
            # If it's a date-only string like "2026-01-29", add time
            if 'T' not in v and ' ' not in v and len(v) == 10:
                v = f"{v}T00:00:00"
            return datetime.fromisoformat(v)
        return v


class TaskResponse(TaskBase):
    """Task response schema."""

    id: uuid.UUID
    user_id: uuid.UUID
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class TaskListFilters(BaseModel):
    """Task list filters schema."""

    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    filter_type: Optional[str] = None  # today, this_week, pending, etc.


class TaskStatistics(BaseModel):
    """Task statistics schema."""

    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    cancelled_tasks: int
    overdue_tasks: int
    completion_rate: float
    average_completion_time: Optional[float] = None
