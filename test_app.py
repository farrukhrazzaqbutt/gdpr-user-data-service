#!/usr/bin/env python3
"""
Simple test script to verify the application works
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.crypto import encrypt_pii, decrypt_pii
from app.config import settings

def test_crypto():
    """Test encryption/decryption"""
    print("Testing encryption/decryption...")
    
    # Test data
    test_data = {
        "name": "John Doe",
        "phone": "+1234567890",
        "address": "123 Main St, City, State 12345"
    }
    
    # Encrypt
    encrypted = encrypt_pii(test_data)
    print(f"✓ Encryption successful, length: {len(encrypted)} bytes")
    
    # Decrypt
    decrypted = decrypt_pii(encrypted)
    print(f"✓ Decryption successful")
    
    # Verify
    assert decrypted == test_data, "Decrypted data doesn't match original"
    print("✓ Data integrity verified")
    
    print("✅ Crypto tests passed!")

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    assert settings.database_url is not None
    assert settings.secret_key is not None
    assert settings.master_key is not None
    
    print("✅ Configuration tests passed!")

def main():
    """Run all tests"""
    print("Running application tests...\n")
    
    try:
        test_config()
        print()
        test_crypto()
        print()
        print("🎉 All tests passed! The application is ready to use.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
