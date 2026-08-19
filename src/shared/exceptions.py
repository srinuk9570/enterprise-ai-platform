"""
Application-wide exception classes.
"""
from typing import Optional, Dict, Any, List
from http import HTTPStatus


class AppException(Exception):
    """
    Base exception class for the application.
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        result = {
            "error": self.code,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            result["details"] = self.details
        return result


# ==================== Validation Errors ====================

class ValidationError(AppException):
    """
    Raised when input validation fails.
    """
    
    def __init__(
        self,
        message: str = "Validation error",
        field_errors: Optional[Dict[str, List[str]]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST,
            details={"field_errors": field_errors} if field_errors else None,
        )
        self.field_errors = field_errors or {}


class InvalidInputError(ValidationError):
    """Raised when input format is invalid."""
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Invalid input for field '{field}': {reason}",
            field_errors={field: [reason]},
        )


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid."""
    
    def __init__(self, email: str):
        super().__init__(
            message=f"Invalid email format: {email}",
            field_errors={"email": ["Invalid email format"]},
        )


class InvalidUsernameError(ValidationError):
    """Raised when username format is invalid."""
    
    def __init__(self, username: str, reason: str):
        super().__init__(
            message=f"Invalid username '{username}': {reason}",
            field_errors={"username": [reason]},
        )


class WeakPasswordError(ValidationError):
    """Raised when password doesn't meet strength requirements."""
    
    def __init__(self, issues: List[str]):
        super().__init__(
            message=f"Weak password: {', '.join(issues)}",
            field_errors={"password": issues},
        )


# ==================== Authentication Errors ====================

class AuthenticationError(AppException):
    """
    Raised when authentication fails.
    """
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=HTTPStatus.UNAUTHORIZED,
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    
    def __init__(self):
        super().__init__(message="Invalid email/username or password")


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""
    
    def __init__(self):
        super().__init__(message="Token has expired")


class TokenInvalidError(AuthenticationError):
    """Raised when JWT token is invalid."""
    
    def __init__(self, reason: Optional[str] = None):
        message = "Invalid token"
        if reason:
            message += f": {reason}"
        super().__init__(message=message)


class AccountLockedError(AuthenticationError):
    """Raised when account is locked."""
    
    def __init__(self, unlock_at: Optional[str] = None):
        message = "Account is locked due to too many failed attempts"
        details = {}
        if unlock_at:
            message += f". Unlocks at {unlock_at}"
            details["unlock_at"] = unlock_at
        super().__init__(message=message)
        self.details = details


class EmailNotVerifiedError(AuthenticationError):
    """Raised when email is not verified."""
    
    def __init__(self, email: str):
        super().__init__(message=f"Email {email} is not verified")


# ==================== Authorization Errors ====================

class AuthorizationError(AppException):
    """
    Raised when user doesn't have required permissions.
    """
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
        )


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks specific permission."""
    
    def __init__(self, required_permission: str):
        super().__init__(
            message=f"Missing required permission: {required_permission}",
            required_permission=required_permission,
        )


# ==================== Not Found Errors ====================

class NotFoundError(AppException):
    """
    Raised when a resource is not found.
    """
    
    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class UserNotFoundError(NotFoundError):
    """Raised when user is not found."""
    
    def __init__(self, identifier: str):
        super().__init__(resource_type="User", resource_id=identifier)


class ConversationNotFoundError(NotFoundError):
    """Raised when conversation is not found."""
    
    def __init__(self, conversation_id: str):
        super().__init__(resource_type="Conversation", resource_id=conversation_id)


class ModelNotFoundError(NotFoundError):
    """Raised when model is not found."""
    
    def __init__(self, model_name: str):
        super().__init__(resource_type="Model", resource_id=model_name)


class AssetNotFoundError(NotFoundError):
    """Raised when asset is not found."""
    
    def __init__(self, asset_id: str):
        super().__init__(resource_type="Asset", resource_id=asset_id)


# ==================== Conflict Errors ====================

class ConflictError(AppException):
    """
    Raised when there's a resource conflict (e.g., duplicate).
    """
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=HTTPStatus.CONFLICT,
        )


class DuplicateEntityError(ConflictError):
    """Raised when attempting to create duplicate entity."""
    
    def __init__(self, entity_type: str, field: str, value: str):
        super().__init__(
            message=f"{entity_type} with {field} '{value}' already exists"
        )


class EmailAlreadyExistsError(DuplicateEntityError):
    """Raised when email is already registered."""
    
    def __init__(self, email: str):
        super().__init__(entity_type="User", field="email", value=email)


class UsernameAlreadyExistsError(DuplicateEntityError):
    """Raised when username is already taken."""
    
    def __init__(self, username: str):
        super().__init__(entity_type="User", field="username", value=username)


# ==================== Rate Limit Errors ====================

class RateLimitError(AppException):
    """
    Raised when rate limit is exceeded.
    """
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
        )
        self.retry_after = retry_after


class MessageRateLimitError(RateLimitError):
    """Raised when message rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Message rate limit exceeded. Try again in {retry_after} seconds.",
            retry_after=retry_after,
        )


