"""
JWT token handling for authentication and authorization.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from jose import jwt

from src.shared.config import settings
from src.shared.constants import UserRole

logger = logging.getLogger(__name__)


class JWTHandler:
    """
    Handler for JWT token creation, validation, and refresh.
    """
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        
        # Token blacklist (in production, use Redis)
        self._blacklist: set[str] = set()
    
    def create_access_token(
        self,
        user_id: UUID,
        username: str,
        role: UserRole,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new JWT access token.
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role.value,
            "email": email,
            "type": "access",
            "iat": now,
            "exp": expire,
            "iss": "enterprise-ai-platform",
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(
        self,
        user_id: UUID,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Create a refresh token for obtaining new access tokens.
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "iss": "enterprise-ai-platform",
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_token_pair(
        self,
        user_id: UUID,
        username: str,
        role: UserRole,
        email: str,
        session_id: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Create both access and refresh tokens.
        """
        import secrets
        
        if not session_id:
            session_id = secrets.token_hex(16)
        
        access_token = self.create_access_token(
            user_id=user_id,
            username=username,
            role=role,
            email=email,
            additional_claims=additional_claims,
        )
        
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            session_id=session_id,
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "session_id": session_id,
            "expires_in": self.access_token_expire_minutes * 60,
        }
    
    def decode_token(self, token: str, verify_exp: bool = True) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        Returns payload if valid, None otherwise.
        """
        # Check blacklist
        if token in self._blacklist:
            logger.warning("Token is blacklisted")
            return None
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": verify_exp},
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return None
    
    def validate_access_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate an access token.
        Returns (is_valid, payload, error_message).
        """
        payload = self.decode_token(token)
        
        if not payload:
            return False, None, "Invalid or expired token"
        
        if payload.get("type") != "access":
            return False, None, "Invalid token type"
        
        return True, payload, None
    
    def validate_refresh_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a refresh token.
        Returns (is_valid, payload, error_message).
        """
        payload = self.decode_token(token)
        
        if not payload:
            return False, None, "Invalid or expired refresh token"
        
        if payload.get("type") != "refresh":
            return False, None, "Invalid token type"
        
        return True, payload, None
    
    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """
        Create a new access token using a valid refresh token.
        Returns (token_pair, error_message).
        """
        is_valid, payload, error = self.validate_refresh_token(refresh_token)
        
        if not is_valid:
            return None, error
        
        user_id = UUID(payload["sub"])
        session_id = payload.get("session_id")
        
        # Note: In production, you'd fetch user details from database here
        # For now, we need user info passed separately or stored in refresh token
        
        return None, "User details required for refresh"
    
    def blacklist_token(self, token: str) -> None:
        """
        Add a token to the blacklist.
        """
        self._blacklist.add(token)
        logger.debug("Token blacklisted")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        """
        return token in self._blacklist
    
    def get_user_id_from_token(self, token: str) -> Optional[UUID]:
        """
        Extract user ID from token without full validation.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            return UUID(payload["sub"])
        except Exception:
            return None
    
    def get_role_from_token(self, token: str) -> Optional[str]:
        """
        Extract role from token without full validation.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            return payload.get("role")
        except Exception:
            return None
    
    def create_api_token(
        self,
        user_id: UUID,
        scopes: list[str],
        expires_in_days: Optional[int] = None,
    ) -> str:
        """
        Create a long-lived API token for programmatic access.
        """
        now = datetime.utcnow()
        
        if expires_in_days:
            expire = now + timedelta(days=expires_in_days)
        else:
            expire = now + timedelta(days=365)  # 1 year default
        
        payload = {
            "sub": str(user_id),
            "type": "api",
            "scopes": scopes,
            "iat": now,
            "exp": expire,
            "iss": "enterprise-ai-platform",
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_email_verification_token(self, user_id: UUID, email: str) -> str:
        """
        Create a token for email verification.
        """
        now = datetime.utcnow()
        expire = now + timedelta(hours=48)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "email_verification",
            "iat": now,
            "exp": expire,
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_password_reset_token(self, user_id: UUID) -> str:
        """
        Create a token for password reset.
        """
        now = datetime.utcnow()
        expire = now + timedelta(hours=1)
        
        payload = {
            "sub": str(user_id),
            "type": "password_reset",
            "iat": now,
            "exp": expire,
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_special_token(
        self,
        token: str,
        expected_type: str,
    ) -> Tuple[bool, Optional[UUID], Optional[str]]:
        """
        Verify a special purpose token (email verification, password reset).
        Returns (is_valid, user_id, error_message).
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            if payload.get("type") != expected_type:
                return False, None, f"Invalid token type, expected {expected_type}"
            
            user_id = UUID(payload["sub"])
            return True, user_id, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {e}"
        except Exception as e:
            return False, None, f"Error verifying token: {e}"
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get expiration time of a token.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
        except Exception:
            pass
        
        return None
    
    def get_token_remaining_time(self, token: str) -> Optional[int]:
        """
        Get remaining validity time in seconds.
        """
        expiry = self.get_token_expiry(token)
        if expiry:
            remaining = (expiry - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
        return None