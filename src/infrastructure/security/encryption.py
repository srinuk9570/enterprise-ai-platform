"""
Encryption service for sensitive data.
"""
import logging
import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from src.shared.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or self._derive_key(settings.SECRET_KEY)
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, secret: str) -> bytes:
        """
        Derive encryption key from secret using PBKDF2.
        """
        salt = b"enterprise_ai_platform_salt"  # In production, use random salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend(),
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key
    
    @classmethod
    def generate_key(cls) -> bytes:
        """
        Generate a new Fernet key.
        """
        return Fernet.generate_key()
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string.
        """
        if not data:
            return data
        
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string.
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        """
        import copy
        result = copy.deepcopy(data)
        
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        
        return result
    
    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        """
        import copy
        result = copy.deepcopy(data)
        
        for field in fields:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(result[field])
                except Exception:
                    # Field might not be encrypted
                    pass
        
        return result
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Encrypt a file.
        """
        output_path = output_path or f"{file_path}.enc"
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        encrypted = self.fernet.encrypt(file_data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        return output_path
    
    def decrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Decrypt a file.
        """
        output_path = output_path or file_path.replace('.enc', '')
        
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted = self.fernet.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return output_path
    
    def hash_sha256(self, data: str) -> str:
        """
        Create SHA-256 hash of data.
        """
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
    
    def hash_md5(self, data: str) -> str:
        """
        Create MD5 hash of data (for non-security purposes).
        """
        import hashlib
        return hashlib.md5(data.encode()).hexdigest()