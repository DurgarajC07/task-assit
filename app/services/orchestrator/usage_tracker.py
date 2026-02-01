"""Usage tracking service for monitoring AI consumption and costs.

Tracks token usage, API calls, execution time, and calculates costs
for billing and quota management.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging

from app.models.usage_log import UsageLog, UsageType
from app.core.tenant_context import get_tenant_context, get_user_context

logger = logging.getLogger(__name__)


# Pricing per 1K tokens (as of Feb 2026)
PROVIDER_PRICING = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "text-embedding-ada-002": {"input": 0.0001, "output": 0.0},
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    },
    "gemini": {
        "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
        "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
        "text-embedding-004": {"input": 0.0001, "output": 0.0},
    },
    "groq": {
        "llama-3.1-405b-reasoning": {"input": 0.001, "output": 0.001},
        "llama-3.1-70b-versatile": {"input": 0.0005, "output": 0.0005},
        "mixtral-8x7b-32768": {"input": 0.0002, "output": 0.0002},
    },
    "ollama": {
        # Local models - no cost
        "default": {"input": 0.0, "output": 0.0},
    }
}


class UsageTracker:
    """Service for tracking AI usage and costs."""
    
    def __init__(self, db: AsyncSession):
        """Initialize usage tracker.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def track_completion(
        self,
        tenant_id: UUID,
        user_id: UUID,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        execution_time_ms: int,
        agent_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageLog:
        """Track a completion request.
        
        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            provider: Provider name
            model: Model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            total_tokens: Total tokens
            execution_time_ms: Execution time in milliseconds
            agent_id: Optional agent UUID
            conversation_id: Optional conversation UUID
            metadata: Optional metadata
            
        Returns:
            Created usage log
        """
        # Calculate cost
        cost = self._calculate_cost(
            provider=provider,
            model=model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens
        )
        
        # Create usage log
        usage_log = UsageLog(
            tenant_id=tenant_id,
            user_id=user_id,
            usage_type=UsageType.COMPLETION,
            provider=provider,
            model=model,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            execution_time_ms=execution_time_ms,
            agent_id=agent_id,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        
        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        logger.info(
            f"Tracked completion: {provider}/{model} - "
            f"{total_tokens} tokens, ${cost:.6f}, {execution_time_ms}ms"
        )
        
        return usage_log
    
    async def track_embedding(
        self,
        tenant_id: UUID,
        user_id: UUID,
        provider: str,
        model: str,
        tokens: int,
        execution_time_ms: int,
        agent_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageLog:
        """Track an embedding request.
        
        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            provider: Provider name
            model: Model name
            tokens: Number of tokens
            execution_time_ms: Execution time in milliseconds
            agent_id: Optional agent UUID
            metadata: Optional metadata
            
        Returns:
            Created usage log
        """
        # Calculate cost (embeddings only have input cost)
        cost = self._calculate_cost(
            provider=provider,
            model=model,
            input_tokens=tokens,
            output_tokens=0
        )
        
        # Create usage log
        usage_log = UsageLog(
            tenant_id=tenant_id,
            user_id=user_id,
            usage_type=UsageType.EMBEDDING,
            provider=provider,
            model=model,
            input_tokens=tokens,
            output_tokens=0,
            total_tokens=tokens,
            cost=cost,
            execution_time_ms=execution_time_ms,
            agent_id=agent_id,
            metadata=metadata or {}
        )
        
        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        logger.info(
            f"Tracked embedding: {provider}/{model} - "
            f"{tokens} tokens, ${cost:.6f}, {execution_time_ms}ms"
        )
        
        return usage_log
    
    async def get_usage_summary(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get usage summary for a period.
        
        Args:
            tenant_id: Tenant UUID
            start_date: Start date (default: beginning of current month)
            end_date: End date (default: now)
            user_id: Optional filter by user
            agent_id: Optional filter by agent
            
        Returns:
            Usage summary with totals
        """
        # Default to current month
        if not start_date:
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build query conditions
        conditions = [
            UsageLog.tenant_id == tenant_id,
            UsageLog.timestamp >= start_date,
            UsageLog.timestamp <= end_date
        ]
        
        if user_id:
            conditions.append(UsageLog.user_id == user_id)
        if agent_id:
            conditions.append(UsageLog.agent_id == agent_id)
        
        # Get totals
        result = await self.db.execute(
            select(
                func.count(UsageLog.id).label('total_requests'),
                func.sum(UsageLog.input_tokens).label('total_input_tokens'),
                func.sum(UsageLog.output_tokens).label('total_output_tokens'),
                func.sum(UsageLog.total_tokens).label('total_tokens'),
                func.sum(UsageLog.cost).label('total_cost'),
                func.avg(UsageLog.execution_time_ms).label('avg_execution_time_ms')
            ).where(and_(*conditions))
        )
        row = result.first()
        
        # Get breakdown by provider
        provider_result = await self.db.execute(
            select(
                UsageLog.provider,
                UsageLog.model,
                func.count(UsageLog.id).label('requests'),
                func.sum(UsageLog.total_tokens).label('tokens'),
                func.sum(UsageLog.cost).label('cost')
            )
            .where(and_(*conditions))
            .group_by(UsageLog.provider, UsageLog.model)
        )
        
        provider_breakdown = [
            {
                "provider": r.provider,
                "model": r.model,
                "requests": r.requests,
                "tokens": r.tokens or 0,
                "cost": float(r.cost or 0)
            }
            for r in provider_result.all()
        ]
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_requests": row.total_requests or 0,
            "total_input_tokens": row.total_input_tokens or 0,
            "total_output_tokens": row.total_output_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost": float(row.total_cost or 0),
            "avg_execution_time_ms": float(row.avg_execution_time_ms or 0),
            "provider_breakdown": provider_breakdown
        }
    
    async def check_quota(
        self,
        tenant_id: UUID,
        monthly_limit: int
    ) -> Dict[str, Any]:
        """Check if tenant has exceeded monthly token quota.
        
        Args:
            tenant_id: Tenant UUID
            monthly_limit: Monthly token limit
            
        Returns:
            Quota status with usage details
        """
        # Get current month usage
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        summary = await self.get_usage_summary(
            tenant_id=tenant_id,
            start_date=start_of_month
        )
        
        used_tokens = summary["total_tokens"]
        remaining = max(0, monthly_limit - used_tokens)
        percentage = (used_tokens / monthly_limit * 100) if monthly_limit > 0 else 0
        
        return {
            "limit": monthly_limit,
            "used": used_tokens,
            "remaining": remaining,
            "percentage": round(percentage, 2),
            "exceeded": used_tokens > monthly_limit
        }
    
    def _calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for token usage.
        
        Args:
            provider: Provider name
            model: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens
            
        Returns:
            Cost in USD
        """
        provider_lower = provider.lower()
        
        # Get pricing for provider
        if provider_lower not in PROVIDER_PRICING:
            logger.warning(f"Unknown provider for pricing: {provider}")
            return 0.0
        
        provider_prices = PROVIDER_PRICING[provider_lower]
        
        # Get pricing for model (or use default)
        if model in provider_prices:
            prices = provider_prices[model]
        elif "default" in provider_prices:
            prices = provider_prices["default"]
        else:
            # Try to find a matching model by prefix
            for model_key, model_prices in provider_prices.items():
                if model.startswith(model_key):
                    prices = model_prices
                    break
            else:
                logger.warning(f"Unknown model for pricing: {provider}/{model}")
                return 0.0
        
        # Calculate cost (prices are per 1K tokens)
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        
        return input_cost + output_cost


async def track_completion_usage(
    db: AsyncSession,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    execution_time_ms: int,
    agent_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[UsageLog]:
    """Convenience function to track completion usage with automatic context.
    
    Args:
        db: Database session
        provider: Provider name
        model: Model name
        prompt_tokens: Input tokens
        completion_tokens: Output tokens
        execution_time_ms: Execution time
        agent_id: Optional agent UUID
        conversation_id: Optional conversation UUID
        metadata: Optional metadata
        
    Returns:
        Usage log or None if context not available
    """
    tenant_id = get_tenant_context()
    user_id = get_user_context()
    
    if not tenant_id or not user_id:
        logger.warning("Cannot track usage: tenant or user context not set")
        return None
    
    tracker = UsageTracker(db)
    return await tracker.track_completion(
        tenant_id=tenant_id,
        user_id=user_id,
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        execution_time_ms=execution_time_ms,
        agent_id=agent_id,
        conversation_id=conversation_id,
        metadata=metadata
    )
