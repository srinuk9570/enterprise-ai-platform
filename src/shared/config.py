"""
Central configuration management using Pydantic Settings.
All environment variables are validated and typed here.
"""
import os
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # ==================== Application ====================
    APP_NAME: str = Field("Enterprise AI Platform", env="APP_NAME")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(False, env="DEBUG")
    SECRET_KEY: str = Field("change-this-secret-key-in-production", env="SECRET_KEY")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    
    # ==================== Server ====================
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    API_PREFIX: str = Field("/api", env="API_PREFIX")
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8501", "http://localhost:8000"],
        env="CORS_ORIGINS",
    )
    
    # ==================== Paths ====================
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_PATH: str = Field(str(DATA_DIR / "database" / "app.db"), env="DATABASE_PATH")
    VECTOR_STORE_PATH: str = Field(str(DATA_DIR / "vector_store"), env="VECTOR_STORE_PATH")
    GENERATED_IMAGES_PATH: str = Field(str(DATA_DIR / "generated" / "images"), env="GENERATED_IMAGES_PATH")
    GENERATED_CHARTS_PATH: str = Field(str(DATA_DIR / "generated" / "charts"), env="GENERATED_CHARTS_PATH")
    LOG_FILE_PATH: str = Field(str(DATA_DIR / "logs" / "app.log"), env="LOG_FILE_PATH")
    UPLOAD_PATH: str = Field(str(DATA_DIR / "uploads"), env="UPLOAD_PATH")
    
    # ==================== Database ====================
    DATABASE_URL: str = Field("sqlite:///./data/database/app.db", env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(10, env="DB_MAX_OVERFLOW")
    DB_ECHO: bool = Field(False, env="DB_ECHO")
    
    # ==================== Redis ====================
    REDIS_ENABLED: bool = Field(False, env="REDIS_ENABLED")
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    
    @property
    def redis_connection_url(self) -> str:
        """Construct Redis connection URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ==================== Ollama LLM ====================
    OLLAMA_HOST: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    OLLAMA_TIMEOUT: int = Field(300, env="OLLAMA_TIMEOUT")
    DEFAULT_MODEL: str = Field("deepseek-r1:7b", env="DEFAULT_MODEL")
    FALLBACK_MODEL: str = Field("llama3.2:3b", env="FALLBACK_MODEL")
    IMAGE_MODEL: str = Field("x/z-image-turbo", env="IMAGE_MODEL")
    EMBEDDING_MODEL: str = Field("nomic-embed-text", env="EMBEDDING_MODEL")
    
    # ==================== Security ====================
    JWT_SECRET_KEY: str = Field("change-this-jwt-secret-in-production", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    BCRYPT_ROUNDS: int = Field(12, env="BCRYPT_ROUNDS")
    
    # API Key settings
    API_KEY_PREFIX: str = Field("eap_", env="API_KEY_PREFIX")
    API_KEY_LENGTH: int = Field(32, env="API_KEY_LENGTH")
    
    # Password policy
    PASSWORD_MIN_LENGTH: int = Field(8, env="PASSWORD_MIN_LENGTH")
    PASSWORD_REQUIRE_UPPER: bool = Field(True, env="PASSWORD_REQUIRE_UPPER")
    PASSWORD_REQUIRE_LOWER: bool = Field(True, env="PASSWORD_REQUIRE_LOWER")
    PASSWORD_REQUIRE_DIGIT: bool = Field(True, env="PASSWORD_REQUIRE_DIGIT")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(True, env="PASSWORD_REQUIRE_SPECIAL")
    
    # ==================== Rate Limiting ====================
    RATE_LIMIT_ENABLED: bool = Field(True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD_SECONDS: int = Field(60, env="RATE_LIMIT_PERIOD_SECONDS")
    RATE_LIMIT_BLOCK_DURATION: int = Field(300, env="RATE_LIMIT_BLOCK_DURATION")
    
    # Tiered limits
    RATE_LIMIT_VIEWER: int = Field(30, env="RATE_LIMIT_VIEWER")
    RATE_LIMIT_USER: int = Field(100, env="RATE_LIMIT_USER")
    RATE_LIMIT_POWER_USER: int = Field(300, env="RATE_LIMIT_POWER_USER")
    RATE_LIMIT_ADMIN: int = Field(1000, env="RATE_LIMIT_ADMIN")
    
    # ==================== File Upload ====================
    MAX_UPLOAD_SIZE_MB: int = Field(50, env="MAX_UPLOAD_SIZE_MB")
    ALLOWED_EXTENSIONS: List[str] = Field(
        [".csv", ".json", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".gif"],
        env="ALLOWED_EXTENSIONS",
    )
    ALLOWED_MIME_TYPES: List[str] = Field(
        ["text/csv", "application/json", "text/plain", "application/pdf", 
         "image/png", "image/jpeg", "image/gif"],
        env="ALLOWED_MIME_TYPES",
    )
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # ==================== Logging ====================
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", env="LOG_FORMAT")
    LOG_DATE_FORMAT: str = Field("%Y-%m-%d %H:%M:%S", env="LOG_DATE_FORMAT")
    LOG_JSON_ENABLED: bool = Field(True, env="LOG_JSON_ENABLED")
    LOG_RETENTION_DAYS: int = Field(30, env="LOG_RETENTION_DAYS")
    
    # ==================== Metrics ====================
    METRICS_ENABLED: bool = Field(True, env="METRICS_ENABLED")
    METRICS_EXPORT_INTERVAL: int = Field(60, env="METRICS_EXPORT_INTERVAL")
    
    # ==================== Email (Optional) ====================
    SMTP_ENABLED: bool = Field(False, env="SMTP_ENABLED")
    SMTP_HOST: str = Field("smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field("noreply@enterprise-ai.local", env="SMTP_FROM_EMAIL")
    SMTP_USE_TLS: bool = Field(True, env="SMTP_USE_TLS")
    
    # ==================== Features ====================
    FEATURE_IMAGE_GENERATION: bool = Field(True, env="FEATURE_IMAGE_GENERATION")
    FEATURE_CHART_GENERATION: bool = Field(True, env="FEATURE_CHART_GENERATION")
    FEATURE_RAG: bool = Field(True, env="FEATURE_RAG")
    FEATURE_STREAMING: bool = Field(True, env="FEATURE_STREAMING")
    FEATURE_WEBSOCKET: bool = Field(True, env="FEATURE_WEBSOCKET")
    FEATURE_API_KEYS: bool = Field(True, env="FEATURE_API_KEYS")
    
    # ==================== Limits ====================
    MAX_CONVERSATIONS_PER_USER: int = Field(100, env="MAX_CONVERSATIONS_PER_USER")
    MAX_MESSAGES_PER_CONVERSATION: int = Field(1000, env="MAX_MESSAGES_PER_CONVERSATION")
    MAX_TOKENS_PER_REQUEST: int = Field(8192, env="MAX_TOKENS_PER_REQUEST")
    MAX_IMAGE_GENERATIONS_PER_DAY: int = Field(50, env="MAX_IMAGE_GENERATIONS_PER_DAY")
    
    # ==================== Cache ====================
    CACHE_TTL_SHORT: int = Field(60, env="CACHE_TTL_SHORT")  # 1 minute
    CACHE_TTL_MEDIUM: int = Field(300, env="CACHE_TTL_MEDIUM")  # 5 minutes
    CACHE_TTL_LONG: int = Field(3600, env="CACHE_TTL_LONG")  # 1 hour
    CACHE_TTL_DAY: int = Field(86400, env="CACHE_TTL_DAY")  # 24 hours
    
    # ==================== Model Config ====================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            """Parse environment variables with special handling."""
            if field_name == "CORS_ORIGINS":
                return [origin.strip() for origin in raw_val.split(",")]
            if field_name == "ALLOWED_EXTENSIONS":
                return [ext.strip() for ext in raw_val.split(",")]
            if field_name == "ALLOWED_MIME_TYPES":
                return [mime.strip() for mime in raw_val.split(",")]
            return raw_val
    
    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        directories = [
            self.DATA_DIR,
            Path(self.DATABASE_PATH).parent,
            Path(self.VECTOR_STORE_PATH),
            Path(self.GENERATED_IMAGES_PATH),
            Path(self.GENERATED_CHARTS_PATH),
            Path(self.LOG_FILE_PATH).parent,
            Path(self.UPLOAD_PATH),
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ["production", "prod"]
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT.lower() in ["testing", "test"]
    
    def get_rate_limit_for_role(self, role: str) -> int:
        """Get rate limit for a user role."""
        role_limits = {
            "viewer": self.RATE_LIMIT_VIEWER,
            "user": self.RATE_LIMIT_USER,
            "power_user": self.RATE_LIMIT_POWER_USER,
            "admin": self.RATE_LIMIT_ADMIN,
        }
        return role_limits.get(role.lower(), self.RATE_LIMIT_REQUESTS)


# Global settings instance
settings = Settings()
settings.ensure_directories()