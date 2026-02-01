"""Caching utilities using Redis for response and data caching.

Provides decorators and utilities for caching expensive operations,
API responses, and database queries.
"""
from typing import Optional, Any, Callable
from functools import wraps
import json
import hashlib
from datetime import timedelta
import redis.asyncio as redis
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize cache manager.
        
        Args:
            redis_client: Redis client
        """
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or settings.redis_cache_ttl
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key
        """
        # Create unique identifier from args and kwargs
        key_data = f"{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"


def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_builder: Optional custom key builder function
        
    Example:
        @cached("user_profile", ttl=300)
        async def get_user_profile(user_id: UUID):
            # Expensive operation
            return profile
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager
            cache = await get_cache_manager()
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache.generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """Decorator to invalidate cache after function execution.
    
    Args:
        pattern: Cache key pattern to invalidate
        
    Example:
        @cache_invalidate("user:*")
        async def update_user(user_id: UUID, data: dict):
            # Update operation
            return updated_user
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            cache = await get_cache_manager()
            deleted = await cache.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted} cache keys matching {pattern}")
            
            return result
        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get cache manager instance.
    
    Returns:
        Cache manager
    """
    global _cache_manager
    if _cache_manager is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        _cache_manager = CacheManager(redis_client)
    return _cache_manager


async def cache_conversation_response(
    conversation_id: str,
    message_hash: str,
    response: dict,
    ttl: int = 3600
) -> None:
    """Cache conversation response for potential reuse.
    
    Args:
        conversation_id: Conversation UUID
        message_hash: Hash of the message
        response: Response to cache
        ttl: Time to live in seconds
    """
    cache = await get_cache_manager()
    key = f"conversation:{conversation_id}:response:{message_hash}"
    await cache.set(key, response, ttl)


async def get_cached_conversation_response(
    conversation_id: str,
    message_hash: str
) -> Optional[dict]:
    """Get cached conversation response.
    
    Args:
        conversation_id: Conversation UUID
        message_hash: Hash of the message
        
    Returns:
        Cached response or None
    """
    cache = await get_cache_manager()
    key = f"conversation:{conversation_id}:response:{message_hash}"
    return await cache.get(key)


async def invalidate_tenant_cache(tenant_id: str) -> int:
    """Invalidate all cache for a tenant.
    
    Args:
        tenant_id: Tenant UUID
        
    Returns:
        Number of keys deleted
    """
    cache = await get_cache_manager()
    return await cache.delete_pattern(f"*:tenant:{tenant_id}:*")


async def invalidate_user_cache(user_id: str, tenant_id: str) -> int:
    """Invalidate all cache for a user.
    
    Args:
        user_id: User UUID
        tenant_id: Tenant UUID
        
    Returns:
        Number of keys deleted
    """
    cache = await get_cache_manager()
    return await cache.delete_pattern(f"*:tenant:{tenant_id}:user:{user_id}:*")
