"""
Password hashing and verification using bcrypt.
"""
import logging
import hashlib
import hmac
import secrets
from typing import Tuple

logger = logging.getLogger(__name__)


class PasswordHasher:
    """
    Secure password hashing using bcrypt with additional pepper.
    """
    
    def __init__(self, pepper: str = ""):
        self.pepper = pepper
        self._bcrypt = None
        self._init_bcrypt()
    
    def _init_bcrypt(self):
        """Initialize bcrypt with fallback."""
        try:
            import bcrypt
            self._bcrypt = bcrypt
        except ImportError:
            logger.warning("bcrypt not installed, using fallback PBKDF2")
            self._bcrypt = None
    
    def hash(self, password: str) -> str:
        """
        Hash a password using bcrypt (or PBKDF2 fallback).
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Apply pepper if configured
        peppered = self._apply_pepper(password)
        
        if self._bcrypt:
            # Use bcrypt
            salt = self._bcrypt.gensalt(rounds=12)
            hashed = self._bcrypt.hashpw(peppered.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        else:
            # Fallback to PBKDF2
            return self._hash_pbkdf2(peppered)
    
    def verify(self, password: str, hashed: str) -> bool:
        """
        Verify a password against a hash.
        """
        if not password or not hashed:
            return False
        
        peppered = self._apply_pepper(password)
        
        if self._bcrypt and hashed.startswith("$2"):
            # bcrypt hash
            try:
                return self._bcrypt.checkpw(
                    peppered.encode('utf-8'),
                    hashed.encode('utf-8'),
                )
            except Exception as e:
                logger.error(f"bcrypt verification error: {e}")
                return False
        else:
            # PBKDF2 fallback
            return self._verify_pbkdf2(peppered, hashed)
    
    def _apply_pepper(self, password: str) -> str:
        """Apply pepper to password."""
        if self.pepper:
            return hmac.new(
                self.pepper.encode('utf-8'),
                password.encode('utf-8'),
                hashlib.sha256,
            ).hexdigest()
        return password
    
    def _hash_pbkdf2(self, password: str) -> str:
        """
        PBKDF2 fallback hashing.
        Format: pbkdf2:sha256:iterations$salt$hash
        """
        import hashlib
        import base64
        
        iterations = 600000
        salt = secrets.token_bytes(16)
        
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations,
        )
        
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        hash_b64 = base64.b64encode(hash_bytes).decode('utf-8')
        
        return f"pbkdf2:sha256:{iterations}${salt_b64}${hash_b64}"
    
    def _verify_pbkdf2(self, password: str, hashed: str) -> bool:
        """
        Verify PBKDF2 hash.
        """
        import hashlib
        import base64
        
        try:
            parts = hashed.split('$')
            if len(parts) != 3:
                return False
            
            algo_part, salt_b64, hash_b64 = parts
            
            # Parse algorithm info
            algo_parts = algo_part.split(':')
            if len(algo_parts) != 3 or algo_parts[0] != "pbkdf2":
                return False
            
            digest = algo_parts[1]
            iterations = int(algo_parts[2])
            
            salt = base64.b64decode(salt_b64)
            expected_hash = base64.b64decode(hash_b64)
            
            actual_hash = hashlib.pbkdf2_hmac(
                digest,
                password.encode('utf-8'),
                salt,
                iterations,
            )
            
            return hmac.compare_digest(actual_hash, expected_hash)
            
        except Exception as e:
            logger.error(f"PBKDF2 verification error: {e}")
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Check if a hash needs to be rehashed (e.g., algorithm updated).
        """
        if self._bcrypt and not hashed.startswith("$2"):
            return True
        
        # Check bcrypt rounds
        if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
            try:
                rounds = int(hashed.split('$')[2])
                return rounds < 12
            except (IndexError, ValueError):
                pass
        
        return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.
        """
        return secrets.token_urlsafe(length)
    
    def generate_numeric_code(self, length: int = 6) -> str:
        """
        Generate a numeric verification code.
        """
        import random
        return ''.join(str(random.randint(0, 9)) for _ in range(length))
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """
        Constant-time string comparison to prevent timing attacks.
        """
        return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key using SHA-256.
        """
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """
        Verify an API key against stored hash.
        """
        return self.hash_api_key(api_key) == stored_hash


class PasswordValidator:
    """
    Password strength validation.
    """
    
    # Common weak passwords
    COMMON_PASSWORDS = {
        "password", "12345678", "qwerty123", "admin123", "letmein",
        "welcome", "monkey", "dragon", "master", "hello",
        "freedom", "whatever", "qazwsx", "trustno1", "password1",
    }
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, list[str]]:
        """
        Validate password strength.
        Returns (is_valid, issues).
        """
        issues = []
        
        if not password:
            return False, ["Password cannot be empty"]
        
        # Length
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            issues.append("Password must be at most 128 characters long")
        
        # Character variety
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
            issues.append("Password must contain at least one special character")
        
        # Common passwords
        if password.lower() in cls.COMMON_PASSWORDS:
            issues.append("Password is too common")
        
        # Sequential characters
        if cls._has_sequential_chars(password):
            issues.append("Password contains sequential characters (e.g., 'abc', '123')")
        
        # Repeated characters
        if cls._has_repeated_chars(password):
            issues.append("Password contains too many repeated characters")
        
        return len(issues) == 0, issues
    
    @classmethod
    def _has_sequential_chars(cls, password: str) -> bool:
        """Check for sequential characters."""
        password_lower = password.lower()
        
        for i in range(len(password_lower) - 2):
            c1, c2, c3 = password_lower[i], password_lower[i+1], password_lower[i+2]
            
            # Check alphabet sequence
            if ord(c1) + 1 == ord(c2) and ord(c2) + 1 == ord(c3):
                return True
            
            # Check numeric sequence
            if c1.isdigit() and c2.isdigit() and c3.isdigit():
                if int(c1) + 1 == int(c2) and int(c2) + 1 == int(c3):
                    return True
        
        return False
    
    @classmethod
    def _has_repeated_chars(cls, password: str) -> bool:
        """Check for too many repeated characters."""
        from collections import Counter
        
        counts = Counter(password.lower())
        max_count = max(counts.values())
        
        return max_count > len(password) * 0.5
    
    @classmethod
    def get_strength_score(cls, password: str) -> int:
        """
        Get password strength score (0-100).
        """
        if not password:
            return 0
        
        score = 0
        
        # Length contribution (up to 30 points)
        score += min(len(password) * 2, 30)
        
        # Character variety (up to 40 points)
        if any(c.isupper() for c in password):
            score += 10
        if any(c.islower() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password):
            score += 10
        
        # Penalties
        if password.lower() in cls.COMMON_PASSWORDS:
            score -= 30
        if cls._has_sequential_chars(password):
            score -= 15
        if cls._has_repeated_chars(password):
            score -= 15
        
        return max(0, min(100, score))
    
    @classmethod
    def get_strength_label(cls, password: str) -> str:
        """
        Get password strength label.
        """
        score = cls.get_strength_score(password)
        
        if score < 30:
            return "Very Weak"
        elif score < 50:
            return "Weak"
        elif score < 70:
            return "Fair"
        elif score < 85:
            return "Strong"
        else:
            return "Very Strong"