"""Task API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.database import get_db
from app.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatistics,
)
from app.services import TaskService
from app.core import get_current_user
from app.models import User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=dict)
async def create_task(
    request: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    try:
        service = TaskService(db)
        result = await service.create_task(
            user_id=current_user.id,
            task_data={
                "title": request.title,
                "description": request.description,
                "priority": request.priority.value,
                "due_date": request.due_date.isoformat() if request.due_date else None,
                "tags": request.tags,
            },
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("", response_model=dict)
async def list_tasks(
    status_filter: str = None,
    priority: str = None,
    filter_type: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user tasks with optional filtering."""
    try:
        service = TaskService(db)
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if priority:
            filters["priority"] = priority
        if filter_type:
            filters["filter_type"] = filter_type

        result = await service.get_tasks(
            user_id=current_user.id,
            filters=filters,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/stats", response_model=dict)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get task statistics."""
    try:
        service = TaskService(db)
        result = await service.get_statistics(
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/search", response_model=dict)
async def search_tasks(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search tasks."""
    try:
        service = TaskService(db)
        result = await service.agent.search_tasks(
            user_id=current_user.id,
            query=q,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task."""
    try:
        service = TaskService(db)
        result = await service.get_task(
            user_id=current_user.id,
            task_id=task_id,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: uuid.UUID,
    request: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    try:
        service = TaskService(db)
        updates = {}
        if request.title:
            updates["title"] = request.title
        if request.description:
            updates["description"] = request.description
        if request.priority:
            updates["priority"] = request.priority.value
        if request.due_date:
            updates["due_date"] = request.due_date.isoformat()
        if request.status:
            updates["status"] = request.status.value
        if request.tags:
            updates["tags"] = request.tags

        result = await service.update_task(
            user_id=current_user.id,
            task_id=task_id,
            updates=updates,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/{task_id}/complete", response_model=dict)
async def complete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark task as complete."""
    try:
        service = TaskService(db)
        result = await service.agent.execute(
            action="complete",
            user_id=current_user.id,
            task_id=task_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task (soft delete)."""
    try:
        service = TaskService(db)
        result = await service.delete_task(
            user_id=current_user.id,
            task_id=task_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
