"""User session model."""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, Index

from app.database import Base
from app.database_utils import GUID
from app.config import settings


class UserSession(Base):
    """User session model for authentication."""

    __tablename__ = "user_sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("idx_user_expires", "user_id", "expires_at"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"

    @classmethod
    def create_expiry(cls) -> datetime:
        """Create expiry time based on refresh token days."""
        return datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
