"""Billing and subscription models."""
from sqlalchemy import Column, String, Text, JSON, Index, Boolean, ForeignKey, Integer, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel, TenantModel, GUID


class BillingPlan(BaseModel):
    """Billing plan model."""
    
    __tablename__ = "billing_plans"
    
    name = Column(String(255), unique=True, nullable=False, index=True)  # free, starter, pro, enterprise
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Numeric(10, 2), nullable=False)  # USD
    price_yearly = Column(Numeric(10, 2), nullable=True)  # USD (annual discount)
    
    # Quotas
    token_quota_monthly = Column(Integer, default=0, nullable=False)  # 0 = unlimited
    max_users = Column(Integer, default=0, nullable=False)  # 0 = unlimited
    max_agents = Column(Integer, default=0, nullable=False)  # 0 = unlimited
    max_api_calls_per_day = Column(Integer, default=0, nullable=False)
    
    # Features (JSON array of feature keys)
    features = Column(JSON, default=dict, nullable=False)
    # Example: {
    #   "custom_agents": true,
    #   "api_access": true,
    #   "priority_support": true,
    #   "advanced_analytics": false
    # }
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_public = Column(Boolean, default=True, nullable=False)  # Show on pricing page
    
    # Display order
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Stripe integration
    stripe_product_id = Column(String(255), nullable=True)
    stripe_price_id_monthly = Column(String(255), nullable=True)
    stripe_price_id_yearly = Column(String(255), nullable=True)
    
    # Relationships
    # subscriptions = relationship("Subscription", back_populates="plan")
    # tenants = relationship("Tenant", back_populates="plan")
    
    __table_args__ = (
        Index("idx_billing_plans_active", "is_active"),
        Index("idx_billing_plans_public", "is_public"),
    )
    
    def __repr__(self) -> str:
        return f"<BillingPlan(id={self.id}, name={self.name}, price=${self.price_monthly})>"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enum."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"


class Subscription(BaseModel):
    """Subscription model for tenant billing."""
    
    __tablename__ = "subscriptions"
    
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan_id = Column(GUID, ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Status
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False, index=True)
    
    # Billing period
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    
    # Cancellation
    cancel_at = Column(DateTime, nullable=True)  # Scheduled cancellation
    cancelled_at = Column(DateTime, nullable=True)  # Actual cancellation
    cancellation_reason = Column(Text, nullable=True)
    
    # Usage tracking
    tokens_used_this_period = Column(Integer, default=0, nullable=False)
    api_calls_today = Column(Integer, default=0, nullable=False)
    last_usage_reset = Column(DateTime, nullable=True)
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Trial
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Additional info
    subscription_metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    # tenant = relationship("Tenant", back_populates="subscription")
    # plan = relationship("BillingPlan", back_populates="subscriptions")
    
    __table_args__ = (
        Index("idx_subscriptions_tenant", "tenant_id"),
        Index("idx_subscriptions_plan", "plan_id"),
        Index("idx_subscriptions_status", "status"),
        Index("idx_subscriptions_stripe", "stripe_subscription_id"),
        Index("idx_subscriptions_period", "current_period_end"),
    )
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, tenant_id={self.tenant_id}, status={self.status})>"
