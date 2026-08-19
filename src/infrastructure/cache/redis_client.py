"""
Redis client wrapper for caching.
"""
import logging
import json
from typing import Optional, Any, Dict, List
import asyncio

from src.shared.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection management.
    """
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or settings.redis_connection_url
        self._client = None
        self._enabled = settings.REDIS_ENABLED
    
    async def _get_client(self):
        """Get or create Redis client."""
        if not self._enabled:
            return None
        
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(self.url, decode_responses=True)
                await self._client.ping()
                logger.info(f"Redis connected: {self.url}")
            except ImportError:
                logger.warning("Redis not installed, falling back to memory cache")
                self._enabled = False
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._enabled = False
        
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._enabled:
            return None
        
        try:
            client = await self._get_client()
            if client:
                value = await client.get(key)
                if value:
                    return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self._enabled:
            return False
        
        try:
            client = await self._get_client()
            if client:
                serialized = json.dumps(value, default=str)
                if ttl:
                    await client.setex(key, ttl, serialized)
                else:
                    await client.set(key, serialized)
                return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
        
        return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._enabled:
            return False
        
        try:
            client = await self._get_client()
            if client:
                await client.delete(key)
                return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
        
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._enabled:
            return False
        
        try:
            client = await self._get_client()
            if client:
                return await client.exists(key) > 0
        except Exception:
            pass
        
        return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        if not self._enabled:
            return False
        
        try:
            client = await self._get_client()
            if client:
                return await client.expire(key, ttl)
        except Exception:
            pass
        
        return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if not self._enabled:
            return []
        
        try:
            client = await self._get_client()
            if client:
                return await client.keys(pattern)
        except Exception:
            pass
        
        return []
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern."""
        keys = await self.keys(pattern)
        if keys:
            client = await self._get_client()
            if client:
                return await client.delete(*keys)
        return 0
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
    
    @property
    def enabled(self) -> bool:
        """Check if Redis is enabled."""
        return self._enabled