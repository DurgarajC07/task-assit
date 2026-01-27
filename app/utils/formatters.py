"""Response formatters."""
from typing import List, Dict, Any
from app.models.task import Task, TaskStatus, TaskPriority


def format_task_response(task: Task) -> Dict[str, Any]:
    """Format a task for API response."""
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


def format_task_list(tasks: List[Task]) -> List[Dict[str, Any]]:
    """Format a list of tasks for API response."""
    return [format_task_response(task) for task in tasks]


def format_conversation_message(
    role: str,
    message: str,
    intent: str = None,
    entities: Dict = None,
) -> Dict[str, Any]:
    """Format a conversation message."""
    return {
        "role": role,
        "message": message,
        "intent": intent,
        "entities": entities or {},
    }
