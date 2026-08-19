"""
Unit tests for User entity.
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.shared.constants import UserRole
from src.domain.exceptions import DomainValidationError


class TestUserEntity:
    """Test cases for User entity."""
    
    def test_create_valid_user(self):
        """Test creating a valid user."""
        user = User(
            email=Email("test@example.com"),
            username="testuser",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
        )
        
        assert user.email.value == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert isinstance(user.id, UUID)
    
    def test_create_user_with_invalid_username_short(self):
        """Test creating user with too short username."""
        with pytest.raises(DomainValidationError, match="Username must be at least 3 characters"):
            User(
                email=Email("test@example.com"),
                username="ab",
                hashed_password="hashed_password",
            )
    
    def test_create_user_with_invalid_username_long(self):
        """Test creating user with too long username."""
        long_username = "a" * 51
        with pytest.raises(DomainValidationError, match="Username must be at most 50 characters"):
            User(
                email=Email("test@example.com"),
                username=long_username,
                hashed_password="hashed_password",
            )
    
    def test_create_user_with_invalid_username_chars(self):
        """Test creating user with invalid characters in username."""
        with pytest.raises(DomainValidationError):
            User(
                email=Email("test@example.com"),
                username="test@user",
                hashed_password="hashed_password",
            )
    
    def test_update_profile(self, sample_user):
        """Test updating user profile."""
        sample_user.update_profile(
            full_name="Updated Name",
            bio="This is my bio",
        )
        
        assert sample_user.full_name == "Updated Name"
        assert sample_user.bio == "This is my bio"
    
    def test_update_profile_with_invalid_bio(self, sample_user):
        """Test updating profile with too long bio."""
        long_bio = "a" * 501
        
        with pytest.raises(DomainValidationError, match="Bio must be at most 500 characters"):
            sample_user.update_profile(bio=long_bio)
    
    def test_change_password(self, sample_user):
        """Test changing password."""
        old_hash = sample_user.hashed_password
        sample_user.change_password("new_hashed_password")
        
        assert sample_user.hashed_password == "new_hashed_password"
        assert sample_user.hashed_password != old_hash
    
    def test_deactivate_user(self, sample_user):
        """Test deactivating a user."""
        assert sample_user.is_active is True
        
        sample_user.deactivate()
        assert sample_user.is_active is False
    
    def test_deactivate_already_deactivated(self, sample_user):
        """Test deactivating an already deactivated user."""
        sample_user.deactivate()
        
        with pytest.raises(DomainValidationError, match="User is already deactivated"):
            sample_user.deactivate()
    
    def test_activate_user(self, sample_user):
        """Test activating a user."""
        sample_user.deactivate()
        assert sample_user.is_active is False
        
        sample_user.activate()
        assert sample_user.is_active is True
    
    def test_verify_email(self, sample_user):
        """Test verifying user email."""
        assert sample_user.is_verified is False
        assert sample_user.email_verified_at is None
        
        sample_user.verify_email()
        
        assert sample_user.is_verified is True
        assert sample_user.email_verified_at is not None
    
    def test_promote_to_role(self, sample_user, sample_admin_user):
        """Test promoting user to higher role."""
        assert sample_user.role == UserRole.USER
        
        sample_user.promote_to_role(UserRole.POWER_USER, promoted_by=sample_admin_user)
        assert sample_user.role == UserRole.POWER_USER
    
    def test_promote_to_same_or_lower_role(self, sample_user, sample_admin_user):
        """Test promoting to same or lower role fails."""
        with pytest.raises(DomainValidationError):
            sample_user.promote_to_role(UserRole.USER, promoted_by=sample_admin_user)
        
        with pytest.raises(DomainValidationError):
            sample_user.promote_to_role(UserRole.VIEWER, promoted_by=sample_admin_user)
    
    def test_has_permission(self, sample_user, sample_admin_user):
        """Test permission checking."""
        # User can access viewer-level resources
        assert sample_user.has_permission(UserRole.VIEWER) is True
        assert sample_user.has_permission(UserRole.USER) is True
        assert sample_user.has_permission(UserRole.POWER_USER) is False
        assert sample_user.has_permission(UserRole.ADMIN) is False
        
        # Admin can access everything
        assert sample_admin_user.has_permission(UserRole.VIEWER) is True
        assert sample_admin_user.has_permission(UserRole.ADMIN) is True
    
    def test_display_name(self, sample_user):
        """Test display name property."""
        assert sample_user.display_name == "Test User"
        
        sample_user.full_name = None
        assert sample_user.display_name == "testuser"
    
    def test_initials(self, sample_user):
        """Test initials property."""
        assert sample_user.initials == "TU"
        
        sample_user.full_name = "John Doe"
        assert sample_user.initials == "JD"
        
        sample_user.full_name = "Single"
        assert sample_user.initials == "SI"
    
    def test_record_login(self, sample_user):
        """Test recording login."""
        assert sample_user.last_login_at is None
        
        sample_user.record_login()
        assert sample_user.last_login_at is not None
    
    def test_to_dict(self, sample_user):
        """Test converting user to dictionary."""
        data = sample_user.to_dict()
        
        assert data["id"] == str(sample_user.id)
        assert data["username"] == "testuser"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert data["is_verified"] is True