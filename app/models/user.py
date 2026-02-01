"""User model with multi-tenant support."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Index, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TenantModel, GUID


class User(TenantModel):
    """User model for task assistant with tenant isolation."""

    __tablename__ = "users"

    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Status
    status = Column(String(50), default="active", nullable=False, index=True)  # active, inactive, suspended
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Preferences
    preferences = Column(JSON, default=dict, nullable=False)
    
    # Metadata
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # Support IPv6
    
    # Relationships
    # tenant = relationship("Tenant", back_populates="users")
    # roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    # tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    # conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_tenant_username", "tenant_id", "username", unique=True),
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
        Index("idx_users_status", "status"),
        Index("idx_users_email_verified", "email_verified"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username={self.username}, tenant_id={self.tenant_id})>"
