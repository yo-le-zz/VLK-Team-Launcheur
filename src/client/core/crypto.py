"""VLK Launcher — Crypto utilities for secure secret storage
Uses PBKDF2 for key derivation and Fernet for encryption.
"""
import os
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


class CryptoManager:
    """Manages encryption/decryption with password-derived keys."""
    
    def __init__(self, password: str, salt: Optional[bytes] = None):
        """
        Initialize crypto manager with a password.
        
        Args:
            password: User password for key derivation
            salt: Optional salt bytes. If None, generates random salt.
        """
        self.password = password.encode() if isinstance(password, str) else password
        self.salt = salt if salt else os.urandom(16)
        self._key = self._derive_key()
        self._fernet = Fernet(self._key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,  # High iteration count for security
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        if not data:
            return ""
        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not encrypted_data:
            return ""
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception:
            return ""
    
    def get_salt(self) -> str:
        """Get salt as base64 string for storage."""
        return base64.urlsafe_b64encode(self.salt).decode()
    
    @classmethod
    def from_password_and_salt(cls, password: str, salt_b64: str) -> 'CryptoManager':
        """Create CryptoManager from password and base64-encoded salt."""
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        return cls(password, salt)


def hash_password(password: str) -> str:
    """Hash password using SHA-256 for quick verification (not for storage)."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_secure_token() -> str:
    """Generate a cryptographically secure random token."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()
