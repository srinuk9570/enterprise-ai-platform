"""
Shared module - Cross-cutting concerns used throughout the application.
Contains configuration, constants, enums, utilities, and decorators.
"""
from src.shared.config import settings, Settings
from src.shared.constants import (
    UserRole,
    MessageRole,
    ConversationStatus,
    AssetType,
    ChartType,
    ModelProvider,
    MODEL_TOKEN_LIMITS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_FREQUENCY_PENALTY,
)
from src.shared.enums import (
    SortOrder,
    DateRangePreset,
    ExportFormat,
    NotificationLevel,
    TaskStatus,
    LogLevel,
    AuthProvider,
    StorageProvider,
)
from src.shared.exceptions import (
    AppException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServiceUnavailableError,
    InternalServerError,
)

__all__ = [
    # Config
    "settings",
    "Settings",
    # Constants
    "UserRole",
    "MessageRole",
    "ConversationStatus",
    "AssetType",
    "ChartType",
    "ModelProvider",
    "MODEL_TOKEN_LIMITS",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TOP_P",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_PRESENCE_PENALTY",
    "DEFAULT_FREQUENCY_PENALTY",
    # Enums
    "SortOrder",
    "DateRangePreset",
    "ExportFormat",
    "NotificationLevel",
    "TaskStatus",
    "LogLevel",
    "AuthProvider",
    "StorageProvider",
    # Exceptions
    "AppException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServiceUnavailableError",
    "InternalServerError",
]