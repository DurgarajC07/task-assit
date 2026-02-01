"""Tenant service for managing tenant operations.

Handles tenant CRUD, settings, quotas, and subscription management.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
from datetime import datetime

from app.models.tenant import Tenant, TenantStatus
from app.models.billing import BillingPlan, Subscription, SubscriptionStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenants."""
    
    def __init__(self, db: AsyncSession):
        """Initialize tenant service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_tenant(
        self,
        name: str,
        slug: str,
        owner_email: str,
        owner_username: str,
        owner_password: str,
        plan_id: Optional[UUID] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> tuple[Tenant, User]:
        """Create a new tenant with owner user.
        
        Args:
            name: Tenant name
            slug: URL-friendly identifier
            owner_email: Owner email
            owner_username: Owner username
            owner_password: Owner password (hashed)
            plan_id: Optional billing plan
            settings: Optional tenant settings
            
        Returns:
            Tuple of (Tenant, Owner User)
            
        Raises:
            ValueError: If slug already exists
        """
        # Check if slug exists
        existing = await self.get_tenant_by_slug(slug)
        if existing:
            raise ValueError(f"Tenant with slug '{slug}' already exists")
        
        # Create tenant
        tenant = Tenant(
            name=name,
            slug=slug,
            plan_id=plan_id,
            status=TenantStatus.ACTIVE,
            settings=settings or {},
        )
        
        self.db.add(tenant)
        await self.db.flush()  # Get tenant ID
        
        # Create owner user
        from app.core.security import get_password_hash
        owner = User(
            tenant_id=tenant.id,
            username=owner_username,
            email=owner_email,
            hashed_password=get_password_hash(owner_password),
            status="active",
            email_verified=True,
        )
        
        self.db.add(owner)
        await self.db.commit()
        await self.db.refresh(tenant)
        await self.db.refresh(owner)
        
        logger.info(f"Created tenant '{name}' with slug '{slug}'")
        return tenant, owner
    
    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Tenant or None
        """
        result = await self.db.execute(
            select(Tenant).where(
                and_(
                    Tenant.id == tenant_id,
                    Tenant.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug.
        
        Args:
            slug: Tenant slug
            
        Returns:
            Tenant or None
        """
        result = await self.db.execute(
            select(Tenant).where(
                and_(
                    Tenant.slug == slug,
                    Tenant.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List all tenants with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List of tenants
        """
        conditions = [Tenant.deleted_at.is_(None)]
        
        if status:
            conditions.append(Tenant.status == status)
        
        result = await self.db.execute(
            select(Tenant)
            .where(and_(*conditions))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def update_tenant(
        self,
        tenant_id: UUID,
        name: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        settings: Optional[Dict[str, Any]] = None,
        max_users: Optional[int] = None,
        max_agents: Optional[int] = None,
        monthly_token_quota: Optional[int] = None,
    ) -> Optional[Tenant]:
        """Update tenant.
        
        Args:
            tenant_id: Tenant UUID
            name: New name
            status: New status
            settings: New settings (merged with existing)
            max_users: User quota
            max_agents: Agent quota
            monthly_token_quota: Token quota
            
        Returns:
            Updated tenant or None
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        if name is not None:
            tenant.name = name
        if status is not None:
            tenant.status = status
        if settings is not None:
            # Merge with existing settings
            tenant.settings = {**tenant.settings, **settings}
        if max_users is not None:
            tenant.max_users = max_users
        if max_agents is not None:
            tenant.max_agents = max_agents
        if monthly_token_quota is not None:
            tenant.monthly_token_quota = monthly_token_quota
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        logger.info(f"Updated tenant {tenant_id}")
        return tenant
    
    async def delete_tenant(self, tenant_id: UUID) -> bool:
        """Soft delete tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if deleted, False if not found
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        tenant.soft_delete()
        tenant.status = TenantStatus.SUSPENDED
        await self.db.commit()
        
        logger.info(f"Deleted tenant {tenant_id}")
        return True
    
    async def suspend_tenant(self, tenant_id: UUID, reason: str) -> Optional[Tenant]:
        """Suspend tenant.
        
        Args:
            tenant_id: Tenant UUID
            reason: Suspension reason
            
        Returns:
            Updated tenant or None
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        tenant.status = TenantStatus.SUSPENDED
        tenant.settings["suspension_reason"] = reason
        tenant.settings["suspended_at"] = datetime.utcnow().isoformat()
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        logger.warning(f"Suspended tenant {tenant_id}: {reason}")
        return tenant
    
    async def activate_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Activate suspended tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Updated tenant or None
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        tenant.status = TenantStatus.ACTIVE
        
        # Clear suspension info
        if "suspension_reason" in tenant.settings:
            del tenant.settings["suspension_reason"]
        if "suspended_at" in tenant.settings:
            del tenant.settings["suspended_at"]
        
        await self.db.commit()
        await self.db.refresh(tenant)
        
        logger.info(f"Activated tenant {tenant_id}")
        return tenant
    
    async def check_quota(
        self,
        tenant_id: UUID,
        quota_type: str,
        amount: int = 1
    ) -> bool:
        """Check if tenant has available quota.
        
        Args:
            tenant_id: Tenant UUID
            quota_type: Type of quota (users, agents, tokens)
            amount: Amount to check
            
        Returns:
            True if quota available, False otherwise
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        if quota_type == "users":
            # Count current users
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.tenant_id == tenant_id,
                        User.deleted_at.is_(None)
                    )
                )
            )
            current = len(list(result.scalars().all()))
            return (current + amount) <= tenant.max_users
        
        elif quota_type == "agents":
            # Check agent quota
            from app.models.agent import Agent
            result = await self.db.execute(
                select(Agent).where(
                    and_(
                        Agent.tenant_id == tenant_id,
                        Agent.deleted_at.is_(None)
                    )
                )
            )
            current = len(list(result.scalars().all()))
            return (current + amount) <= tenant.max_agents
        
        elif quota_type == "tokens":
            # Check token usage this month
            # This would integrate with usage tracking
            return True  # Placeholder
        
        return False
    
    async def get_subscription(self, tenant_id: UUID) -> Optional[Subscription]:
        """Get active subscription for tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Active subscription or None
        """
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()
