"""
Caching decorators with TTL support.
"""
import time
import logging
import hashlib
import json
from functools import wraps
from typing import Callable, Optional, Any, Dict, Tuple

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache: Dict[str, Tuple[Any, float]] = {}


def _generate_cache_key(func: Callable, args: Tuple, kwargs: Dict) -> str:
    """Generate a cache key from function and arguments."""
    key_data = {
        "func": func.__module__ + "." + func.__name__,
        "args": args,
        "kwargs": kwargs,
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache(ttl_seconds: Optional[int] = None):
    """
    Decorator to cache function results in memory.
    
    Args:
        ttl_seconds: Time-to-live in seconds (None = no expiry)
    
    Usage:
        @cache(ttl_seconds=300)
        def expensive_operation(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = _generate_cache_key(func, args, kwargs)
            
            # Check cache
            if cache_key in _cache:
                result, expiry = _cache[cache_key]
                if expiry is None or time.time() < expiry:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    del _cache[cache_key]
            
            # Compute and cache
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            
            expiry = None if ttl_seconds is None else time.time() + ttl_seconds
            _cache[cache_key] = (result, expiry)
            
            return result
        
        return wrapper
    return decorator


def async_cache(ttl_seconds: Optional[int] = None):
    """
    Decorator to cache async function results in memory.
    
    Args:
        ttl_seconds: Time-to-live in seconds (None = no expiry)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache_key = _generate_cache_key(func, args, kwargs)
            
            # Check cache
            if cache_key in _cache:
                result, expiry = _cache[cache_key]
                if expiry is None or time.time() < expiry:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    del _cache[cache_key]
            
            # Compute and cache
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            
            expiry = None if ttl_seconds is None else time.time() + ttl_seconds
            _cache[cache_key] = (result, expiry)
            
            return result
        
        return wrapper
    return decorator


def cache_with_ttl(ttl_seconds: int):
    """Alias for cache with required TTL."""
    return cache(ttl_seconds=ttl_seconds)


def clear_cache(func: Optional[Callable] = None) -> None:
    """
    Clear cache for a specific function or all cache.
    
    Args:
        func: Function to clear cache for, or None to clear all
    """
    global _cache
    
    if func is None:
        _cache.clear()
        logger.debug("Cleared all cache")
    else:
        prefix = func.__module__ + "." + func.__name__
        keys_to_remove = [k for k in _cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del _cache[key]
        logger.debug(f"Cleared cache for {prefix}")


def get_cache_size() -> int:
    """Get current cache size."""
    return len(_cache)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    valid_entries = 0
    expired_entries = 0
    
    now = time.time()
    for _, (_, expiry) in _cache.items():
        if expiry is None or now < expiry:
            valid_entries += 1
        else:
            expired_entries += 1
    
    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
    }