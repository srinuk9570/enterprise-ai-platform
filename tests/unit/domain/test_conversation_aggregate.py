"""
Unit tests for Conversation aggregate.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.shared.constants import ConversationStatus, MessageRole
from src.domain.exceptions import DomainValidationError, InvalidStateTransitionError


class TestConversationAggregate:
    """Test cases for Conversation aggregate."""
    
    def test_create_valid_conversation(self):
        """Test creating a valid conversation."""
        conv = Conversation(
            user_id=uuid4(),
            title="Test Conversation",
            model_name="deepseek-r1:7b",
        )
        
        assert conv.title == "Test Conversation"
        assert conv.model_name == "deepseek-r1:7b"
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.message_count == 0
        assert conv.total_tokens == 0
    
    def test_create_conversation_with_empty_title(self):
        """Test creating conversation with empty title fails."""
        with pytest.raises(DomainValidationError, match="Conversation title cannot be empty"):
            Conversation(
                user_id=uuid4(),
                title="",
                model_name="deepseek-r1:7b",
            )
    
    def test_create_conversation_with_long_title(self):
        """Test creating conversation with too long title fails."""
        long_title = "a" * 201
        with pytest.raises(DomainValidationError, match="at most 200 characters"):
            Conversation(
                user_id=uuid4(),
                title=long_title,
                model_name="deepseek-r1:7b",
            )
    
    def test_add_message(self, sample_conversation):
        """Test adding a message to conversation."""
        message = sample_conversation.add_message(
            role=MessageRole.USER,
            content="Hello, world!",
            tokens=10,
        )
        
        assert sample_conversation.message_count == 1
        assert sample_conversation.total_tokens == 10
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.sequence_number == 0
    
    def test_add_multiple_messages(self, sample_conversation):
        """Test adding multiple messages."""
        msg1 = sample_conversation.add_message(MessageRole.USER, "First", 5)
        msg2 = sample_conversation.add_message(MessageRole.ASSISTANT, "Second", 8)
        msg3 = sample_conversation.add_message(MessageRole.USER, "Third", 6)
        
        assert sample_conversation.message_count == 3
        assert sample_conversation.total_tokens == 19
        assert msg1.sequence_number == 0
        assert msg2.sequence_number == 1
        assert msg3.sequence_number == 2
    
    def test_add_message_to_archived_conversation(self, sample_conversation):
        """Test adding message to archived conversation fails."""
        sample_conversation.archive()
        
        with pytest.raises(InvalidStateTransitionError):
            sample_conversation.add_message(MessageRole.USER, "Hello", 10)
    
    def test_add_message_to_deleted_conversation(self, sample_conversation):
        """Test adding message to deleted conversation fails."""
        sample_conversation.delete()
        
        with pytest.raises(InvalidStateTransitionError):
            sample_conversation.add_message(MessageRole.USER, "Hello", 10)
    
    def test_get_messages_for_llm(self, sample_conversation):
        """Test formatting messages for LLM API."""
        sample_conversation.system_prompt = "You are helpful."
        sample_conversation.add_message(MessageRole.USER, "Hello", 5)
        sample_conversation.add_message(MessageRole.ASSISTANT, "Hi there!", 5)
        
        messages = sample_conversation.get_messages_for_llm()
        
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Hi there!"
    
    def test_archive_conversation(self, sample_conversation):
        """Test archiving a conversation."""
        assert sample_conversation.status == ConversationStatus.ACTIVE
        
        sample_conversation.archive()
        assert sample_conversation.status == ConversationStatus.ARCHIVED
    
    def test_archive_already_archived(self, sample_conversation):
        """Test archiving already archived conversation fails."""
        sample_conversation.archive()
        
        with pytest.raises(InvalidStateTransitionError):
            sample_conversation.archive()
    
    def test_unarchive_conversation(self, sample_conversation):
        """Test unarchiving a conversation."""
        sample_conversation.archive()
        assert sample_conversation.status == ConversationStatus.ARCHIVED
        
        sample_conversation.unarchive()
        assert sample_conversation.status == ConversationStatus.ACTIVE
    
    def test_delete_conversation(self, sample_conversation):
        """Test soft deleting a conversation."""
        assert sample_conversation.status == ConversationStatus.ACTIVE
        
        sample_conversation.delete()
        assert sample_conversation.status == ConversationStatus.DELETED
    
    def test_restore_conversation(self, sample_conversation):
        """Test restoring a deleted conversation."""
        sample_conversation.delete()
        assert sample_conversation.status == ConversationStatus.DELETED
        
        sample_conversation.restore()
        assert sample_conversation.status == ConversationStatus.ACTIVE
    
    def test_update_title(self, sample_conversation):
        """Test updating conversation title."""
        sample_conversation.update_title("New Title")
        assert sample_conversation.title == "New Title"
    
    def test_set_system_prompt(self, sample_conversation):
        """Test setting system prompt."""
        sample_conversation.set_system_prompt("You are a helpful assistant.")
        assert sample_conversation.system_prompt == "You are a helpful assistant."
    
    def test_set_long_system_prompt(self, sample_conversation):
        """Test setting too long system prompt fails."""
        long_prompt = "a" * 2001
        
        with pytest.raises(DomainValidationError, match="at most 2000 characters"):
            sample_conversation.set_system_prompt(long_prompt)
    
    def test_add_and_remove_tags(self, sample_conversation):
        """Test adding and removing tags."""
        sample_conversation.add_tag("important")
        sample_conversation.add_tag("research")
        
        assert "important" in sample_conversation.tags
        assert "research" in sample_conversation.tags
        
        sample_conversation.remove_tag("research")
        assert "research" not in sample_conversation.tags
        assert "important" in sample_conversation.tags
    
    def test_toggle_pin(self, sample_conversation):
        """Test toggling pin status."""
        assert sample_conversation.is_pinned is False
        
        sample_conversation.toggle_pin()
        assert sample_conversation.is_pinned is True
        
        sample_conversation.toggle_pin()
        assert sample_conversation.is_pinned is False
    
    def test_toggle_favorite(self, sample_conversation):
        """Test toggling favorite status."""
        assert sample_conversation.is_favorite is False
        
        sample_conversation.toggle_favorite()
        assert sample_conversation.is_favorite is True
    
    def test_last_message_property(self, sample_conversation):
        """Test last message property."""
        assert sample_conversation.last_message is None
        
        sample_conversation.add_message(MessageRole.USER, "First", 5)
        sample_conversation.add_message(MessageRole.ASSISTANT, "Second", 5)
        
        assert sample_conversation.last_message.content == "Second"
    
    def test_message_count_display(self, sample_conversation):
        """Test message count display formatting."""
        assert sample_conversation.message_count_display == "No messages"
        
        sample_conversation.add_message(MessageRole.USER, "Hi", 2)
        assert sample_conversation.message_count_display == "1 message"
        
        sample_conversation.add_message(MessageRole.ASSISTANT, "Hello", 2)
        assert sample_conversation.message_count_display == "2 messages"