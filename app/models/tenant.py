"""Tenant model for multi-tenancy."""
from sqlalchemy import Column, String, Boolean, JSON, Index, Enum as SQLEnum, Integer
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, GUID
import uuid


class TenantStatus(str, enum.Enum):
    """Tenant status enum."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class Tenant(BaseModel, SoftDeleteMixin):
    """Tenant model for multi-tenancy.
    
    Each tenant represents a separate customer/organization.
    All user data is isolated by tenant_id.
    """
    
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(TenantStatus),
        default=TenantStatus.TRIAL,
        nullable=False,
        index=True
    )
    
    # Relationships (will be populated from plan_id)
    plan_id = Column(GUID, nullable=True)  # Will add FK after BillingPlan is defined
    
    # Settings
    settings = Column(JSON, default=dict, nullable=False)
    
    # Metadata
    domain = Column(String(255), nullable=True)  # Custom domain
    logo_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Quotas
    max_users = Column(Integer, default=10, nullable=False)
    max_agents = Column(Integer, default=5, nullable=False)
    monthly_token_quota = Column(Integer, default=100000, nullable=False)
    
    # Relationships
    # users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    # providers = relationship("Provider", back_populates="tenant", cascade="all, delete-orphan")
    # agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_tenants_status", "status"),
        Index("idx_tenants_slug", "slug"),
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, slug={self.slug})>"
