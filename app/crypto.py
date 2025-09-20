"""
GDPR-compliant encryption utilities using envelope encryption.
PII data is encrypted with random data keys, which are then encrypted with a master key.
"""
import json
import secrets
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
from app.config import settings


class CryptoService:
    def __init__(self):
        self.master_key = settings.master_key.encode()
        self.algorithm = settings.encryption_algorithm
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive a key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password)
    
    def _generate_data_key(self) -> bytes:
        """Generate a random data key"""
        return Fernet.generate_key()
    
    def _encrypt_data_key(self, data_key: bytes) -> bytes:
        """Encrypt data key with master key using AES-GCM"""
        salt = secrets.token_bytes(16)
        key = self._derive_key(self.master_key, salt)
        
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        encrypted_key = aesgcm.encrypt(nonce, data_key, None)
        
        # Combine salt + nonce + encrypted_key
        return salt + nonce + encrypted_key
    
    def _decrypt_data_key(self, encrypted_data_key: bytes) -> bytes:
        """Decrypt data key with master key"""
        salt = encrypted_data_key[:16]
        nonce = encrypted_data_key[16:28]
        encrypted_key = encrypted_data_key[28:]
        
        key = self._derive_key(self.master_key, salt)
        aesgcm = AESGCM(key)
        
        return aesgcm.decrypt(nonce, encrypted_key, None)
    
    def encrypt_pii(self, pii_data: Dict[str, Any]) -> bytes:
        """
        Encrypt PII data using envelope encryption.
        
        Args:
            pii_data: Dictionary containing PII information
            
        Returns:
            Encrypted data as bytes (encrypted_data_key + encrypted_pii)
        """
        # Generate random data key
        data_key = self._generate_data_key()
        
        # Encrypt PII data with data key
        fernet = Fernet(data_key)
        pii_json = json.dumps(pii_data, sort_keys=True).encode('utf-8')
        encrypted_pii = fernet.encrypt(pii_json)
        
        # Encrypt data key with master key
        encrypted_data_key = self._encrypt_data_key(data_key)
        
        # Combine encrypted data key and encrypted PII
        return encrypted_data_key + encrypted_pii
    
    def decrypt_pii(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt PII data using envelope encryption.
        
        Args:
            encrypted_data: Encrypted data as bytes
            
        Returns:
            Decrypted PII data as dictionary
        """
        # Split encrypted data key and encrypted PII
        # Data key is 16 (salt) + 12 (nonce) + 16 (encrypted key) = 44 bytes
        encrypted_data_key = encrypted_data[:44]
        encrypted_pii = encrypted_data[44:]
        
        # Decrypt data key
        data_key = self._decrypt_data_key(encrypted_data_key)
        
        # Decrypt PII data
        fernet = Fernet(data_key)
        decrypted_pii_json = fernet.decrypt(encrypted_pii)
        
        return json.loads(decrypted_pii_json.decode('utf-8'))
    
    def is_encrypted_data(self, data: bytes) -> bool:
        """Check if data appears to be encrypted (has minimum expected length)"""
        return len(data) > 44  # Minimum length for encrypted data


# Global crypto service instance
crypto_service = CryptoService()


def encrypt_pii(pii_data: Dict[str, Any]) -> bytes:
    """Convenience function for encrypting PII"""
    return crypto_service.encrypt_pii(pii_data)


def decrypt_pii(encrypted_data: bytes) -> Dict[str, Any]:
    """Convenience function for decrypting PII"""
    return crypto_service.decrypt_pii(encrypted_data)
