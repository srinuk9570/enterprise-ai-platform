"""
Logging decorators for function entry/exit logging.
"""
import logging
from functools import wraps
from typing import Callable, Optional, Any

logger = logging.getLogger(__name__)


def log_execution(
    level: int = logging.DEBUG,
    log_args: bool = True,
    log_result: bool = False,
    max_arg_length: int = 100,
):
    """
    Decorator to log function execution.
    
    Args:
        level: Logging level
        log_args: Whether to log arguments
        log_result: Whether to log return value
        max_arg_length: Maximum length for argument strings
    
    Usage:
        @log_execution(level=logging.INFO)
        def process_data(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            func_name = func.__name__
            
            # Log entry
            if log_args:
                args_str = _format_args(args, kwargs, max_arg_length)
                logger.log(level, f"→ {func_name}({args_str})")
            else:
                logger.log(level, f"→ {func_name}()")
            
            try:
                result = func(*args, **kwargs)
                
                # Log exit
                if log_result:
                    result_str = _truncate(str(result), max_arg_length)
                    logger.log(level, f"← {func_name}() -> {result_str}")
                else:
                    logger.log(level, f"← {func_name}()")
                
                return result
                
            except Exception as e:
                logger.error(f"✗ {func_name}() failed: {e}")
                raise
        
        return wrapper
    return decorator


def log_async_execution(
    level: int = logging.DEBUG,
    log_args: bool = True,
    log_result: bool = False,
    max_arg_length: int = 100,
):
    """
    Decorator to log async function execution.
    
    Args:
        level: Logging level
        log_args: Whether to log arguments
        log_result: Whether to log return value
        max_arg_length: Maximum length for argument strings
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            func_name = func.__name__
            
            if log_args:
                args_str = _format_args(args, kwargs, max_arg_length)
                logger.log(level, f"→ {func_name}({args_str}) [async]")
            else:
                logger.log(level, f"→ {func_name}() [async]")
            
            try:
                result = await func(*args, **kwargs)
                
                if log_result:
                    result_str = _truncate(str(result), max_arg_length)
                    logger.log(level, f"← {func_name}() -> {result_str} [async]")
                else:
                    logger.log(level, f"← {func_name}() [async]")
                
                return result
                
            except Exception as e:
                logger.error(f"✗ {func_name}() failed: {e} [async]")
                raise
        
        return wrapper
    return decorator


def _format_args(args: tuple, kwargs: dict, max_length: int) -> str:
    """Format function arguments for logging."""
    parts = []
    
    # Positional args
    for arg in args:
        if arg is not None and not isinstance(arg, (str, int, float, bool)):
            parts.append(type(arg).__name__)
        else:
            parts.append(_truncate(str(arg), max_length))
    
    # Keyword args
    for key, value in kwargs.items():
        if value is not None and not isinstance(value, (str, int, float, bool)):
            parts.append(f"{key}={type(value).__name__}")
        else:
            parts.append(f"{key}={_truncate(str(value), max_length)}")
    
    return ", ".join(parts)


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."