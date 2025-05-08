#!/usr/bin/env python3
"""
Database Security Setup Script

This script sets up secure database access for the BibleScholarProject:
1. Creates read-only and write user roles
2. Sets appropriate permissions for each role
3. Updates .env file with new credentials

Usage:
    python scripts/setup_db_security.py

Requirements:
    - Admin access to the PostgreSQL database
    - Existing .env file in project root
"""

import os
import sys
import getpass
import logging
from pathlib import Path
from dotenv import load_dotenv, set_key
sys.path.append(str(Path(__file__).parent.parent))
from src.database.secure_connection import setup_database_roles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_secure_password(length=16):
    """Generate a secure random password."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def update_env_file(read_user, read_pass, write_user, write_pass):
    """Update the .env file with the new database credentials."""
    env_file = Path('.env')
    
    if not env_file.exists():
        logger.error(".env file not found. Please create one first.")
        return False
    
    # Load current environment
    load_dotenv()
    
    # Update .env file with new variables
    set_key('.env', 'POSTGRES_READ_USER', read_user)
    set_key('.env', 'POSTGRES_READ_PASSWORD', read_pass)
    set_key('.env', 'POSTGRES_WRITE_USER', write_user)
    set_key('.env', 'POSTGRES_WRITE_PASSWORD', write_pass)
    
    logger.info("Updated .env file with new database credentials")
    return True

def main():
    """Main function to set up database security."""
    logger.info("Bible Database Security Setup")
    logger.info("============================")
    logger.info("This script will set up secure database access with read-only and write modes.")
    logger.info("You will need admin access to your PostgreSQL database.")
    
    print("\nDatabase Admin Credentials")
    print("-------------------------")
    admin_username = input("Admin username (default: postgres): ") or "postgres"
    admin_password = getpass.getpass("Admin password: ")
    
    print("\nRead-Only User Setup")
    print("-------------------")
    read_user = input("Read-only username (default: bible_reader): ") or "bible_reader"
    read_pass = input("Read-only password (leave empty to generate): ") or generate_secure_password(12)
    
    print("\nWrite Access User Setup")
    print("----------------------")
    write_user = input("Write access username (default: bible_writer): ") or "bible_writer"
    write_pass = input("Write access password (leave empty to generate): ") or generate_secure_password(16)
    
    # Update environment variables
    os.environ['POSTGRES_READ_USER'] = read_user
    os.environ['POSTGRES_READ_PASSWORD'] = read_pass
    os.environ['POSTGRES_WRITE_USER'] = write_user
    os.environ['POSTGRES_WRITE_PASSWORD'] = write_pass
    
    print("\nSetting up database roles and permissions...")
    success = setup_database_roles(admin_username, admin_password)
    
    if success:
        print("\nDatabase roles created successfully!")
        
        # Update .env file
        if update_env_file(read_user, read_pass, write_user, write_pass):
            print("\nCredentials saved to .env file.")
        
        print("\n=== SETUP COMPLETE ===")
        print("\nDatabase security is now configured with:")
        print(f"- READ-ONLY access: {read_user}")
        print(f"- WRITE access: {write_user} (protected with password)")
        print("\nTo use secure connections in your code:")
        print("```python")
        print("from src.database.secure_connection import get_secure_connection")
        print("")
        print("# Read-only access (default)")
        print("conn = get_secure_connection()")
        print("")
        print("# Write access (requires POSTGRES_WRITE_PASSWORD in .env)")
        print("conn = get_secure_connection(mode='write')")
        print("```")
    else:
        print("\nFailed to set up database roles. Check the error logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 