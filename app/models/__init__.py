"""Database models package.

This package contains all SQLAlchemy ORM models for the Task Assistant SaaS platform.
All models inherit from base classes that provide:
- UUID primary keys
- Automatic timestamps (created_at, updated_at)
- Tenant isolation (for multi-tenancy)
- Soft delete functionality
"""

# Base classes
from app.models.base import Base, BaseModel, TenantModel, GUID

# Core models
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.api_key import APIKey

# Provider models
from app.models.provider import Provider, Model, ProviderType

# Agent models
from app.models.agent import Agent, AgentTool, AgentRun, MemoryStrategy, AgentRunStatus

# Conversation models
from app.models.message import Conversation, Message, ConversationStatus, MessageRole

# Task models
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project

# Billing models
from app.models.billing import BillingPlan, Subscription, SubscriptionStatus

# Usage and audit models
from app.models.usage_log import UsageLog
from app.models.audit import AuditLog

# Legacy models (for backward compatibility - will be removed)
from app.models.conversation import ConversationHistory, MessageRole as LegacyMessageRole
from app.models.audit_log import TaskAuditLog, AuditAction
from app.models.session import UserSession

__all__ = [
    # Base
    "Base",
    "BaseModel",
    "TenantModel",
    "GUID",
    # Core
    "Tenant",
    "TenantStatus",
    "User",
    "Role",
    "UserRole",
    "APIKey",
    # Providers
    "Provider",
    "Model",
    "ProviderType",
    # Agents
    "Agent",
    "AgentTool",
    "AgentRun",
    "MemoryStrategy",
    "AgentRunStatus",
    # Conversations
    "Conversation",
    "Message",
    "ConversationStatus",
    "MessageRole",
    # Tasks
    "Task",
    "TaskStatus",
    "TaskPriority",
    "Project",
    # Billing
    "BillingPlan",
    "Subscription",
    "SubscriptionStatus",
    # Usage & Audit
    "UsageLog",
    "AuditLog",
    # Legacy (for backward compatibility)
    "ConversationHistory",
    "TaskAuditLog",
    "AuditAction",
    "UserSession",
]
