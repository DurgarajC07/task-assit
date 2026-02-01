"""Encryption service for sensitive data.

Provides Fernet symmetric encryption for:
- API keys and credentials
- Sensitive configuration
- Personal identifiable information (PII)
"""
from cryptography.fernet import Fernet
from typing import Optional
import base64
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""
    
    def __init__(self, encryption_key: str):
        """Initialize encryption service.
        
        Args:
            encryption_key: Base64-encoded Fernet key from settings
        """
        try:
            # Ensure key is properly formatted
            if not encryption_key:
                raise ValueError("Encryption key cannot be empty")
            
            # Convert to bytes if string
            if isinstance(encryption_key, str):
                key_bytes = encryption_key.encode()
            else:
                key_bytes = encryption_key
            
            # Ensure it's base64 encoded and the right length (32 bytes)
            try:
                decoded = base64.urlsafe_b64decode(key_bytes)
                if len(decoded) != 32:
                    # Generate proper key if invalid
                    logger.warning("Invalid encryption key length, generating new key")
                    key_bytes = Fernet.generate_key()
            except Exception:
                # If not base64, create a proper key
                logger.warning("Invalid encryption key format, generating new key")
                key_bytes = Fernet.generate_key()
            
            self.cipher = Fernet(key_bytes)
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise
    
    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted bytes
            
        Raises:
            ValueError: If plaintext is empty
            Exception: If encryption fails
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        try:
            plaintext_bytes = plaintext.encode('utf-8')
            encrypted = self.cipher.encrypt(plaintext_bytes)
            logger.debug("Data encrypted successfully")
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt ciphertext bytes.
        
        Args:
            ciphertext: Encrypted bytes
            
        Returns:
            Decrypted string
            
        Raises:
            ValueError: If ciphertext is empty
            Exception: If decryption fails
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty data")
        
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext)
            decrypted = decrypted_bytes.decode('utf-8')
            logger.debug("Data decrypted successfully")
            return decrypted
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: dict) -> bytes:
        """Encrypt dictionary as JSON.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted bytes
        """
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: bytes) -> dict:
        """Decrypt ciphertext to dictionary.
        
        Args:
            ciphertext: Encrypted bytes
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get or create encryption service singleton.
    
    Returns:
        EncryptionService instance
    """
    global _encryption_service
    
    if _encryption_service is None:
        from app.config import settings
        _encryption_service = EncryptionService(settings.encryption_key)
    
    return _encryption_service


def encrypt_credentials(credentials: dict) -> bytes:
    """Convenience function to encrypt credentials dictionary.
    
    Args:
        credentials: Dictionary of credentials to encrypt
        
    Returns:
        Encrypted bytes
    """
    service = get_encryption_service()
    return service.encrypt_dict(credentials)


def decrypt_credentials(encrypted: bytes) -> dict:
    """Convenience function to decrypt credentials.
    
    Args:
        encrypted: Encrypted credentials bytes
        
    Returns:
        Decrypted credentials dictionary
    """
    service = get_encryption_service()
    return service.decrypt_dict(encrypted)
