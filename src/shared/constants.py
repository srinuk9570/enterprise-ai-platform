"""
Application-wide constants.
"""
from enum import Enum


# ==================== User Roles ====================
class UserRole(str, Enum):
    """User role enumeration for RBAC."""
    ADMIN = "admin"
    POWER_USER = "power_user"
    USER = "user"
    VIEWER = "viewer"


# ==================== Message Roles ====================
class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# ==================== Conversation Status ====================
class ConversationStatus(str, Enum):
    """Conversation status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"


# ==================== Asset Types ====================
class AssetType(str, Enum):
    """Generated asset types."""
    IMAGE = "image"
    CHART = "chart"
    EXPORT = "export"
    DOCUMENT = "document"


# ==================== Chart Types ====================
class ChartType(str, Enum):
    """Supported chart types."""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    PIE = "pie"
    RADAR = "radar"
    CANDLESTICK = "candlestick"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"


# ==================== Model Provider ====================
class ModelProvider(str, Enum):
    """LLM model providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"


# ==================== Token Limits ====================
MODEL_TOKEN_LIMITS = {
    "deepseek-r1:1.5b": 4096,
    "deepseek-r1:7b": 8192,
    "deepseek-r1:14b": 16384,
    "llama3.2:3b": 4096,
    "llama3.2:7b": 8192,
    "llama3.2:70b": 32768,
    "qwen2.5:7b": 32768,
    "qwen2.5:14b": 32768,
    "mistral:7b": 8192,
    "codellama:7b": 16384,
    "codellama:13b": 16384,
    "nomic-embed-text": 8192,
}

# ==================== Default Model Parameters ====================
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40
DEFAULT_MAX_TOKENS = 2048
DEFAULT_PRESENCE_PENALTY = 0.0
DEFAULT_FREQUENCY_PENALTY = 0.0
DEFAULT_REPETITION_PENALTY = 1.0

# ==================== Image Generation Defaults ====================
DEFAULT_IMAGE_WIDTH = 1024
DEFAULT_IMAGE_HEIGHT = 1024
DEFAULT_IMAGE_STEPS = 50
DEFAULT_GUIDANCE_SCALE = 7.5

# ==================== File Size Limits ====================
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DOCUMENT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

# ==================== Pagination ====================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_SKIP = 0

# ==================== Time Constants ====================
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
MILLISECONDS_PER_SECOND = 1000

# ==================== Cache Keys ====================
CACHE_KEY_USER = "user:{user_id}"
CACHE_KEY_CONVERSATION = "conversation:{conversation_id}"
CACHE_KEY_MESSAGES = "messages:{conversation_id}"
CACHE_KEY_MODELS = "models:available"
CACHE_KEY_RATE_LIMIT = "rate_limit:{identifier}:{endpoint}"

# ==================== HTTP Headers ====================
HEADER_REQUEST_ID = "X-Request-ID"
HEADER_CORRELATION_ID = "X-Correlation-ID"
HEADER_RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
HEADER_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
HEADER_RATE_LIMIT_RESET = "X-RateLimit-Reset"

# ==================== Content Types ====================
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_SSE = "text/event-stream"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
CONTENT_TYPE_MULTIPART = "multipart/form-data"

# ==================== Character Sets ====================
ALPHABET_LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
ALPHABET_UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
ALPHANUMERIC = ALPHABET_LOWERCASE + ALPHABET_UPPERCASE + DIGITS