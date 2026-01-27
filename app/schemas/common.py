"""Common schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class APIResponse(BaseModel):
    """Generic API response schema."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __init__(self, **data):
        """Initialize with default timestamp."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class ErrorResponse(BaseModel):
    """Error response schema."""

    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime = None

    def __init__(self, **data):
        """Initialize with default timestamp."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class PaginationParams(BaseModel):
    """Pagination parameters schema."""

    skip: int = 0
    limit: int = 100
