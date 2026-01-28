"""Task management agent."""
from typing import Any, Dict, Optional, List
import uuid
import logging
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base_agent import BaseAgent
from app.models import Task, TaskStatus, TaskPriority, TaskAuditLog, AuditAction
from app.core.exceptions import TaskNotFoundException, ValidationException
from app.utils import (
    validate_task_title,
    validate_tags,
    parse_natural_date,
    combine_date_and_time,
    get_date_range_for_filter,
    is_overdue,
)

logger = logging.getLogger(__name__)


class TaskManagementAgent(BaseAgent):
    """Task management agent for CRUD operations."""

    def __init__(self, db: AsyncSession):
        """Initialize task management agent.

        Args:
            db: Database session.
        """
        super().__init__("TaskManagementAgent")
        self.db = db

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute task management operation.

        Args:
            **kwargs: Operation parameters (action, user_id, task_data, etc.)

        Returns:
            Result dictionary.
        """
        action = kwargs.get("action")
        user_id = kwargs.get("user_id")

        if not action or not user_id:
            return {"success": False, "error": "Missing required parameters"}

        try:
            if action == "create":
                return await self.create_task(user_id, kwargs.get("task_data", {}))
            elif action == "list":
                return await self.get_tasks(user_id, kwargs.get("filters", {}))
            elif action == "get":
                return await self.get_task(
                    user_id, kwargs.get("task_id") or kwargs.get("task_identifier")
                )
            elif action == "update":
                return await self.update_task(
                    user_id, kwargs.get("task_id"), kwargs.get("updates", {})
                )
            elif action == "complete":
                return await self.complete_task(
                    user_id, kwargs.get("task_id"), kwargs.get("completion_action")
                )
            elif action == "delete":
                return await self.delete_task(user_id, kwargs.get("task_id"))
            elif action == "search":
                return await self.search_tasks(user_id, kwargs.get("query", ""))
            elif action == "statistics":
                return await self.get_statistics(user_id)
            elif action == "bulk_delete":
                return await self.bulk_delete_tasks(user_id, kwargs.get("criteria", {}))
            elif action == "bulk_update":
                return await self.bulk_update_tasks(
                    user_id, kwargs.get("criteria", {}), kwargs.get("updates", {})
                )
            elif action == "bulk_complete":
                return await self.bulk_complete_tasks(user_id, kwargs.get("criteria", {}))
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_task(
        self,
        user_id: uuid.UUID,
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new task.

        Args:
            user_id: User ID.
            task_data: Task data from intent agent entities.

        Returns:
            Created task data.
        """
        try:
            logger.info(f"Creating task with data: {task_data}")
            
            # Validate and extract data
            title = validate_task_title(task_data.get("title", ""))
            description = task_data.get("description", "").strip() or None
            
            # Normalize priority to lowercase
            priority_str = task_data.get("priority", "medium")
            if isinstance(priority_str, str):
                priority_str = priority_str.lower()
            priority = TaskPriority(priority_str)
            
            tags = validate_tags(task_data.get("tags", []))

            # Parse due date and time with better logging
            due_date = None
            if task_data.get("due_date"):
                due_date_str = task_data.get("due_date")
                logger.debug(f"Parsing due date: '{due_date_str}'")
                parsed_date = parse_natural_date(due_date_str)
                
                if parsed_date:
                    time_str = task_data.get("due_time", "")
                    logger.debug(f"Combining with time: '{time_str}'")
                    due_date = combine_date_and_time(parsed_date, time_str)
                    logger.info(f"Final due date: {due_date}")
                else:
                    logger.warning(f"Could not parse date: '{due_date_str}'")

            # Create task
            task = Task(
                user_id=user_id,
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                tags=tags,
                status=TaskStatus.PENDING,
            )

            self.db.add(task)
            await self.db.flush()

            # Log audit
            await self._log_audit(
                task.id,
                user_id,
                AuditAction.CREATED,
                None,
                self._task_to_dict(task),
            )

            await self.db.commit()
            
            logger.info(f"Task created successfully: {task.id}")

            return {
                "success": True,
                "message": f"Task '{title}' created successfully!",
                "data": self._task_to_dict(task),
            }

        except ValidationException as e:
            logger.error(f"Validation error creating task: {e.message}")
            return {"success": False, "error": e.message, "details": e.details}
        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def get_tasks(
        self,
        user_id: uuid.UUID,
        filters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Get tasks with optional filtering.

        Args:
            user_id: User ID.
            filters: Filter criteria.

        Returns:
            List of tasks.
        """
        try:
            filters = filters or {}
            query = select(Task).where(
                and_(Task.user_id == user_id, Task.deleted_at.is_(None))
            )

            # Apply filters
            if filters.get("status"):
                query = query.where(Task.status == TaskStatus(filters["status"]))

            if filters.get("priority"):
                query = query.where(
                    Task.priority == TaskPriority(filters["priority"])
                )

            if filters.get("filter_type"):
                date_range = get_date_range_for_filter(filters["filter_type"])
                if date_range[0]:
                    query = query.where(Task.due_date >= date_range[0])
                if date_range[1]:
                    query = query.where(Task.due_date < date_range[1])

            if filters.get("due_date_from"):
                query = query.where(Task.due_date >= filters["due_date_from"])

            if filters.get("due_date_to"):
                query = query.where(Task.due_date <= filters["due_date_to"])

            if filters.get("tags"):
                for tag in filters["tags"]:
                    query = query.where(Task.tags.contains([tag]))

            # Apply sorting
            sort_by = filters.get("sort_by", "due_date")
            sort_order = filters.get("sort_order", "asc")
            
            if sort_by == "created_at":
                if sort_order == "desc":
                    query = query.order_by(Task.created_at.desc())
                else:
                    query = query.order_by(Task.created_at)
            elif sort_by == "updated_at":
                if sort_order == "desc":
                    query = query.order_by(Task.updated_at.desc())
                else:
                    query = query.order_by(Task.updated_at)
            else:
                # Default: order by due date and priority
                query = query.order_by(Task.due_date, Task.priority)

            result = await self.db.execute(query)
            tasks = result.scalars().all()

            return {
                "success": True,
                "message": f"Retrieved {len(tasks)} task(s)",
                "data": {
                    "tasks": [self._task_to_dict(task) for task in tasks],
                    "total_count": len(tasks),
                    "filters_applied": list(filters.keys()),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_task(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID = None,
        task_identifier: str = None,
    ) -> Dict[str, Any]:
        """Get a single task by ID or identifier.

        Args:
            user_id: User ID.
            task_id: Task UUID.
            task_identifier: Task title or partial identifier.

        Returns:
            Task data.
        """
        try:
            if task_id:
                query = select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                    )
                )
            elif task_identifier:
                query = select(Task).where(
                    and_(
                        or_(
                            Task.title.ilike(f"%{task_identifier}%"),
                            Task.description.ilike(f"%{task_identifier}%"),
                        ),
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                    )
                )
            else:
                return {"success": False, "error": "Task ID or identifier required"}

            result = await self.db.execute(query)
            task = result.scalar_one_or_none()

            if not task:
                raise TaskNotFoundException(
                    str(task_id or task_identifier),
                    "No task found matching your criteria",
                )

            return {"success": True, "data": self._task_to_dict(task)}

        except TaskNotFoundException as e:
            return {"success": False, "error": e.message, "code": e.code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def update_task(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a task.

        Args:
            user_id: User ID.
            task_id: Task ID.
            updates: Fields to update.

        Returns:
            Updated task data.
        """
        try:
            # Get existing task
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                    )
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                raise TaskNotFoundException(str(task_id))

            # Store old values for audit
            old_values = self._task_to_dict(task)

            # Apply updates
            if "title" in updates and updates["title"]:
                task.title = validate_task_title(updates["title"])

            if "description" in updates:
                task.description = updates["description"].strip() or None

            if "priority" in updates and updates["priority"]:
                priority_str = updates["priority"]
                if isinstance(priority_str, str):
                    priority_str = priority_str.lower()
                task.priority = TaskPriority(priority_str)

            if "status" in updates and updates["status"]:
                status_str = updates["status"]
                if isinstance(status_str, str):
                    status_str = status_str.lower()
                task.status = TaskStatus(status_str)
                if status_str == "completed":
                    task.completed_at = datetime.utcnow()

            if "due_date" in updates:
                if updates["due_date"]:
                    parsed_date = parse_natural_date(updates["due_date"])
                    if parsed_date:
                        time_str = updates.get("due_time", "")
                        task.due_date = combine_date_and_time(parsed_date, time_str)
                else:
                    task.due_date = None

            if "tags" in updates and updates["tags"]:
                task.tags = validate_tags(updates["tags"])

            task.updated_at = datetime.utcnow()
            await self.db.flush()

            # Log audit
            await self._log_audit(
                task.id,
                user_id,
                AuditAction.UPDATED,
                old_values,
                self._task_to_dict(task),
            )

            await self.db.commit()

            return {
                "success": True,
                "message": "Task updated successfully!",
                "data": self._task_to_dict(task),
            }

        except (TaskNotFoundException, ValidationException) as e:
            return {"success": False, "error": e.message}
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def complete_task(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        completion_action: str = "complete",
    ) -> Dict[str, Any]:
        """Mark task as complete or incomplete.

        Args:
            user_id: User ID.
            task_id: Task ID.
            completion_action: "complete" or "incomplete".

        Returns:
            Updated task data.
        """
        try:
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                    )
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                raise TaskNotFoundException(str(task_id))

            old_values = self._task_to_dict(task)

            if completion_action == "complete" or completion_action is None:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                action = AuditAction.COMPLETED
            else:
                task.status = TaskStatus.PENDING
                task.completed_at = None
                action = AuditAction.UPDATED

            task.updated_at = datetime.utcnow()
            await self.db.flush()

            await self._log_audit(
                task.id,
                user_id,
                action,
                old_values,
                self._task_to_dict(task),
            )

            await self.db.commit()

            status_msg = "completed" if completion_action != "incomplete" else "marked as incomplete"
            return {
                "success": True,
                "message": f"Task '{task.title}' {status_msg}!",
                "data": self._task_to_dict(task),
            }

        except TaskNotFoundException as e:
            return {"success": False, "error": e.message}
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def delete_task(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Soft delete a task.

        Args:
            user_id: User ID.
            task_id: Task ID.

        Returns:
            Success confirmation.
        """
        try:
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.id == task_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                    )
                )
            )
            task = result.scalar_one_or_none()

            if not task:
                raise TaskNotFoundException(str(task_id))

            old_values = self._task_to_dict(task)
            task.deleted_at = datetime.utcnow()

            await self.db.flush()

            await self._log_audit(
                task.id,
                user_id,
                AuditAction.DELETED,
                old_values,
                None,
            )

            await self.db.commit()

            return {
                "success": True,
                "message": f"Task '{task.title}' deleted successfully!",
            }

        except TaskNotFoundException as e:
            return {"success": False, "error": e.message}
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def search_tasks(
        self,
        user_id: uuid.UUID,
        query: str,
    ) -> Dict[str, Any]:
        """Search tasks by keyword.

        Args:
            user_id: User ID.
            query: Search query.

        Returns:
            Matching tasks.
        """
        try:
            search_term = f"%{query}%"
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                        or_(
                            Task.title.ilike(search_term),
                            Task.description.ilike(search_term),
                        ),
                    )
                )
            )
            tasks = result.scalars().all()

            return {
                "success": True,
                "message": f"Found {len(tasks)} task(s)",
                "data": {
                    "tasks": [self._task_to_dict(task) for task in tasks],
                    "search_query": query,
                    "total_results": len(tasks),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_statistics(
        self,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Get task statistics for user.

        Args:
            user_id: User ID.

        Returns:
            Statistics data.
        """
        try:
            now = datetime.utcnow()

            # Get all tasks
            result = await self.db.execute(
                select(Task).where(
                    and_(Task.user_id == user_id, Task.deleted_at.is_(None))
                )
            )
            tasks = result.scalars().all()

            # Calculate statistics
            total = len(tasks)
            pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
            in_progress = sum(
                1 for t in tasks if t.status == TaskStatus.IN_PROGRESS
            )
            completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
            cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)
            high_priority = sum(
                1 for t in tasks if t.priority in [TaskPriority.HIGH, TaskPriority.URGENT]
                and t.status != TaskStatus.COMPLETED
            )
            overdue = sum(
                1
                for t in tasks
                if t.due_date and t.due_date < now
                and t.status != TaskStatus.COMPLETED
            )
            
            # Priority breakdown
            low_priority = sum(1 for t in tasks if t.priority == TaskPriority.LOW)
            medium_priority = sum(1 for t in tasks if t.priority == TaskPriority.MEDIUM)
            high_priority_count = sum(1 for t in tasks if t.priority == TaskPriority.HIGH)
            urgent_priority = sum(1 for t in tasks if t.priority == TaskPriority.URGENT)

            completion_rate = (
                (completed / total * 100) if total > 0 else 0
            )

            return {
                "success": True,
                "data": {
                    "statistics": {
                        "total_tasks": total,
                        "pending_tasks": pending,
                        "in_progress_tasks": in_progress,
                        "completed_tasks": completed,
                        "cancelled_tasks": cancelled,
                        "high_priority_tasks": high_priority,
                        "overdue_tasks": overdue,
                        "completion_rate": round(completion_rate, 2),
                        # Status breakdown for charts
                        "pending": pending,
                        "in_progress": in_progress,
                        "completed": completed,
                        # Priority breakdown for charts
                        "low_priority": low_priority,
                        "medium_priority": medium_priority,
                        "high_priority": high_priority_count,
                        "urgent_priority": urgent_priority,
                    }
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_task_by_description(
        self,
        user_id: uuid.UUID,
        description: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a task by fuzzy description match.

        Args:
            user_id: User ID.
            description: Description to search.

        Returns:
            First matching task or None.
        """
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.deleted_at.is_(None),
                    or_(
                        Task.title.ilike(f"%{description}%"),
                        Task.description.ilike(f"%{description}%"),
                    ),
                )
            )
        )
        task = result.scalar_one_or_none()
        return self._task_to_dict(task) if task else None

    @staticmethod
    def _task_to_dict(task: Task) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": str(task.id),
            "user_id": str(task.user_id),
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "tags": task.tags,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
        }

    async def _log_audit(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        action: AuditAction,
        old_values: Optional[Dict],
        new_values: Optional[Dict],
    ):
        """Log task audit trail.

        Args:
            task_id: Task ID.
            user_id: User ID.
            action: Audit action.
            old_values: Previous values.
            new_values: New values.
        """
        audit_log = TaskAuditLog(
            task_id=task_id,
            user_id=user_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
        )
        self.db.add(audit_log)

    async def bulk_delete_tasks(
        self,
        user_id: uuid.UUID,
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Delete multiple tasks based on criteria.

        Args:
            user_id: User ID.
            criteria: Filter criteria (status, priority, due_date_filter).

        Returns:
            Result with count of deleted tasks.
        """
        try:
            logger.info(f"Bulk delete with criteria: {criteria}")
            
            # Build query
            query = select(Task).where(
                and_(Task.user_id == user_id, Task.deleted_at.is_(None))
            )

            # Apply filters
            if criteria.get("status"):
                status = TaskStatus(criteria["status"].lower())
                query = query.where(Task.status == status)
            
            if criteria.get("priority"):
                priority = TaskPriority(criteria["priority"].lower())
                query = query.where(Task.priority == priority)
            
            if criteria.get("due_date_filter"):
                date_range = get_date_range_for_filter(criteria["due_date_filter"])
                if date_range[0]:
                    query = query.where(Task.due_date >= date_range[0])
                if date_range[1]:
                    query = query.where(Task.due_date < date_range[1])

            # Get tasks to delete
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                return {
                    "success": True,
                    "message": "No tasks match the criteria",
                    "data": {"deleted_count": 0}
                }

            # Soft delete
            from datetime import datetime
            deleted_count = 0
            for task in tasks:
                task.deleted_at = datetime.utcnow()
                await self._log_audit(
                    task.id,
                    user_id,
                    AuditAction.DELETED,
                    self._task_to_dict(task),
                    None,
                )
                deleted_count += 1

            await self.db.commit()
            
            logger.info(f"Bulk deleted {deleted_count} tasks")

            return {
                "success": True,
                "message": f"Successfully deleted {deleted_count} task(s)",
                "data": {
                    "deleted_count": deleted_count,
                    "criteria": criteria
                }
            }

        except Exception as e:
            logger.error(f"Bulk delete error: {e}", exc_info=True)
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def bulk_update_tasks(
        self,
        user_id: uuid.UUID,
        criteria: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update multiple tasks based on criteria.

        Args:
            user_id: User ID.
            criteria: Filter criteria.
            updates: Fields to update.

        Returns:
            Result with count of updated tasks.
        """
        try:
            logger.info(f"Bulk update with criteria: {criteria}, updates: {updates}")
            
            # Build query
            query = select(Task).where(
                and_(Task.user_id == user_id, Task.deleted_at.is_(None))
            )

            # Apply filters
            if criteria.get("status"):
                status = TaskStatus(criteria["status"].lower())
                query = query.where(Task.status == status)
            
            if criteria.get("priority"):
                priority = TaskPriority(criteria["priority"].lower())
                query = query.where(Task.priority == priority)
            
            if criteria.get("due_date_filter"):
                date_range = get_date_range_for_filter(criteria["due_date_filter"])
                if date_range[0]:
                    query = query.where(Task.due_date >= date_range[0])
                if date_range[1]:
                    query = query.where(Task.due_date < date_range[1])

            # Get tasks to update
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                return {
                    "success": True,
                    "message": "No tasks match the criteria",
                    "data": {"updated_count": 0}
                }

            # Update tasks
            updated_count = 0
            for task in tasks:
                old_values = self._task_to_dict(task)
                
                if updates.get("priority"):
                    task.priority = TaskPriority(updates["priority"].lower())
                if updates.get("status"):
                    task.status = TaskStatus(updates["status"].lower())
                if updates.get("title"):
                    task.title = updates["title"]
                if updates.get("description"):
                    task.description = updates["description"]
                if updates.get("due_date"):
                    parsed_date = parse_natural_date(updates["due_date"])
                    if parsed_date:
                        task.due_date = parsed_date
                if updates.get("tags"):
                    task.tags = validate_tags(updates["tags"])
                
                task.updated_at = datetime.utcnow()
                
                await self._log_audit(
                    task.id,
                    user_id,
                    AuditAction.UPDATED,
                    old_values,
                    self._task_to_dict(task),
                )
                updated_count += 1

            await self.db.commit()
            
            logger.info(f"Bulk updated {updated_count} tasks")

            return {
                "success": True,
                "message": f"Successfully updated {updated_count} task(s)",
                "data": {
                    "updated_count": updated_count,
                    "criteria": criteria,
                    "updates": updates
                }
            }

        except Exception as e:
            logger.error(f"Bulk update error: {e}", exc_info=True)
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def bulk_complete_tasks(
        self,
        user_id: uuid.UUID,
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mark multiple tasks as complete based on criteria.

        Args:
            user_id: User ID.
            criteria: Filter criteria.

        Returns:
            Result with count of completed tasks.
        """
        try:
            logger.info(f"Bulk complete with criteria: {criteria}")
            
            # Build query
            query = select(Task).where(
                and_(
                    Task.user_id == user_id,
                    Task.deleted_at.is_(None),
                    Task.status != TaskStatus.COMPLETED
                )
            )

            # Apply filters
            if criteria.get("status"):
                status = TaskStatus(criteria["status"].lower())
                query = query.where(Task.status == status)
            
            if criteria.get("priority"):
                priority = TaskPriority(criteria["priority"].lower())
                query = query.where(Task.priority == priority)
            
            if criteria.get("due_date_filter"):
                date_range = get_date_range_for_filter(criteria["due_date_filter"])
                if date_range[0]:
                    query = query.where(Task.due_date >= date_range[0])
                if date_range[1]:
                    query = query.where(Task.due_date < date_range[1])

            # Get tasks to complete
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                return {
                    "success": True,
                    "message": "No tasks to complete",
                    "data": {"completed_count": 0}
                }

            # Mark as complete
            from datetime import datetime
            completed_count = 0
            for task in tasks:
                old_values = self._task_to_dict(task)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                
                await self._log_audit(
                    task.id,
                    user_id,
                    AuditAction.UPDATED,
                    old_values,
                    self._task_to_dict(task),
                )
                completed_count += 1

            await self.db.commit()
            
            logger.info(f"Bulk completed {completed_count} tasks")

            return {
                "success": True,
                "message": f"Successfully completed {completed_count} task(s)",
                "data": {
                    "completed_count": completed_count,
                    "criteria": criteria
                }
            }

        except Exception as e:
            logger.error(f"Bulk complete error: {e}", exc_info=True)
            await self.db.rollback()
            return {"success": False, "error": str(e)}
