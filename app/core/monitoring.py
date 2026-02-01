"""Monitoring and observability integration with Sentry.

Provides error tracking, performance monitoring, and distributed tracing
for production environments.
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from app.config import settings
from app.core.tenant_context import get_tenant_context, get_user_context

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry SDK with integrations."""
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not configured, skipping initialization")
        return
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        # Send default PII (to capture user info in errors)
        send_default_pii=True,
        # Attach stack traces to messages
        attach_stacktrace=True,
        # Release tracking
        release=f"{settings.app_name}@{settings.app_version}",
    )
    
    logger.info(f"Sentry initialized for environment: {settings.sentry_environment}")


def set_sentry_context(
    user_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Set Sentry context for current request.
    
    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        extra: Additional context data
    """
    if not settings.sentry_dsn:
        return
    
    # Set user context
    if user_id:
        sentry_sdk.set_user({"id": str(user_id)})
    else:
        # Try to get from context
        context_user_id = get_user_context()
        if context_user_id:
            sentry_sdk.set_user({"id": str(context_user_id)})
    
    # Set tenant tag
    if tenant_id:
        sentry_sdk.set_tag("tenant_id", str(tenant_id))
    else:
        context_tenant_id = get_tenant_context()
        if context_tenant_id:
            sentry_sdk.set_tag("tenant_id", str(context_tenant_id))
    
    # Set extra context
    if extra:
        sentry_sdk.set_context("custom", extra)


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> Optional[str]:
    """Capture exception with context.
    
    Args:
        error: Exception to capture
        context: Additional context
        level: Error level (error, warning, info)
        
    Returns:
        Event ID or None
    """
    if not settings.sentry_dsn:
        return None
    
    # Set context
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            scope.level = level
            return sentry_sdk.capture_exception(error)
    
    return sentry_sdk.capture_exception(error)


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Capture message with context.
    
    Args:
        message: Message to capture
        level: Message level
        context: Additional context
        
    Returns:
        Event ID or None
    """
    if not settings.sentry_dsn:
        return None
    
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            scope.level = level
            return sentry_sdk.capture_message(message)
    
    return sentry_sdk.capture_message(message, level=level)


def start_transaction(
    name: str,
    op: str = "task"
) -> Any:
    """Start performance transaction.
    
    Args:
        name: Transaction name
        op: Operation type
        
    Returns:
        Transaction object
    """
    if not settings.sentry_dsn:
        return None
    
    return sentry_sdk.start_transaction(name=name, op=op)


# Metrics tracking utilities

class MetricsTracker:
    """Utility for tracking application metrics."""
    
    @staticmethod
    def track_api_call(
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        tenant_id: Optional[UUID] = None
    ) -> None:
        """Track API call metrics.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration_ms: Request duration
            tenant_id: Tenant UUID
        """
        if settings.sentry_dsn:
            sentry_sdk.set_measurement("request_duration", duration_ms, "millisecond")
            sentry_sdk.set_tag("endpoint", endpoint)
            sentry_sdk.set_tag("method", method)
            sentry_sdk.set_tag("status_code", status_code)
            if tenant_id:
                sentry_sdk.set_tag("tenant_id", str(tenant_id))
    
    @staticmethod
    def track_agent_execution(
        agent_id: UUID,
        execution_time_ms: int,
        tokens_used: int,
        status: str
    ) -> None:
        """Track agent execution metrics.
        
        Args:
            agent_id: Agent UUID
            execution_time_ms: Execution time
            tokens_used: Tokens consumed
            status: Execution status
        """
        if settings.sentry_dsn:
            sentry_sdk.set_measurement("agent_execution_time", execution_time_ms, "millisecond")
            sentry_sdk.set_measurement("agent_tokens_used", tokens_used, "none")
            sentry_sdk.set_tag("agent_id", str(agent_id))
            sentry_sdk.set_tag("agent_status", status)
    
    @staticmethod
    def track_provider_call(
        provider: str,
        model: str,
        tokens: int,
        latency_ms: int,
        success: bool
    ) -> None:
        """Track provider API call metrics.
        
        Args:
            provider: Provider name
            model: Model name
            tokens: Tokens used
            latency_ms: API latency
            success: Whether call succeeded
        """
        if settings.sentry_dsn:
            sentry_sdk.set_measurement("provider_latency", latency_ms, "millisecond")
            sentry_sdk.set_measurement("provider_tokens", tokens, "none")
            sentry_sdk.set_tag("provider", provider)
            sentry_sdk.set_tag("model", model)
            sentry_sdk.set_tag("provider_success", "true" if success else "false")


# Health check utilities

async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity.
    
    Returns:
        Health status
    """
    try:
        from app.database import get_db
        db = await anext(get_db())
        await db.execute("SELECT 1")
        return {"status": "healthy", "component": "database"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "component": "database", "error": str(e)}


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity.
    
    Returns:
        Health status
    """
    try:
        from app.core.caching import get_cache_manager
        cache = await get_cache_manager()
        await cache.redis.ping()
        return {"status": "healthy", "component": "redis"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "component": "redis", "error": str(e)}


async def check_celery_health() -> Dict[str, Any]:
    """Check Celery worker connectivity.
    
    Returns:
        Health status
    """
    try:
        from app.core.celery_tasks import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            return {"status": "healthy", "component": "celery", "workers": len(stats)}
        return {"status": "unhealthy", "component": "celery", "error": "No workers"}
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {"status": "unhealthy", "component": "celery", "error": str(e)}


async def get_system_health() -> Dict[str, Any]:
    """Get overall system health.
    
    Returns:
        System health status
    """
    checks = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_celery_health(),
        return_exceptions=True
    )
    
    components = []
    overall_healthy = True
    
    for check in checks:
        if isinstance(check, dict):
            components.append(check)
            if check.get("status") != "healthy":
                overall_healthy = False
        else:
            # Exception occurred
            components.append({
                "status": "unhealthy",
                "error": str(check)
            })
            overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "components": components,
        "timestamp": datetime.utcnow().isoformat()
    }


import asyncio
from datetime import datetime
