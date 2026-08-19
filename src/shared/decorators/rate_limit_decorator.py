"""
Rate limiting decorators.
"""
import time
import logging
from functools import wraps
from typing import Callable, Optional, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter
_rate_limit_store: Dict[str, list] = defaultdict(list)


def rate_limit(
    max_calls: int,
    period_seconds: int,
    key_func: Optional[Callable[..., str]] = None,
):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_calls: Maximum number of calls allowed in the period
        period_seconds: Time period in seconds
        key_func: Function to generate rate limit key from arguments
    
    Usage:
        @rate_limit(max_calls=10, period_seconds=60)
        def api_call(user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate key
            if key_func:
                key = f"{func.__name__}:{key_func(*args, **kwargs)}"
            else:
                key = func.__name__
            
            now = time.time()
            window_start = now - period_seconds
            
            # Clean old calls
            calls = _rate_limit_store[key]
            calls[:] = [t for t in calls if t > window_start]
            
            # Check limit
            if len(calls) >= max_calls:
                oldest = min(calls) if calls else now
                retry_after = int(oldest + period_seconds - now) + 1
                
                from src.shared.exceptions import RateLimitError
                raise RateLimitError(
                    f"Rate limit exceeded for {func.__name__}",
                    retry_after=retry_after,
                )
            
            # Record call
            calls.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def async_rate_limit(
    max_calls: int,
    period_seconds: int,
    key_func: Optional[Callable[..., str]] = None,
):
    """
    Decorator to rate limit async function calls.
    
    Args:
        max_calls: Maximum number of calls allowed in the period
        period_seconds: Time period in seconds
        key_func: Function to generate rate limit key from arguments
    """
    import asyncio
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if key_func:
                key = f"{func.__name__}:{key_func(*args, **kwargs)}"
            else:
                key = func.__name__
            
            now = time.time()
            window_start = now - period_seconds
            
            calls = _rate_limit_store[key]
            calls[:] = [t for t in calls if t > window_start]
            
            if len(calls) >= max_calls:
                oldest = min(calls) if calls else now
                retry_after = int(oldest + period_seconds - now) + 1
                
                from src.shared.exceptions import RateLimitError
                raise RateLimitError(
                    f"Rate limit exceeded for {func.__name__}",
                    retry_after=retry_after,
                )
            
            calls.append(now)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def clear_rate_limits(key: Optional[str] = None) -> None:
    """
    Clear rate limit data.
    
    Args:
        key: Specific key to clear, or None to clear all
    """
    if key is None:
        _rate_limit_store.clear()
    elif key in _rate_limit_store:
        del _rate_limit_store[key]