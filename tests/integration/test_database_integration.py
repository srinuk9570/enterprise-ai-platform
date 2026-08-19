"""
Integration tests for database operations.
"""
import pytest
from uuid import uuid4

from src.infrastructure.repositories.sqlite_user_repository import SQLiteUserRepository
from src.infrastructure.repositories.sqlite_conversation_repository import SQLiteConversationRepository
from src.domain.entities.user import User
from src.domain.entities.conversation import Conversation
from src.domain.value_objects.email import Email
from src.shared.constants import UserRole, ConversationStatus


class TestUserRepository:
    """Integration tests for UserRepository."""
    
    @pytest.mark.asyncio
    async def test_add_and_get_user(self, test_db):
        """Test adding and retrieving a user."""
        repo = SQLiteUserRepository()
        
        user = User(
            email=Email("test@example.com"),
            username="testuser",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
        )
        
        # Add user
        created = await repo.add(user)
        assert created.id == user.id
        
        # Get by ID
        retrieved = await repo.get_by_id(user.id)
        assert retrieved is not None
        assert retrieved.email.value == "test@example.com"
        assert retrieved.username == "testuser"
        
        # Get by email
        by_email = await repo.get_by_email("test@example.com")
        assert by_email is not None
        assert by_email.id == user.id
        
        # Get by username
        by_username = await repo.get_by_username("testuser")
        assert by_username is not None
        assert by_username.id == user.id
    
    @pytest.mark.asyncio
    async def test_update_user(self, test_db):
        """Test updating a user."""
        repo = SQLiteUserRepository()
        
        user = User(
            email=Email("test@example.com"),
            username="testuser",
            hashed_password="hashed_password",
        )
        
        created = await repo.add(user)
        
        # Update user
        created.update_profile(full_name="Updated Name")
        updated = await repo.update(created)
        
        assert updated.full_name == "Updated Name"
        
        # Verify in database
        retrieved = await repo.get_by_id(user.id)
        assert retrieved.full_name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, test_db):
        """Test deleting a user."""
        repo = SQLiteUserRepository()
        
        user = User(
            email=Email("delete@example.com"),
            username="deleteuser",
            hashed_password="hashed_password",
        )
        
        created = await repo.add(user)
        
        # Delete user
        deleted = await repo.delete(user.id)
        assert deleted is True
        
        # Verify deletion
        retrieved = await repo.get_by_id(user.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_email_exists(self, test_db):
        """Test checking if email exists."""
        repo = SQLiteUserRepository()
        
        user = User(
            email=Email("exists@example.com"),
            username="existsuser",
            hashed_password="hashed_password",
        )
        
        await repo.add(user)
        
        assert await repo.email_exists("exists@example.com") is True
        assert await repo.email_exists("nonexistent@example.com") is False
    
    @pytest.mark.asyncio
    async def test_username_exists(self, test_db):
        """Test checking if username exists."""
        repo = SQLiteUserRepository()
        
        user = User(
            email=Email("user@example.com"),
            username="uniqueuser",
            hashed_password="hashed_password",
        )
        
        await repo.add(user)
        
        assert await repo.username_exists("uniqueuser") is True
        assert await repo.username_exists("newuser") is False


class TestConversationRepository:
    """Integration tests for ConversationRepository."""
    
    @pytest.fixture
    async def test_user(self, test_db):
        """Create a test user."""
        repo = SQLiteUserRepository()
        user = User(
            email=Email("convuser@example.com"),
            username="convuser",
            hashed_password="hashed_password",
        )
        return await repo.add(user)
    
    @pytest.mark.asyncio
    async def test_add_and_get_conversation(self, test_db, test_user):
        """Test adding and retrieving a conversation."""
        repo = SQLiteConversationRepository()
        
        conv = Conversation(
            user_id=test_user.id,
            title="Test Conversation",
            model_name="deepseek-r1:7b",
        )
        
        # Add conversation
        created = await repo.add(conv)
        assert created.id == conv.id
        
        # Get by ID
        retrieved = await repo.get_by_id(conv.id)
        assert retrieved is not None
        assert retrieved.title == "Test Conversation"
        assert retrieved.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_add_message(self, test_db, test_user):
        """Test adding a message to conversation."""
        conv_repo = SQLiteConversationRepository()
        
        conv = Conversation(
            user_id=test_user.id,
            title="Test Conversation",
            model_name="deepseek-r1:7b",
        )
        created_conv = await conv_repo.add(conv)
        
        # Add message
        from src.domain.entities.message import Message
        from src.shared.constants import MessageRole
        
        message = Message(
            conversation_id=created_conv.id,
            role=MessageRole.USER,
            content="Hello, world!",
            sequence_number=0,
            token_count=10,
        )
        
        added_msg = await conv_repo.add_message(created_conv.id, message)
        assert added_msg.id == message.id
        
        # Get messages
        messages = await conv_repo.get_messages(created_conv.id)
        assert len(messages) == 1
        assert messages[0].content == "Hello, world!"
        
        # Verify conversation stats updated
        updated_conv = await conv_repo.get_by_id(created_conv.id)
        assert updated_conv.message_count == 1
        assert updated_conv.total_tokens == 10
    
    @pytest.mark.asyncio
    async def test_get_user_conversations(self, test_db, test_user):
        """Test getting conversations by user."""
        repo = SQLiteConversationRepository()
        
        conv1 = Conversation(
            user_id=test_user.id,
            title="Conversation 1",
            model_name="deepseek-r1:7b",
        )
        conv2 = Conversation(
            user_id=test_user.id,
            title="Conversation 2",
            model_name="llama3.2:7b",
        )
        
        await repo.add(conv1)
        await repo.add(conv2)
        
        conversations = await repo.get_by_user_id(test_user.id)
        assert len(conversations) == 2
    
    @pytest.mark.asyncio
    async def test_search_conversations(self, test_db, test_user):
        """Test searching conversations."""
        repo = SQLiteConversationRepository()
        
        conv1 = Conversation(
            user_id=test_user.id,
            title="AI Research",
            model_name="deepseek-r1:7b",
        )
        conv2 = Conversation(
            user_id=test_user.id,
            title="Code Review",
            model_name="codellama:7b",
        )
        
        await repo.add(conv1)
        await repo.add(conv2)
        
        # Search by title
        results = await repo.search_conversations(test_user.id, "Research")
        assert len(results) == 1
        assert results[0].title == "AI Research"
        
        # Search by model
        results = await repo.search_conversations(test_user.id, "codellama")
        assert len(results) == 1
        assert results[0].title == "Code Review"