"""
Unit tests for command handlers.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from src.application.commands import (
    CreateUserCommand,
    SendMessageCommand,
    GenerateImageCommand,
    DeleteConversationCommand,
)
from src.application.handlers import (
    UserCommandHandler,
    ConversationCommandHandler,
    AssetCommandHandler,
)
from src.application.dtos import UserDTO, LLMResponseDTO, AssetDTO
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.shared.constants import UserRole


class TestUserCommandHandler:
    """Test cases for UserCommandHandler."""
    
    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_auth_service(self):
        service = Mock()
        service.can_register = AsyncMock(return_value=(True, None))
        service.hash_password = Mock(return_value="hashed_password")
        return service
    
    @pytest.fixture
    def handler(self, mock_user_repository, mock_auth_service):
        return UserCommandHandler(
            user_repository=mock_user_repository,
            authentication_service=mock_auth_service,
        )
    
    @pytest.mark.asyncio
    async def test_handle_create_user_success(self, handler, mock_user_repository):
        """Test successful user creation."""
        command = CreateUserCommand(
            email="new@example.com",
            username="newuser",
            password="SecurePass123!",
            full_name="New User",
        )
        
        expected_user = User(
            email=Email("new@example.com"),
            username="newuser",
            hashed_password="hashed_password",
            full_name="New User",
            role=UserRole.USER,
        )
        mock_user_repository.add.return_value = expected_user
        
        user_dto, errors = await handler.handle_create_user(command)
        
        assert errors == []
        assert user_dto is not None
        assert user_dto.email == "new@example.com"
        assert user_dto.username == "newuser"
        mock_user_repository.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_create_user_validation_error(self, handler):
        """Test user creation with invalid data."""
        command = CreateUserCommand(
            email="invalid-email",
            username="ab",  # Too short
            password="weak",
        )
        
        user_dto, errors = await handler.handle_create_user(command)
        
        assert user_dto is None
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_handle_create_user_duplicate(self, handler, mock_auth_service):
        """Test creating duplicate user fails."""
        mock_auth_service.can_register.return_value = (False, "Email already registered")
        
        command = CreateUserCommand(
            email="existing@example.com",
            username="newuser",
            password="SecurePass123!",
        )
        
        user_dto, errors = await handler.handle_create_user(command)
        
        assert user_dto is None
        assert "Email already registered" in errors[0]


class TestConversationCommandHandler:
    """Test cases for ConversationCommandHandler."""
    
    @pytest.fixture
    def mock_conversation_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_llm_service(self):
        service = Mock()
        service.generate_response = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def handler(self, mock_conversation_repository, mock_llm_service, mock_user_repository):
        return ConversationCommandHandler(
            conversation_repository=mock_conversation_repository,
            message_repository=mock_conversation_repository,
            llm_service=mock_llm_service,
            user_repository=mock_user_repository,
        )
    
    @pytest.mark.asyncio
    async def test_handle_send_message_success(self, handler, mock_conversation_repository, mock_llm_service):
        """Test successful message sending."""
        from src.domain.entities.conversation import Conversation
        from src.shared.constants import ConversationStatus
        
        conversation = Conversation(
            user_id=uuid4(),
            title="Test",
            model_name="deepseek-r1:7b",
            status=ConversationStatus.ACTIVE,
        )
        mock_conversation_repository.get_conversation_with_messages.return_value = conversation
        
        mock_response = Mock()
        mock_response.content = "AI response"
        mock_response.model_used = "deepseek-r1:7b"
        mock_response.tokens_used = 50
        mock_response.generation_time_ms = 100.0
        mock_response.finish_reason = "stop"
        mock_llm_service.generate_response.return_value = mock_response
        
        command = SendMessageCommand(
            conversation_id=conversation.id,
            content="Hello",
            user_id=conversation.user_id,
        )
        
        response_dto, errors = await handler.handle_send_message(command)
        
        assert errors == []
        assert response_dto is not None
        assert response_dto.content == "AI response"
    
    @pytest.mark.asyncio
    async def test_handle_send_message_conversation_not_found(self, handler, mock_conversation_repository):
        """Test sending message to non-existent conversation."""
        mock_conversation_repository.get_conversation_with_messages.return_value = None
        
        command = SendMessageCommand(
            conversation_id=uuid4(),
            content="Hello",
            user_id=uuid4(),
        )
        
        response_dto, errors = await handler.handle_send_message(command)
        
        assert response_dto is None
        assert "not found" in errors[0]
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, handler, mock_conversation_repository, mock_user_repository):
        """Test creating a new conversation."""
        user = User(
            email=Email("test@example.com"),
            username="testuser",
            hashed_password="hash",
        )
        mock_user_repository.get_by_id.return_value = user
        mock_conversation_repository.get_active_conversations.return_value = []
        
        conv_dto, errors = await handler.create_conversation(
            user_id=user.id,
            title="New Chat",
            model_name="llama3.2:7b",
        )
        
        assert errors == []
        assert conv_dto is not None
        assert conv_dto.title == "New Chat"
        assert conv_dto.model_name == "llama3.2:7b"