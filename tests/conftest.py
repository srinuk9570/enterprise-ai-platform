"""
Pytest fixtures and configuration.
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import json
import os

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"

from src.shared.config import settings
from src.infrastructure.database.sqlite.connection import DatabaseConnection
from src.infrastructure.database.sqlite.models import Base
from src.domain.entities.user import User
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.value_objects.email import Email
from src.shared.constants import UserRole, MessageRole, ConversationStatus


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def test_db() -> Generator[DatabaseConnection, None, None]:
    """
    Create a test database in memory.
    """
    db = DatabaseConnection()
    db.db_path = ":memory:"
    db.initialize_database()
    yield db


@pytest.fixture(scope="function")
def db_connection(test_db) -> Generator:
    """Get a database connection."""
    with test_db.get_cursor() as cursor:
        yield cursor


# ==================== Entity Fixtures ====================

@pytest.fixture
def sample_user() -> User:
    """Create a sample user entity."""
    return User(
        id=uuid4(),
        email=Email("test@example.com"),
        username="testuser",
        hashed_password="hashed_password_123",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_admin_user() -> User:
    """Create a sample admin user entity."""
    return User(
        id=uuid4(),
        email=Email("admin@example.com"),
        username="admin",
        hashed_password="hashed_password_123",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_conversation(sample_user) -> Conversation:
    """Create a sample conversation entity."""
    return Conversation(
        id=uuid4(),
        user_id=sample_user.id,
        title="Test Conversation",
        model_name="deepseek-r1:7b",
        status=ConversationStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_message(sample_conversation) -> Message:
    """Create a sample message entity."""
    return Message(
        id=uuid4(),
        conversation_id=sample_conversation.id,
        role=MessageRole.USER,
        content="Hello, this is a test message.",
        sequence_number=1,
        token_count=10,
        created_at=datetime.utcnow(),
    )


# ==================== Mock Data Fixtures ====================

@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """Sample user data for API requests."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "SecurePass123!",
        "full_name": "New User",
    }


@pytest.fixture
def mock_login_data() -> Dict[str, Any]:
    """Sample login data."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
    }


@pytest.fixture
def mock_chat_message() -> Dict[str, Any]:
    """Sample chat message data."""
    return {
        "message": "What is artificial intelligence?",
        "model": "deepseek-r1:7b",
        "temperature": 0.7,
        "max_tokens": 2048,
    }


@pytest.fixture
def mock_image_prompt() -> Dict[str, Any]:
    """Sample image generation prompt."""
    return {
        "prompt": "A beautiful mountain landscape at sunset",
        "negative_prompt": "blurry, low quality",
        "width": 1024,
        "height": 1024,
        "num_images": 1,
    }


# ==================== Mock Client Fixtures ====================

class MockOllamaClient:
    """Mock Ollama client for testing."""
    
    async def chat(self, model: str, messages: list, **kwargs):
        return "This is a mock response from the AI.", {
            "model": model,
            "tokens": 50,
            "generation_time_ms": 100.0,
            "finish_reason": "stop",
        }
    
    async def stream_chat(self, model: str, messages: list, **kwargs):
        yield {"content": "This "}
        yield {"content": "is "}
        yield {"content": "a "}
        yield {"content": "mock "}
        yield {"content": "response."}
        yield {"done": True, "metadata": {"tokens": 5}}
    
    async def generate_image(self, model: str, prompt: str, **kwargs):
        return {
            "file_path": "/tmp/mock_image.png",
            "file_name": "mock_image.png",
            "file_size": 1024,
            "mime_type": "image/png",
            "model_used": model,
            "generation_time_ms": 500.0,
        }
    
    async def list_models(self):
        return ["deepseek-r1:7b", "llama3.2:7b", "qwen2.5:7b"]
    
    async def health_check(self):
        return True


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client fixture."""
    return MockOllamaClient()


class MockRedisClient:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self._data = {}
    
    async def get(self, key: str):
        return self._data.get(key)
    
    async def set(self, key: str, value: Any, ex: int = None):
        self._data[key] = value
    
    async def delete(self, key: str):
        self._data.pop(key, None)
    
    async def exists(self, key: str):
        return key in self._data


@pytest.fixture
def mock_redis_client():
    """Mock Redis client fixture."""
    return MockRedisClient()


# ==================== Auth Fixtures ====================

@pytest.fixture
def auth_headers(sample_user) -> Dict[str, str]:
    """Create authorization headers with JWT token."""
    from src.infrastructure.security.jwt_handler import JWTHandler
    
    jwt_handler = JWTHandler()
    token = jwt_handler.create_access_token(
        user_id=sample_user.id,
        username=sample_user.username,
        role=sample_user.role,
        email=str(sample_user.email),
    )
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(sample_admin_user) -> Dict[str, str]:
    """Create authorization headers for admin user."""
    from src.infrastructure.security.jwt_handler import JWTHandler
    
    jwt_handler = JWTHandler()
    token = jwt_handler.create_access_token(
        user_id=sample_admin_user.id,
        username=sample_admin_user.username,
        role=sample_admin_user.role,
        email=str(sample_admin_user.email),
    )
    
    return {"Authorization": f"Bearer {token}"}


# ==================== Async Fixtures ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== Temp File Fixtures ====================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir) -> Generator[Path, None, None]:
    """Create a temporary file."""
    filepath = temp_dir / "test_file.txt"
    filepath.write_text("Test content")
    yield filepath


@pytest.fixture
def sample_csv_file(temp_dir) -> Path:
    """Create a sample CSV file."""
    import pandas as pd
    
    filepath = temp_dir / "sample_data.csv"
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "value": [100, 150, 200],
        "category": ["A", "B", "A"],
    })
    df.to_csv(filepath, index=False)
    return filepath


# ==================== Fixture Cleanup ====================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data after each test."""
    yield
    # Clean up any global state if needed