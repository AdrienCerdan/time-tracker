#!/usr/bin/env python3
"""
Password Hash Generator for Streamlit Time Tracker

This script generates a secure SHA-256 hash of your password
for use in Streamlit secrets.
"""

import hashlib
import getpass

def generate_password_hash():
    """Generate password hash for Streamlit secrets"""

    print("🔐 Password Hash Generator for Time Tracker")
    print("=" * 50)
    print("This will generate a secure hash of your password for use in Streamlit secrets.")
    print()

    # Get password securely (won't show on screen)
    password = getpass.getpass("Enter your password: ")

    if len(password) < 8:
        print("⚠️  Warning: Password is less than 8 characters. Consider using a stronger password.")

    # Confirm password
    password_confirm = getpass.getpass("Confirm your password: ")

    if password != password_confirm:
        print("❌ Passwords don't match. Please try again.")
        return

    # Generate hash
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    print("✅ Password hash generated successfully!")
    print()
    print("Add this line to your .streamlit/secrets.toml file:")
    print("-" * 50)
    print(f'app_password_hash = "{password_hash}"')
    print("-" * 50)
    print()
    print("Complete secrets.toml example:")
    print("""
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
# ... your other Google Cloud credentials ...

# App authentication
app_password_hash = """" + password_hash + """"
    """)

    print("🔒 Keep your password secure and don't share the hash with others!")

if __name__ == "__main__":
    generate_password_hash()
