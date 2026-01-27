"""Custom exceptions for the application."""


class TaskAssistantException(Exception):
    """Base exception for task assistant."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: str = ""):
        """Initialize exception."""
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class TaskNotFoundException(TaskAssistantException):
    """Raised when a task is not found."""

    def __init__(self, task_id: str = "", details: str = ""):
        """Initialize exception."""
        super().__init__(
            f"Task not found: {task_id}",
            code="TASK_NOT_FOUND",
            details=details or "No tasks found matching your criteria.",
        )


class UserNotFoundException(TaskAssistantException):
    """Raised when a user is not found."""

    def __init__(self, username: str = ""):
        """Initialize exception."""
        super().__init__(
            f"User not found: {username}",
            code="USER_NOT_FOUND",
            details="Invalid credentials or user does not exist.",
        )


class UnauthorizedAccessException(TaskAssistantException):
    """Raised when unauthorized access is attempted."""

    def __init__(self, message: str = ""):
        """Initialize exception."""
        super().__init__(
            message or "Unauthorized access",
            code="UNAUTHORIZED",
            details="You don't have permission to access this resource.",
        )


class ValidationException(TaskAssistantException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str = ""):
        """Initialize exception."""
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details=f"Invalid value for field: {field}" if field else message,
        )


class IntentUnclearException(TaskAssistantException):
    """Raised when intent cannot be determined."""

    def __init__(self, clarification_question: str = ""):
        """Initialize exception."""
        super().__init__(
            "I'm not sure what you want to do.",
            code="INTENT_UNCLEAR",
            details=clarification_question
            or "Could you please provide more details?",
        )


class DuplicateResourceException(TaskAssistantException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource_type: str, identifier: str):
        """Initialize exception."""
        super().__init__(
            f"{resource_type} already exists: {identifier}",
            code="DUPLICATE_RESOURCE",
            details=f"A {resource_type} with this identifier already exists.",
        )


class InternalServerException(TaskAssistantException):
    """Raised for internal server errors."""

    def __init__(self, message: str = ""):
        """Initialize exception."""
        super().__init__(
            message or "An unexpected error occurred",
            code="INTERNAL_ERROR",
            details="Please try again later or contact support.",
        )
