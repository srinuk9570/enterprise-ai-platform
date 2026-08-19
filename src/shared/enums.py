"""
Shared enumerations used across the application.
"""
from enum import Enum, auto


class SortOrder(str, Enum):
    """Sort order for queries."""
    ASC = "asc"
    DESC = "desc"


class DateRangePreset(str, Enum):
    """Preset date ranges for filtering."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"
    ALL_TIME = "all_time"


class ExportFormat(str, Enum):
    """Export file formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    EXCEL = "xlsx"


class NotificationLevel(str, Enum):
    """Notification severity levels."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Background task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuthProvider(str, Enum):
    """Authentication providers."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    OAUTH2 = "oauth2"
    LDAP = "ldap"
    SAML = "saml"


class StorageProvider(str, Enum):
    """Storage providers."""
    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"
    MINIO = "minio"


class QueueType(str, Enum):
    """Message queue types."""
    MEMORY = "memory"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    SQS = "sqs"


class EventType(str, Enum):
    """System event types."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_UPDATED = "conversation.updated"
    CONVERSATION_DELETED = "conversation.deleted"
    
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    
    IMAGE_GENERATED = "image.generated"
    CHART_GENERATED = "chart.generated"
    
    MODEL_LOADED = "model.loaded"
    MODEL_UNLOADED = "model.unloaded"
    
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class Permission(str, Enum):
    """User permissions."""
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Conversation permissions
    CONVERSATION_CREATE = "conversation:create"
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_UPDATE = "conversation:update"
    CONVERSATION_DELETE = "conversation:delete"
    
    # Chat permissions
    CHAT_SEND = "chat:send"
    CHAT_STREAM = "chat:stream"
    
    # Image permissions
    IMAGE_GENERATE = "image:generate"
    IMAGE_READ = "image:read"
    IMAGE_DELETE = "image:delete"
    
    # Chart permissions
    CHART_CREATE = "chart:create"
    CHART_READ = "chart:read"
    CHART_DELETE = "chart:delete"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_USERS = "admin:users"
    ADMIN_MODELS = "admin:models"
    ADMIN_SETTINGS = "admin:settings"
    
    # API Key permissions
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_REVOKE = "api_key:revoke"


class FeatureFlag(str, Enum):
    """Feature flags."""
    IMAGE_GENERATION = "image_generation"
    CHART_GENERATION = "chart_generation"
    RAG = "rag"
    STREAMING = "streaming"
    WEBSOCKET = "websocket"
    API_KEYS = "api_keys"
    EMAIL_NOTIFICATIONS = "email_notifications"
    DARK_MODE = "dark_mode"
    BETA_FEATURES = "beta_features"