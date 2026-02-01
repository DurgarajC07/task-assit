"""Webhook management for event notifications.

Allows tenants to register webhooks for various events like
agent completions, usage alerts, subscription changes, etc.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
import logging

from app.models.webhook import Webhook, WebhookDelivery, WebhookEventType, WebhookDeliveryStatus

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manager for webhooks and event delivery."""
    
    def __init__(self, db: AsyncSession):
        """Initialize webhook manager.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_webhook(
        self,
        tenant_id: UUID,
        url: str,
        event_types: List[WebhookEventType],
        description: Optional[str] = None,
        secret: Optional[str] = None,
        is_active: bool = True
    ) -> Webhook:
        """Create a webhook.
        
        Args:
            tenant_id: Tenant UUID
            url: Webhook URL
            event_types: List of event types to subscribe to
            description: Optional description
            secret: Optional secret for signature verification
            is_active: Whether webhook is active
            
        Returns:
            Created webhook
        """
        webhook = Webhook(
            tenant_id=tenant_id,
            url=url,
            event_types=event_types,
            description=description,
            secret=secret,
            is_active=is_active
        )
        
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        
        logger.info(f"Created webhook {webhook.id} for tenant {tenant_id}")
        return webhook
    
    async def get_webhooks_for_event(
        self,
        tenant_id: UUID,
        event_type: WebhookEventType
    ) -> List[Webhook]:
        """Get active webhooks subscribed to event type.
        
        Args:
            tenant_id: Tenant UUID
            event_type: Event type
            
        Returns:
            List of webhooks
        """
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.tenant_id == tenant_id,
                    Webhook.is_active == True,
                    Webhook.event_types.contains([event_type]),
                    Webhook.deleted_at.is_(None)
                )
            )
        )
        return list(result.scalars().all())
    
    async def trigger_event(
        self,
        tenant_id: UUID,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ) -> int:
        """Trigger webhooks for an event.
        
        Args:
            tenant_id: Tenant UUID
            event_type: Event type
            payload: Event payload
            
        Returns:
            Number of webhooks triggered
        """
        webhooks = await self.get_webhooks_for_event(tenant_id, event_type)
        
        if not webhooks:
            logger.debug(f"No webhooks for event {event_type} on tenant {tenant_id}")
            return 0
        
        # Queue webhook deliveries
        from app.core.celery_tasks import process_webhook
        
        for webhook in webhooks:
            # Create delivery record
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                status=WebhookDeliveryStatus.PENDING
            )
            self.db.add(delivery)
            
            # Queue async delivery
            process_webhook.apply_async(
                args=[webhook.url, event_type.value, payload],
                link_error=self._handle_webhook_error.s(delivery.id)
            )
        
        await self.db.commit()
        
        logger.info(f"Triggered {len(webhooks)} webhooks for event {event_type}")
        return len(webhooks)
    
    async def _handle_webhook_error(self, delivery_id: UUID, error: str) -> None:
        """Handle webhook delivery error.
        
        Args:
            delivery_id: Delivery UUID
            error: Error message
        """
        result = await self.db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()
        
        if delivery:
            delivery.status = WebhookDeliveryStatus.FAILED
            delivery.response_body = error
            delivery.delivered_at = datetime.utcnow()
            await self.db.commit()


# Convenience functions for triggering common events

async def trigger_agent_completed(
    db: AsyncSession,
    tenant_id: UUID,
    agent_run_id: UUID,
    output: str,
    tokens_used: int
) -> None:
    """Trigger agent.completed event.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        agent_run_id: Agent run UUID
        output: Agent output
        tokens_used: Tokens consumed
    """
    manager = WebhookManager(db)
    await manager.trigger_event(
        tenant_id=tenant_id,
        event_type=WebhookEventType.AGENT_COMPLETED,
        payload={
            "agent_run_id": str(agent_run_id),
            "output": output,
            "tokens_used": tokens_used,
            "completed_at": datetime.utcnow().isoformat()
        }
    )


async def trigger_quota_exceeded(
    db: AsyncSession,
    tenant_id: UUID,
    quota_type: str,
    current: int,
    limit: int
) -> None:
    """Trigger usage.quota_exceeded event.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        quota_type: Type of quota (tokens, users, agents)
        current: Current usage
        limit: Quota limit
    """
    manager = WebhookManager(db)
    await manager.trigger_event(
        tenant_id=tenant_id,
        event_type=WebhookEventType.QUOTA_EXCEEDED,
        payload={
            "quota_type": quota_type,
            "current": current,
            "limit": limit,
            "exceeded_at": datetime.utcnow().isoformat()
        }
    )


async def trigger_subscription_expiring(
    db: AsyncSession,
    tenant_id: UUID,
    subscription_id: UUID,
    expires_at: datetime
) -> None:
    """Trigger subscription.expiring event.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        subscription_id: Subscription UUID
        expires_at: Expiration date
    """
    manager = WebhookManager(db)
    await manager.trigger_event(
        tenant_id=tenant_id,
        event_type=WebhookEventType.SUBSCRIPTION_EXPIRING,
        payload={
            "subscription_id": str(subscription_id),
            "expires_at": expires_at.isoformat(),
            "days_remaining": (expires_at - datetime.utcnow()).days
        }
    )
