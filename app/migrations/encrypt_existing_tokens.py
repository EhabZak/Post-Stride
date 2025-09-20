"""
Data migration script to encrypt existing tokens in the database.

This script should be run after the encryption utilities are in place
to encrypt any existing plaintext tokens in the user_platforms table.

Usage:
    python -m app.migrations.encrypt_existing_tokens
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.encryption import token_encryption

def migrate_existing_tokens():
    """Encrypt existing plaintext tokens in the database."""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/dev.db')
    
    # Create engine and session
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user_platforms table exists and has data
        result = session.execute(text("""
            SELECT COUNT(*) as count FROM user_platforms 
            WHERE access_token IS NOT NULL OR refresh_token IS NOT NULL
        """)).fetchone()
        
        if result.count == 0:
            print("No existing tokens found to encrypt.")
            return
        
        print(f"Found {result.count} records with tokens to encrypt...")
        
        # Get all records with tokens
        records = session.execute(text("""
            SELECT id, access_token, refresh_token 
            FROM user_platforms 
            WHERE access_token IS NOT NULL OR refresh_token IS NOT NULL
        """)).fetchall()
        
        updated_count = 0
        
        for record in records:
            record_id, access_token, refresh_token = record
            
            # Check if tokens are already encrypted (they would be base64 encoded)
            # Simple heuristic: encrypted tokens are much longer and contain base64 chars
            needs_encryption = False
            
            if access_token and not is_likely_encrypted(access_token):
                needs_encryption = True
            if refresh_token and not is_likely_encrypted(refresh_token):
                needs_encryption = True
            
            if needs_encryption:
                # Encrypt the tokens
                encrypted_access = token_encryption.encrypt_token(access_token) if access_token else None
                encrypted_refresh = token_encryption.encrypt_token(refresh_token) if refresh_token else None
                
                # Update the record
                session.execute(text("""
                    UPDATE user_platforms 
                    SET access_token = :access_token, refresh_token = :refresh_token 
                    WHERE id = :id
                """), {
                    'access_token': encrypted_access,
                    'refresh_token': encrypted_refresh,
                    'id': record_id
                })
                
                updated_count += 1
                print(f"Encrypted tokens for record {record_id}")
        
        session.commit()
        print(f"Successfully encrypted {updated_count} token records.")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        session.close()

def is_likely_encrypted(token):
    """
    Simple heuristic to determine if a token is already encrypted.
    
    Encrypted tokens are base64 encoded and much longer than typical OAuth tokens.
    """
    if not token:
        return True
    
    # OAuth tokens are typically 50-200 characters
    # Encrypted tokens are typically 200+ characters and contain base64 characters
    if len(token) < 100:
        return False
    
    # Check for base64-like characters (A-Z, a-z, 0-9, +, /, =)
    base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    if all(c in base64_chars for c in token):
        return True
    
    return False

if __name__ == "__main__":
    migrate_existing_tokens()
