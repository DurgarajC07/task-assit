"""Rate limiting middleware and utilities using Redis.

Implements token bucket rate limiting per tenant, user, and API key
to prevent abuse and ensure fair resource distribution.
"""
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
import redis.asyncio as redis
import logging
from uuid import UUID

from app.config import settings
from app.core.tenant_context import get_tenant_context, get_user_context

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter using token bucket algorithm."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize rate limiter.
        
        Args:
            redis_client: Redis client
        """
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key (e.g., "tenant:123:rate_limit")
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed, remaining, reset_seconds)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Use sorted set to track requests with timestamps
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        
        # Count requests in current window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
        
        # Set expiry on the key
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[1]
        
        # Check if limit exceeded
        allowed = current_count < limit
        remaining = max(0, limit - current_count - 1)
        
        # Calculate reset time
        if current_count >= limit:
            # Get oldest request in window
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]
                reset_seconds = int(window_seconds - (now.timestamp() - oldest_timestamp))
            else:
                reset_seconds = window_seconds
        else:
            reset_seconds = window_seconds
        
        return allowed, remaining, reset_seconds
    
    async def check_tenant_rate_limit(
        self,
        tenant_id: UUID,
        limit_per_minute: Optional[int] = None,
        limit_per_hour: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Check tenant rate limits.
        
        Args:
            tenant_id: Tenant UUID
            limit_per_minute: Requests per minute (default from settings)
            limit_per_hour: Requests per hour (default from settings)
            
        Returns:
            Tuple of (allowed, error_message)
        """
        limit_per_minute = limit_per_minute or settings.rate_limit_per_minute
        limit_per_hour = limit_per_hour or settings.rate_limit_per_hour
        
        # Check per-minute limit
        minute_key = f"rate_limit:tenant:{tenant_id}:minute"
        minute_allowed, minute_remaining, minute_reset = await self.check_rate_limit(
            minute_key, limit_per_minute, 60
        )
        
        if not minute_allowed:
            return False, f"Rate limit exceeded. Try again in {minute_reset} seconds."
        
        # Check per-hour limit
        hour_key = f"rate_limit:tenant:{tenant_id}:hour"
        hour_allowed, hour_remaining, hour_reset = await self.check_rate_limit(
            hour_key, limit_per_hour, 3600
        )
        
        if not hour_allowed:
            return False, f"Hourly rate limit exceeded. Try again in {hour_reset // 60} minutes."
        
        return True, ""
    
    async def check_user_rate_limit(
        self,
        user_id: UUID,
        tenant_id: UUID,
        limit_per_minute: int = 50
    ) -> Tuple[bool, str]:
        """Check user rate limits.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            limit_per_minute: Requests per minute
            
        Returns:
            Tuple of (allowed, error_message)
        """
        key = f"rate_limit:user:{tenant_id}:{user_id}:minute"
        allowed, remaining, reset = await self.check_rate_limit(
            key, limit_per_minute, 60
        )
        
        if not allowed:
            return False, f"User rate limit exceeded. Try again in {reset} seconds."
        
        return True, ""
    
    async def check_endpoint_rate_limit(
        self,
        endpoint: str,
        identifier: str,
        limit: int = 10,
        window_seconds: int = 60
    ) -> Tuple[bool, str]:
        """Check endpoint-specific rate limits.
        
        Args:
            endpoint: Endpoint path
            identifier: User/tenant/IP identifier
            limit: Request limit
            window_seconds: Time window
            
        Returns:
            Tuple of (allowed, error_message)
        """
        key = f"rate_limit:endpoint:{endpoint}:{identifier}"
        allowed, remaining, reset = await self.check_rate_limit(
            key, limit, window_seconds
        )
        
        if not allowed:
            return False, f"Endpoint rate limit exceeded. Try again in {reset} seconds."
        
        return True, ""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic rate limiting."""
    
    def __init__(self, app, redis_client: redis.Redis):
        """Initialize middleware.
        
        Args:
            app: FastAPI app
            redis_client: Redis client
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_client)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware
            
        Returns:
            Response
        """
        # Skip rate limiting for health check and metrics
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get context
        tenant_id = get_tenant_context()
        user_id = get_user_context()
        
        # Check tenant rate limit
        if tenant_id:
            allowed, message = await self.rate_limiter.check_tenant_rate_limit(tenant_id)
            if not allowed:
                logger.warning(f"Tenant {tenant_id} rate limit exceeded")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message
                )
        
        # Check user rate limit
        if user_id and tenant_id:
            allowed, message = await self.rate_limiter.check_user_rate_limit(
                user_id, tenant_id
            )
            if not allowed:
                logger.warning(f"User {user_id} rate limit exceeded")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message
                )
        
        # Check auth endpoint rate limit (stricter)
        if request.url.path.startswith("/api/auth"):
            identifier = str(tenant_id) if tenant_id else request.client.host
            allowed, message = await self.rate_limiter.check_endpoint_rate_limit(
                "auth",
                identifier,
                limit=settings.auth_rate_limit_per_15min,
                window_seconds=900  # 15 minutes
            )
            if not allowed:
                logger.warning(f"Auth endpoint rate limit exceeded for {identifier}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message
                )
        
        # Process request
        response = await call_next(request)
        
        return response


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance.
    
    Returns:
        Rate limiter
    """
    global _rate_limiter
    if _rate_limiter is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter
