"""
Rate limiting implementation using token bucket algorithm.
"""
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Any  # ADD Any HERE
from uuid import UUID
import asyncio
import threading

from src.shared.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""
    
    max_requests: int
    window_seconds: int
    block_duration_seconds: int = 300  # 5 minutes block
    
    def get_refill_rate(self) -> float:
        """Get tokens refilled per second."""
        return self.max_requests / self.window_seconds


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    
    config: RateLimitConfig
    tokens: float = field(default_factory=lambda: 0.0)
    last_refill: float = field(default_factory=time.time)
    blocked_until: float = 0.0
    
    def __post_init__(self):
        self.tokens = float(self.config.max_requests)
    
    def refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            refill_amount = elapsed * self.config.get_refill_rate()
            self.tokens = min(self.config.max_requests, self.tokens + refill_amount)
            self.last_refill = now
    
    def consume(self, tokens: float = 1.0) -> bool:
        """
        Try to consume tokens.
        Returns True if successful, False if rate limited.
        """
        now = time.time()
        
        # Check if blocked
        if now < self.blocked_until:
            return False
        
        self.refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        # Set block time
        self.blocked_until = now + self.config.block_duration_seconds
        return False
    
    def get_remaining_tokens(self) -> float:
        """Get remaining tokens."""
        self.refill()
        return max(0, self.tokens)
    
    def get_reset_time(self) -> float:
        """Get time until bucket is fully refilled."""
        self.refill()
        missing = self.config.max_requests - self.tokens
        if missing <= 0:
            return 0
        return missing / self.config.get_refill_rate()


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.
    Supports in-memory storage (use Redis for distributed).
    """
    
    def __init__(self, use_redis: bool = False, redis_client=None):
        self.use_redis = use_redis
        self.redis_client = redis_client
        
        # In-memory storage
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.RLock()
        
        # Default configurations for different endpoint types
        self.configs = {
            "default": RateLimitConfig(
                max_requests=settings.RATE_LIMIT_REQUESTS,
                window_seconds=settings.RATE_LIMIT_PERIOD_SECONDS,
            ),
            "auth": RateLimitConfig(
                max_requests=10,
                window_seconds=60,
                block_duration_seconds=900,  # 15 minutes
            ),
            "api": RateLimitConfig(
                max_requests=1000,
                window_seconds=3600,  # 1 hour
            ),
            "chat": RateLimitConfig(
                max_requests=60,
                window_seconds=60,
            ),
            "image_generation": RateLimitConfig(
                max_requests=10,
                window_seconds=3600,
            ),
            "admin": RateLimitConfig(
                max_requests=10000,
                window_seconds=3600,
            ),
        }
    
    def _get_key(self, identifier: str, endpoint_type: str) -> str:
        """Generate storage key."""
        return f"rate_limit:{endpoint_type}:{identifier}"
    
    def _get_or_create_bucket(self, key: str, endpoint_type: str) -> TokenBucket:
        """Get or create a token bucket."""
        with self._lock:
            if key not in self._buckets:
                config = self.configs.get(endpoint_type, self.configs["default"])
                self._buckets[key] = TokenBucket(config=config)
            
            return self._buckets[key]
    
    async def check(
        self,
        identifier: str,
        endpoint_type: str = "default",
        cost: float = 1.0,
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        Returns (allowed, wait_seconds).
        """
        if self.use_redis and self.redis_client:
            return await self._check_redis(identifier, endpoint_type, cost)
        
        return self._check_memory(identifier, endpoint_type, cost)
    
    def check_sync(
        self,
        identifier: str,
        endpoint_type: str = "default",
        cost: float = 1.0,
    ) -> Tuple[bool, int]:
        """
        Synchronous version of check.
        """
        return self._check_memory(identifier, endpoint_type, cost)
    
    def _check_memory(
        self,
        identifier: str,
        endpoint_type: str,
        cost: float,
    ) -> Tuple[bool, int]:
        """Check using in-memory storage."""
        key = self._get_key(identifier, endpoint_type)
        bucket = self._get_or_create_bucket(key, endpoint_type)
        
        allowed = bucket.consume(cost)
        
        if not allowed:
            wait_time = int(bucket.blocked_until - time.time())
            return False, max(0, wait_time)
        
        return True, 0
    
    async def _check_redis(
        self,
        identifier: str,
        endpoint_type: str,
        cost: float,
    ) -> Tuple[bool, int]:
        """
        Check using Redis (distributed rate limiting).
        """
        # Simplified - return allowed for now
        return True, 0
    
    def get_remaining(
        self,
        identifier: str,
        endpoint_type: str = "default",
    ) -> Optional[float]:
        """
        Get remaining tokens for an identifier.
        """
        key = self._get_key(identifier, endpoint_type)
        
        with self._lock:
            if key in self._buckets:
                return self._buckets[key].get_remaining_tokens()
        
        return None
    
    def get_reset_time(
        self,
        identifier: str,
        endpoint_type: str = "default",
    ) -> Optional[float]:
        """
        Get time until rate limit resets.
        """
        key = self._get_key(identifier, endpoint_type)
        
        with self._lock:
            if key in self._buckets:
                return self._buckets[key].get_reset_time()
        
        return None
    
    def reset(self, identifier: str, endpoint_type: str = "default") -> None:
        """
        Reset rate limit for an identifier.
        """
        key = self._get_key(identifier, endpoint_type)
        
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.
        """
        with self._lock:
            stats = {
                "total_buckets": len(self._buckets),
                "blocked_buckets": 0,
                "by_endpoint": {},
            }
            
            for key, bucket in self._buckets.items():
                # Extract endpoint type from key
                parts = key.split(':')
                if len(parts) >= 2:
                    endpoint_type = parts[1]
                    if endpoint_type not in stats["by_endpoint"]:
                        stats["by_endpoint"][endpoint_type] = 0
                    stats["by_endpoint"][endpoint_type] += 1
                
                if bucket.blocked_until > time.time():
                    stats["blocked_buckets"] += 1
            
            return stats
    
    def cleanup_expired(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up expired buckets.
        """
        now = time.time()
        to_delete = []
        
        with self._lock:
            for key, bucket in self._buckets.items():
                if bucket.last_refill < now - max_age_seconds:
                    to_delete.append(key)
            
            for key in to_delete:
                del self._buckets[key]
        
        return len(to_delete)


