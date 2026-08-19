"""
Domain service for authentication business logic.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib
import secrets

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.exceptions import (
    DomainValidationError,
    AuthenticationFailedError,
    AccountLockedError,
    EmailNotVerifiedError,
)
from src.shared.constants import UserRole


class AuthenticationService:
    """
    Domain service for authentication-related business logic.
    Framework-agnostic authentication rules.
    """
    
    # Configuration
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24
    EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 48
    
    def __init__(self, user_repository, password_hasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
    
    async def authenticate(
        self,
        email_or_username: str,
        password: str,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user with email/username and password.
        Returns (user, error_message).
        """
        # Find user
        user = await self._find_user_by_email_or_username(email_or_username)
        
        if not user:
            return None, "Invalid credentials"
        
        # Check if account is locked
        if await self._is_account_locked(user):
            unlock_time = await self._get_unlock_time(user)
            raise AccountLockedError(
                str(user.id),
                "Too many failed attempts",
                unlock_time.isoformat() if unlock_time else None,
            )
        
        # Check if account is active
        if not user.is_active:
            return None, "Account is deactivated"
        
        # Verify password
        if not self.password_hasher.verify(password, user.hashed_password):
            await self._record_failed_attempt(user)
            return None, "Invalid credentials"
        
        # Check email verification if required
        if self._require_email_verification() and not user.is_verified:
            raise EmailNotVerifiedError(str(user.email))
        
        # Successful authentication
        await self._record_successful_login(user)
        
        return user, None
    
    async def _find_user_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Find user by email or username."""
        if "@" in identifier:
            try:
                email = Email(identifier)
                return await self.user_repository.get_by_email(str(email))
            except DomainValidationError:
                pass
        
        return await self.user_repository.get_by_username(identifier)
    
    async def _is_account_locked(self, user: User) -> bool:
        """Check if account is locked due to failed attempts."""
        failed_attempts = user.preferences.get("failed_login_attempts", 0)
        if failed_attempts >= self.MAX_LOGIN_ATTEMPTS:
            last_attempt = user.preferences.get("last_failed_attempt")
            if last_attempt:
                last_attempt_time = datetime.fromisoformat(last_attempt)
                lockout_until = last_attempt_time + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                if datetime.utcnow() < lockout_until:
                    return True
                else:
                    # Reset failed attempts after lockout period
                    await self._reset_failed_attempts(user)
        return False
    
    async def _get_unlock_time(self, user: User) -> Optional[datetime]:
        """Get time when account will be unlocked."""
        last_attempt = user.preferences.get("last_failed_attempt")
        if last_attempt:
            last_attempt_time = datetime.fromisoformat(last_attempt)
            return last_attempt_time + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
        return None
    
    async def _record_failed_attempt(self, user: User) -> None:
        """Record a failed login attempt."""
        failed_attempts = user.preferences.get("failed_login_attempts", 0) + 1
        user.update_preferences({
            "failed_login_attempts": failed_attempts,
            "last_failed_attempt": datetime.utcnow().isoformat(),
        })
        await self.user_repository.update(user)
    
    async def _reset_failed_attempts(self, user: User) -> None:
        """Reset failed login attempts."""
        user.update_preferences({
            "failed_login_attempts": 0,
            "last_failed_attempt": None,
        })
        await self.user_repository.update(user)
    
    async def _record_successful_login(self, user: User) -> None:
        """Record a successful login."""
        await self._reset_failed_attempts(user)
        user.record_login()
        await self.user_repository.update_last_login(user.id)
    
    def _require_email_verification(self) -> bool:
        """Check if email verification is required."""
        # This could be configurable
        return False  # Set to True to require email verification
    
    def validate_password_strength(self, password: str) -> Tuple[bool, list]:
        """
        Validate password strength.
        Returns (is_valid, list_of_issues).
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters")
        
        if len(password) > 128:
            issues.append("Password must be at most 128 characters")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = {"password", "12345678", "qwerty123", "admin123"}
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        return len(issues) == 0, issues
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storage."""
        return self.password_hasher.hash(password)
    
    def generate_password_reset_token(self, user: User) -> str:
        """Generate a password reset token."""
        token_data = f"{user.id}:{user.email}:{datetime.utcnow().timestamp()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        return token
    
    def generate_email_verification_token(self, user: User) -> str:
        """Generate an email verification token."""
        token_data = f"{user.id}:{user.email}:verify:{datetime.utcnow().timestamp()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        return token
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return f"eap_{secrets.token_urlsafe(32)}"
    
    async def can_register(
        self,
        email: str,
        username: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a user can register with given email and username.
        Returns (can_register, error_message).
        """
        # Check email
        try:
            email_vo = Email(email)
        except DomainValidationError as e:
            return False, str(e)
        
        if await self.user_repository.email_exists(str(email_vo)):
            return False, "Email is already registered"
        
        # Check if email is disposable
        if email_vo.is_disposable:
            return False, "Disposable email addresses are not allowed"
        
        # Check username
        if await self.user_repository.username_exists(username):
            return False, "Username is already taken"
        
        return True, None
    
    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user.
        Returns (user, error_message).
        """
        # Validate password
        is_valid, issues = self.validate_password_strength(password)
        if not is_valid:
            return None, "; ".join(issues)
        
        # Check if can register
        can_register, error = await self.can_register(email, username)
        if not can_register:
            return None, error
        
        # Create user
        try:
            email_vo = Email(email)
            hashed_password = self.hash_password(password)
            
            user = User(
                email=email_vo,
                username=username,
                hashed_password=hashed_password,
                full_name=full_name,
                role=UserRole.USER,
            )
            
            created_user = await self.user_repository.add(user)
            return created_user, None
            
        except DomainValidationError as e:
            return None, str(e)