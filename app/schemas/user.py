"""User schemas."""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, max_length=255)


class UserLogin(BaseModel):
    """User login schema."""

    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)


class UserResponse(UserBase):
    """User response schema."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    preferences: dict = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse" = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class TokenData(BaseModel):
    """Token data schema."""

    user_id: uuid.UUID
    username: str