class TieredRateLimiter(RateLimiter):
    """
    Rate limiter with different limits based on user tier/role.
    """
    
    def __init__(self, use_redis: bool = False, redis_client=None):
        super().__init__(use_redis, redis_client)
        
        # Tier-based configurations
        self.tier_configs = {
            "viewer": {
                "default": RateLimitConfig(max_requests=30, window_seconds=60),
                "chat": RateLimitConfig(max_requests=10, window_seconds=60),
                "image_generation": RateLimitConfig(max_requests=5, window_seconds=86400),
            },
            "user": {
                "default": RateLimitConfig(max_requests=100, window_seconds=60),
                "chat": RateLimitConfig(max_requests=30, window_seconds=60),
                "image_generation": RateLimitConfig(max_requests=20, window_seconds=86400),
            },
            "power_user": {
                "default": RateLimitConfig(max_requests=300, window_seconds=60),
                "chat": RateLimitConfig(max_requests=100, window_seconds=60),
                "image_generation": RateLimitConfig(max_requests=50, window_seconds=86400),
            },
            "admin": {
                "default": RateLimitConfig(max_requests=1000, window_seconds=60),
                "chat": RateLimitConfig(max_requests=500, window_seconds=60),
                "image_generation": RateLimitConfig(max_requests=200, window_seconds=86400),
            },
        }
    
    async def check_with_tier(
        self,
        identifier: str,
        tier: str,
        endpoint_type: str = "default",
        cost: float = 1.0,
    ) -> Tuple[bool, int]:
        """
        Check rate limit with tier-based configuration.
        """
        # Override config with tier-specific
        original_configs = self.configs.copy()
        
        if tier in self.tier_configs:
            tier_config = self.tier_configs[tier]
            for endpoint, config in tier_config.items():
                self.configs[endpoint] = config
        
        try:
            result = await self.check(identifier, endpoint_type, cost)
            return result
        finally:
            # Restore original configs
            self.configs = original_configs