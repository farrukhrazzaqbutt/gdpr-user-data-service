"""
Test encryption/decryption functionality
"""
import pytest
from app.crypto import encrypt_pii, decrypt_pii, crypto_service


class TestCryptoService:
    def test_encrypt_decrypt_round_trip(self, sample_pii_data):
        """Test that encrypting and decrypting PII data works correctly"""
        # Encrypt the data
        encrypted = encrypt_pii(sample_pii_data)
        
        # Verify it's encrypted (not the same as original)
        assert encrypted != sample_pii_data
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 0
        
        # Decrypt the data
        decrypted = decrypt_pii(encrypted)
        
        # Verify it matches the original
        assert decrypted == sample_pii_data
    
    def test_encrypt_different_data_produces_different_results(self, sample_pii_data):
        """Test that encrypting the same data twice produces different encrypted results"""
        encrypted1 = encrypt_pii(sample_pii_data)
        encrypted2 = encrypt_pii(sample_pii_data)
        
        # Should be different due to random data keys
        assert encrypted1 != encrypted2
    
    def test_decrypt_tampered_data_fails(self, sample_pii_data):
        """Test that tampering with encrypted data causes decryption to fail"""
        encrypted = encrypt_pii(sample_pii_data)
        
        # Tamper with the encrypted data
        tampered = encrypted[:-1] + b'X'
        
        # Decryption should fail
        with pytest.raises(Exception):
            decrypt_pii(tampered)
    
    def test_encrypt_empty_dict(self):
        """Test encrypting empty dictionary"""
        empty_data = {}
        encrypted = encrypt_pii(empty_data)
        decrypted = decrypt_pii(encrypted)
        assert decrypted == empty_data
    
    def test_encrypt_nested_data(self):
        """Test encrypting nested data structures"""
        nested_data = {
            "name": "John Doe",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "zip": "12345"
            },
            "phones": ["+1234567890", "+0987654321"]
        }
        
        encrypted = encrypt_pii(nested_data)
        decrypted = decrypt_pii(encrypted)
        assert decrypted == nested_data
    
    def test_is_encrypted_data(self):
        """Test the is_encrypted_data helper function"""
        # Test with encrypted data
        encrypted = encrypt_pii({"test": "data"})
        assert crypto_service.is_encrypted_data(encrypted) is True
        
        # Test with too short data
        short_data = b"short"
        assert crypto_service.is_encrypted_data(short_data) is False
        
        # Test with empty data
        empty_data = b""
        assert crypto_service.is_encrypted_data(empty_data) is False