class TokenLimitExceededError(AppException):
    """Raised when token limit is exceeded."""
    
    def __init__(self, current: int, limit: int):
        super().__init__(
            message=f"Token limit exceeded: {current}/{limit}",
            code="TOKEN_LIMIT_EXCEEDED",
            status_code=HTTPStatus.BAD_REQUEST,
            details={"current": current, "limit": limit},
        )


class QuotaExceededError(AppException):
    """Raised when user exceeds their quota."""
    
    def __init__(self, quota_type: str, limit: int, current: int):
        super().__init__(
            message=f"{quota_type} quota exceeded: {current}/{limit}",
            code="QUOTA_EXCEEDED",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            details={"quota_type": quota_type, "limit": limit, "current": current},
        )


# ==================== Service Errors ====================

class ServiceUnavailableError(AppException):
    """
    Raised when a service is unavailable.
    """
    
    def __init__(self, service: str, reason: Optional[str] = None):
        message = f"Service '{service}' is unavailable"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details={"service": service, "reason": reason},
        )


class ModelNotAvailableError(ServiceUnavailableError):
    """Raised when LLM model is not available."""
    
    def __init__(self, model_name: str, reason: Optional[str] = None):
        super().__init__(service=f"Model:{model_name}", reason=reason)
        self.model_name = model_name


class DatabaseError(AppException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class InternalServerError(AppException):
    """
    Raised for unexpected internal errors.
    """
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            code="INTERNAL_SERVER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


# ==================== Business Logic Errors ====================

class BusinessRuleViolationError(AppException):
    """
    Raised when a business rule is violated.
    """
    
    def __init__(self, message: str, rule: Optional[str] = None):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            status_code=HTTPStatus.BAD_REQUEST,
            details={"rule": rule} if rule else None,
        )


class InvalidStateTransitionError(BusinessRuleViolationError):
    """Raised when invalid state transition is attempted."""
    
    def __init__(self, current_state: str, target_state: str):
        super().__init__(
            message=f"Cannot transition from '{current_state}' to '{target_state}'",
            rule="state_transition",
        )


class ConversationLimitExceededError(BusinessRuleViolationError):
    """Raised when user exceeds conversation limit."""
    
    def __init__(self, user_id: str, limit: int, current: int):
        super().__init__(
            message=f"Conversation limit exceeded: {current}/{limit}",
            rule="conversation_limit",
        )
        self.user_id = user_id
        self.limit = limit
        self.current = current


# ==================== File Errors ====================

class FileError(AppException):
    """Base class for file-related errors."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="FILE_ERROR",
            status_code=HTTPStatus.BAD_REQUEST,
        )


class FileTooLargeError(FileError):
    """Raised when uploaded file exceeds size limit."""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"File size {file_size} bytes exceeds maximum of {max_size} bytes"
        )
        self.file_size = file_size
        self.max_size = max_size


class UnsupportedFileTypeError(FileError):
    """Raised when file type is not supported."""
    
    def __init__(self, file_type: str, supported_types: List[str]):
        super().__init__(
            message=f"Unsupported file type '{file_type}'. Supported: {', '.join(supported_types)}"
        )
        self.file_type = file_type
        self.supported_types = supported_types


class ImageGenerationFailedError(AppException):
    """Raised when image generation fails."""
    
    def __init__(self, prompt: str, reason: str, model: Optional[str] = None):
        super().__init__(
            message=f"Image generation failed: {reason}",
            code="IMAGE_GENERATION_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "reason": reason,
                "model": model,
            },
        )


class ChartGenerationFailedError(AppException):
    """Raised when chart generation fails."""
    
    def __init__(self, chart_type: str, reason: str):
        super().__init__(
            message=f"Chart generation failed for {chart_type}: {reason}",
            code="CHART_GENERATION_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"chart_type": chart_type, "reason": reason},
        )