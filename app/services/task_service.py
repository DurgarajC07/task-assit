"""Task service."""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from datetime import datetime
import logging

from app.models.task import Task, TaskStatus, TaskPriority
from app.core.tenant_context import get_tenant_context, get_user_context

logger = logging.getLogger(__name__)


class TaskService:
    """Task service for managing tasks."""

    def __init__(self, db: AsyncSession):
        """Initialize task service.

        Args:
            db: Database session.
        """
        self.db = db

    async def create_task(
        self,
        user_id: UUID,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new task.
        
        Args:
            user_id: User ID
            task_data: Task creation data
            
        Returns:
            Created task data
        """
        try:
            tenant_id = get_tenant_context()
            
            task = Task(
                tenant_id=tenant_id,
                user_id=user_id,
                title=task_data.get("title"),
                description=task_data.get("description"),
                status=TaskStatus(task_data.get("status", "pending")),
                priority=TaskPriority(task_data.get("priority", "medium")),
                due_date=task_data.get("due_date"),
                tags=task_data.get("tags", []),
                metadata=task_data.get("metadata", {})
            )
            
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"Created task {task.id} for user {user_id}")
            return {
                "success": True,
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    async def get_tasks(
        self,
        user_id: UUID,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get tasks for a user.
        
        Args:
            user_id: User ID
            filters: Optional filters (status, priority, etc.)
            
        Returns:
            List of tasks
        """
        try:
            tenant_id = get_tenant_context()
            filters = filters or {}
            
            # Build query
            conditions = [
                Task.tenant_id == tenant_id,
                Task.user_id == user_id,
                Task.deleted_at.is_(None)
            ]
            
            if "status" in filters:
                conditions.append(Task.status == TaskStatus(filters["status"]))
            
            if "priority" in filters:
                conditions.append(Task.priority == TaskPriority(filters["priority"]))
            
            query = select(Task).where(and_(*conditions)).order_by(desc(Task.created_at))
            
            if "limit" in filters:
                query = query.limit(filters["limit"])
            
            if "offset" in filters:
                query = query.offset(filters["offset"])
            
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            return {
                "success": True,
                "tasks": [
                    {
                        "id": str(task.id),
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "priority": task.priority.value,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "created_at": task.created_at.isoformat()
                    }
                    for task in tasks
                ],
                "count": len(tasks)
            }
        except Exception as e:
            logger.error(f"Error getting tasks: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tasks": [],
                "count": 0
            }

    async def get_task(
        self,
        user_id: UUID,
        task_id: UUID
    ) -> Dict[str, Any]:
        """Get a single task.
        
        Args:
            user_id: User ID
            task_id: Task ID
            
        Returns:
            Task data
        """
        try:
            tenant_id = get_tenant_context()
            
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.tenant_id == tenant_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None)
                    )
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            return {
                "success": True,
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting task: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def update_task(
        self,
        user_id: UUID,
        task_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a task.
        
        Args:
            user_id: User ID
            task_id: Task ID
            updates: Update data
            
        Returns:
            Updated task data
        """
        try:
            tenant_id = get_tenant_context()
            
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.tenant_id == tenant_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None)
                    )
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            # Apply updates
            if "title" in updates:
                task.title = updates["title"]
            if "description" in updates:
                task.description = updates["description"]
            if "status" in updates:
                task.status = TaskStatus(updates["status"])
            if "priority" in updates:
                task.priority = TaskPriority(updates["priority"])
            if "due_date" in updates:
                task.due_date = updates["due_date"]
            if "tags" in updates:
                task.tags = updates["tags"]
            
            task.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"Updated task {task_id}")
            return {
                "success": True,
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "updated_at": task.updated_at.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error updating task: {e}", exc_info=True)
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_task(
        self,
        user_id: UUID,
        task_id: UUID
    ) -> Dict[str, Any]:
        """Delete a task (soft delete).
        
        Args:
            user_id: User ID
            task_id: Task ID
            
        Returns:
            Success status
        """
        try:
            tenant_id = get_tenant_context()
            
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.tenant_id == tenant_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None)
                    )
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return {
                    "success": False,
                    "error": "Task not found"
                }
            
            task.deleted_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info(f"Deleted task {task_id}")
            return {
                "success": True,
                "message": "Task deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting task: {e}", exc_info=True)
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    async def get_statistics(self, user_id):
        """Get task statistics."""
        return await self.agent.execute(
            action="statistics",
            user_id=user_id,
        )
