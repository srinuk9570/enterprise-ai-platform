"""
Specific domain exceptions for business logic.
"""
from src.domain.exceptions import DomainError


class ConversationLimitExceededError(DomainError):
    """Raised when user exceeds conversation limit."""
    
    def __init__(self, user_id: str, limit: int, current: int):
        self.user_id = user_id
        self.limit = limit
        self.current = current
        super().__init__(
            f"User {user_id} has {current} conversations, exceeding limit of {limit}"
        )


class MessageRateLimitExceededError(DomainError):
    """Raised when user exceeds message rate limit."""
    
    def __init__(self, user_id: str, wait_seconds: int):
        self.user_id = user_id
        self.wait_seconds = wait_seconds
        super().__init__(f"Rate limit exceeded. Please wait {wait_seconds} seconds.")


class ModelNotAvailableError(DomainError):
    """Raised when requested model is not available."""
    
    def __init__(self, model_name: str, available_models: list = None):
        self.model_name = model_name
        self.available_models = available_models or []
        msg = f"Model '{model_name}' is not available"
        if available_models:
            msg += f". Available: {', '.join(available_models[:5])}"
        super().__init__(msg)


class TokenLimitExceededError(DomainError):
    """Raised when token limit is exceeded."""
    
    def __init__(self, current: int, limit: int):
        self.current = current
        self.limit = limit
        super().__init__(f"Token limit exceeded: {current}/{limit}")


class InvalidPromptError(DomainError):
    """Raised when prompt validation fails."""
    
    def __init__(self, reason: str, prompt: str = None):
        self.reason = reason
        self.prompt = prompt[:100] + "..." if prompt and len(prompt) > 100 else prompt
        super().__init__(f"Invalid prompt: {reason}")


class ImageGenerationFailedError(DomainError):
    """Raised when image generation fails."""
    
    def __init__(self, prompt: str, reason: str, model: str = None):
        self.prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
        self.reason = reason
        self.model = model
        super().__init__(f"Image generation failed: {reason}")


class ChartGenerationFailedError(DomainError):
    """Raised when chart generation fails."""
    
    def __init__(self, chart_type: str, reason: str):
        self.chart_type = chart_type
        self.reason = reason
        super().__init__(f"Chart generation failed for {chart_type}: {reason}")


class DataSourceNotFoundError(DomainError):
    """Raised when data source cannot be found or accessed."""
    
    def __init__(self, source_path: str):
        self.source_path = source_path
        super().__init__(f"Data source not found: {source_path}")


class InvalidDataFormatError(DomainError):
    """Raised when data format is invalid."""
    
    def __init__(self, expected: str, received: str):
        self.expected = expected
        self.received = received
        super().__init__(f"Invalid data format. Expected {expected}, got {received}")


class QuotaExceededError(DomainError):
    """Raised when user exceeds their quota."""
    
    def __init__(self, quota_type: str, limit: int, current: int):
        self.quota_type = quota_type
        self.limit = limit
        self.current = current
        super().__init__(f"{quota_type} quota exceeded: {current}/{limit}")