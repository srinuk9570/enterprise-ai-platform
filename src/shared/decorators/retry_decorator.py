"""
Retry decorators with exponential backoff.
"""
import time
import logging
import asyncio
from functools import wraps
from typing import Callable, Optional, Tuple, Type, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    max_delay_seconds: float = 60.0
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[Exception, int], None]] = None


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay_seconds: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator to retry a function on failure with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff_factor: Multiplier for delay after each attempt
        max_delay_seconds: Maximum delay between retries
        exceptions: Exceptions to catch and retry
        on_retry: Optional callback called before each retry
    
    Usage:
        @retry(max_attempts=3, delay_seconds=0.5)
        def flaky_operation():
            ...
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        delay_seconds=delay_seconds,
        backoff_factor=backoff_factor,
        max_delay_seconds=max_delay_seconds,
        exceptions=exceptions,
        on_retry=on_retry,
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = config.delay_seconds
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts:
                        if config.on_retry:
                            config.on_retry(e, attempt)
                        
                        logger.warning(
                            f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        
                        time.sleep(current_delay)
                        current_delay = min(
                            current_delay * config.backoff_factor,
                            config.max_delay_seconds,
                        )
            
            logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay_seconds: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator to retry an async function on failure with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff_factor: Multiplier for delay after each attempt
        max_delay_seconds: Maximum delay between retries
        exceptions: Exceptions to catch and retry
        on_retry: Optional callback called before each retry
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        delay_seconds=delay_seconds,
        backoff_factor=backoff_factor,
        max_delay_seconds=max_delay_seconds,
        exceptions=exceptions,
        on_retry=on_retry,
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = config.delay_seconds
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts:
                        if config.on_retry:
                            config.on_retry(e, attempt)
                        
                        logger.warning(
                            f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        
                        await asyncio.sleep(current_delay)
                        current_delay = min(
                            current_delay * config.backoff_factor,
                            config.max_delay_seconds,
                        )
            
            logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator