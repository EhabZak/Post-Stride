"""
Token encryption utilities for securing OAuth tokens at rest.

This module provides secure encryption/decryption functionality for storing
OAuth access and refresh tokens in the database.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class TokenEncryption:
    """
    Handles encryption and decryption of OAuth tokens using Fernet symmetric encryption.
    
    Uses PBKDF2 key derivation with a password and salt for key generation.
    The salt is stored with the encrypted data for secure decryption.
    """
    
    def __init__(self):
        """Initialize the encryption handler."""
        self._fernet = None
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Set up the Fernet encryption instance."""
        try:
            # Get encryption key from environment
            encryption_password = os.environ.get('TOKEN_ENCRYPTION_PASSWORD')
            if not encryption_password:
                raise ValueError("TOKEN_ENCRYPTION_PASSWORD environment variable is required")
            
            # Generate salt from environment or use a default
            salt = os.environ.get('TOKEN_ENCRYPTION_SALT', 'default_salt_change_in_production')
            
            # Convert password and salt to bytes
            password = encryption_password.encode()
            salt = salt.encode()
            
            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Create Fernet instance
            self._fernet = Fernet(key)
            
        except Exception as e:
            logger.error(f"Failed to setup token encryption: {e}")
            raise
    
    def encrypt_token(self, token):
        """
        Encrypt a token for secure storage.
        
        Args:
            token (str): The plaintext token to encrypt
            
        Returns:
            str: Base64 encoded encrypted token, or None if token is None/empty
        """
        if not token:
            return None
            
        try:
            # Convert token to bytes and encrypt
            token_bytes = token.encode('utf-8')
            encrypted_bytes = self._fernet.encrypt(token_bytes)
            
            # Return base64 encoded string for database storage
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}")
            raise
    
    def decrypt_token(self, encrypted_token):
        """
        Decrypt a token from secure storage.
        
        Args:
            encrypted_token (str): The base64 encoded encrypted token
            
        Returns:
            str: The decrypted plaintext token, or None if encrypted_token is None/empty
        """
        if not encrypted_token:
            return None
            
        try:
            # Decode base64 and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Return decrypted token as string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            raise
    
    def mask_token(self, token, visible_chars=4):
        """
        Mask a token for logging purposes (show only first and last few characters).
        
        Args:
            token (str): The token to mask
            visible_chars (int): Number of characters to show at start and end
            
        Returns:
            str: Masked token for safe logging
        """
        if not token or len(token) <= visible_chars * 2:
            return "***masked***"
        
        return f"{token[:visible_chars]}...{token[-visible_chars:]}"

# Global instance for use throughout the application
token_encryption = None

def _get_encryption_instance():
    """Get or create the encryption instance lazily."""
    global token_encryption
    if token_encryption is None:
        try:
            token_encryption = TokenEncryption()
        except ValueError as e:
            print(f"Warning: Token encryption not available: {e}")
            token_encryption = None
    return token_encryption

def encrypt_token(token):
    """Convenience function to encrypt a token."""
    instance = _get_encryption_instance()
    if instance is None:
        raise RuntimeError("Token encryption not initialized. Check environment variables.")
    return instance.encrypt_token(token)

def decrypt_token(encrypted_token):
    """Convenience function to decrypt a token."""
    instance = _get_encryption_instance()
    if instance is None:
        raise RuntimeError("Token encryption not initialized. Check environment variables.")
    return instance.decrypt_token(encrypted_token)

def mask_token(token, visible_chars=4):
    """Convenience function to mask a token for logging."""
    instance = _get_encryption_instance()
    if instance is None:
        return "***encryption_not_available***"
    return instance.mask_token(token, visible_chars)
