"""Validation utilities."""
from typing import List
from app.core.exceptions import ValidationException


def validate_task_title(title: str) -> str:
    """Validate task title."""
    if not title:
        raise ValidationException("Task title cannot be empty", "title")
    if len(title) > 255:
        raise ValidationException(
            "Task title cannot exceed 255 characters",
            "title",
        )
    return title.strip()


def validate_tags(tags: List[str]) -> List[str]:
    """Validate task tags."""
    if not isinstance(tags, list):
        raise ValidationException("Tags must be a list", "tags")

    if len(tags) > 20:
        raise ValidationException("Maximum 20 tags allowed", "tags")

    validated_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValidationException("Each tag must be a string", "tags")
        tag = tag.strip().lower()
        if tag and len(tag) <= 50:
            validated_tags.append(tag)

    return validated_tags


def validate_priority(priority: str) -> str:
    """Validate priority value."""
    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority not in valid_priorities:
        raise ValidationException(
            f"Priority must be one of {valid_priorities}",
            "priority",
        )
    return priority


def validate_status(status: str) -> str:
    """Validate status value."""
    valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
    if status not in valid_statuses:
        raise ValidationException(
            f"Status must be one of {valid_statuses}",
            "status",
        )
    return status
