"""
Validation decorators for function arguments and return values.
"""
from functools import wraps
from typing import Callable, Optional, Any, Type, List, Union


def validate_args(**validators: Callable[[Any], bool]):
    """
    Decorator to validate function arguments.
    
    Args:
        **validators: Argument name to validator function mapping
    
    Usage:
        @validate_args(
            email=lambda x: "@" in x,
            age=lambda x: 0 <= x <= 150,
        )
        def register_user(email, age):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get argument names and values
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate each argument
            for arg_name, validator in validators.items():
                if arg_name in bound.arguments:
                    value = bound.arguments[arg_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for argument '{arg_name}': {value}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_return(validator: Callable[[Any], bool], error_message: str = "Invalid return value"):
    """
    Decorator to validate function return value.
    
    Args:
        validator: Function that validates the return value
        error_message: Error message on validation failure
    
    Usage:
        @validate_return(lambda x: x > 0, "Result must be positive")
        def calculate_positive_number():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            if not validator(result):
                raise ValueError(f"{error_message}: {result}")
            
            return result
        
        return wrapper
    return decorator


def require_fields(*field_names: str):
    """
    Decorator to require specific fields in a dictionary argument.
    
    Args:
        *field_names: Required field names
    
    Usage:
        @require_fields("name", "email")
        def create_user(data: dict):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Find dictionary argument
            for arg in args:
                if isinstance(arg, dict):
                    missing = [f for f in field_names if f not in arg]
                    if missing:
                        raise ValueError(f"Missing required fields: {missing}")
            
            for value in kwargs.values():
                if isinstance(value, dict):
                    missing = [f for f in field_names if f not in value]
                    if missing:
                        raise ValueError(f"Missing required fields: {missing}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator