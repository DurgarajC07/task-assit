"""User model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Index
from app.database import Base
from app.database_utils import GUID


class User(Base):
    """User model for task assistant."""

    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        nullable=False
    )
    preferences = Column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_email", "email"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username={self.username})>"
