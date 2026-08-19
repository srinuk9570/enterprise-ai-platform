"""
Timing decorators for measuring execution time.
"""
import time
import logging
from functools import wraps
from typing import Callable, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_ms: Optional[float] = None
    
    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args) -> None:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
        logger.debug(f"{self.name} completed in {self.elapsed_ms:.2f}ms")


def timing_decorator(name: Optional[str] = None, log_level: int = logging.DEBUG):
    """
    Decorator to measure and log function execution time.
    
    Args:
        name: Custom name for the operation
        log_level: Logging level
    
    Usage:
        @timing_decorator("database_query")
        def query_database():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation_name = name or func.__name__
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.log(
                    log_level,
                    f"{operation_name} completed in {elapsed_ms:.2f}ms"
                )
        
        return wrapper
    return decorator


def async_timing_decorator(name: Optional[str] = None, log_level: int = logging.DEBUG):
    """
    Decorator to measure and log async function execution time.
    
    Args:
        name: Custom name for the operation
        log_level: Logging level
    """
    import asyncio
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            operation_name = name or func.__name__
            
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.log(
                    log_level,
                    f"{operation_name} completed in {elapsed_ms:.2f}ms"
                )
        
        return wrapper
    return decorator