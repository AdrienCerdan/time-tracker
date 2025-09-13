#!/usr/bin/env python3
"""
Debug script to test password authentication
"""

import hashlib

def test_password_hash():
    """Test password hashing to debug authentication issues"""

    print("🔧 Password Hash Debug Tool")
    print("=" * 40)

    # Test the default password
    default_password = "admin123"
    default_hash = hashlib.sha256(default_password.encode()).hexdigest()

    print(f"Default password: {default_password}")
    print(f"Default hash: {default_hash}")
    print()

    # Test a custom password
    custom_password = input("Enter your custom password: ")
    custom_hash = hashlib.sha256(custom_password.encode()).hexdigest()

    print(f"Custom password: {custom_password}")
    print(f"Custom hash: {custom_hash}")
    print()

    print("Add this to your secrets.toml:")
    print(f'app_password_hash = "{custom_hash}"')
    print()

    # Test comparison
    test_input = input("Enter password to test: ")
    test_hash = hashlib.sha256(test_input.encode()).hexdigest()

    if test_hash == custom_hash:
        print("✅ Password match!")
    else:
        print("❌ Password doesn't match")
        print(f"Expected: {custom_hash}")
        print(f"Got: {test_hash}")

if __name__ == "__main__":
    test_password_hash()
