"""
Domain-specific exceptions.
"""


class DomainError(Exception):
    """Base class for all domain exceptions."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(message)


class DomainValidationError(DomainError):
    """Raised when domain validation fails."""
    pass


class EntityNotFoundError(DomainError):
    """Raised when an entity cannot be found."""
    
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class UnauthorizedOperationError(DomainError):
    """Raised when user attempts unauthorized operation."""
    pass


class InvalidStateTransitionError(DomainError):
    """Raised when invalid state transition is attempted."""
    pass


class BusinessRuleViolationError(DomainError):
    """Raised when a business rule is violated."""
    pass


class DuplicateEntityError(DomainError):
    """Raised when attempting to create duplicate entity."""
    
    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field} '{value}' already exists")


class InsufficientPermissionsError(DomainError):
    """Raised when user lacks required permissions."""
    
    def __init__(self, required_permission: str, user_permissions: list = None):
        self.required_permission = required_permission
        self.user_permissions = user_permissions or []
        super().__init__(f"Required permission '{required_permission}' not found")


class AuthenticationFailedError(DomainError):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str = "Invalid credentials"):
        self.reason = reason
        super().__init__(f"Authentication failed: {reason}")


class AccountLockedError(DomainError):
    """Raised when account is locked."""
    
    def __init__(self, user_id: str, reason: str = None, unlock_at: str = None):
        self.user_id = user_id
        self.reason = reason
        self.unlock_at = unlock_at
        msg = "Account is locked"
        if reason:
            msg += f": {reason}"
        if unlock_at:
            msg += f". Unlocks at {unlock_at}"
        super().__init__(msg)


class EmailNotVerifiedError(DomainError):
    """Raised when email is not verified."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} is not verified")


class TokenExpiredError(DomainError):
    """Raised when token has expired."""
    
    def __init__(self, token_type: str = "Token"):
        super().__init__(f"{token_type} has expired")


class TokenInvalidError(DomainError):
    """Raised when token is invalid."""
    
    def __init__(self, reason: str = None):
        msg = "Invalid token"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


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


class MessageRateLimitExceededError(DomainError):
    """Raised when user exceeds message rate limit."""
    
    def __init__(self, user_id: str, wait_seconds: int):
        self.user_id = user_id
        self.wait_seconds = wait_seconds
        super().__init__(f"Rate limit exceeded. Please wait {wait_seconds} seconds.")


class InvalidChartConfigurationError(DomainError):
    """Raised when chart configuration is invalid."""
    
    def __init__(self, field: str, issue: str):
        self.field = field
        self.issue = issue
        super().__init__(f"Invalid chart configuration - {field}: {issue}")


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


__all__ = [
    "DomainError",
    "DomainValidationError",
    "EntityNotFoundError",
    "UnauthorizedOperationError",
    "InvalidStateTransitionError",
    "BusinessRuleViolationError",
    "DuplicateEntityError",
    "InsufficientPermissionsError",
    "AuthenticationFailedError",
    "AccountLockedError",
    "EmailNotVerifiedError",
    "TokenExpiredError",
    "TokenInvalidError",
    "ModelNotAvailableError",
    "TokenLimitExceededError",
    "InvalidPromptError",
    "ImageGenerationFailedError",
    "ChartGenerationFailedError",
    "MessageRateLimitExceededError",
    "InvalidChartConfigurationError",
    "DataSourceNotFoundError",
    "InvalidDataFormatError",
]