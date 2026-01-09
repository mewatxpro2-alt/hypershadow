"""
═══════════════════════════════════════════════════════════════════════════════
BORDER SURVEILLANCE SYSTEM - DATA ENCRYPTION UTILITIES
═══════════════════════════════════════════════════════════════════════════════
Classification: RESTRICTED
Organization: Border Security Force
Module: database/encryption.py
Last Updated: 2026-01-02
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
    Provides encryption utilities for data at rest.
    Uses Fernet symmetric encryption (AES-128-CBC).
    
SECURITY NOTES:
    - Encryption keys should be stored securely
    - Keys should be rotated periodically
    - Never log encrypted data or keys
    
USAGE:
    from database.encryption import DataEncryption
    
    crypto = DataEncryption()
    encrypted = crypto.encrypt("sensitive data")
    decrypted = crypto.decrypt(encrypted)

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import base64
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Union
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import cryptography library
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("WARNING: cryptography library not installed. Using fallback encryption.")

# Configure logging
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA ENCRYPTION CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class DataEncryption:
    """
    Handles encryption and decryption of sensitive data.
    
    Uses Fernet symmetric encryption (AES-128-CBC with HMAC).
    Falls back to XOR encryption if cryptography library is unavailable.
    
    SECURITY NOTE:
        The fallback XOR encryption is NOT secure for production use.
        Always install the cryptography library for proper security.
        
    Example:
        >>> crypto = DataEncryption("my-secret-key")
        >>> encrypted = crypto.encrypt("sensitive data")
        >>> decrypted = crypto.decrypt(encrypted)
        >>> print(decrypted)
        'sensitive data'
    """
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption with a key.
        
        Args:
            key: Encryption key string. If None, uses environment variable
                 BSS_ENCRYPTION_KEY or generates a random key.
                 
        SECURITY NOTE:
            For production, always provide a secure key or set the
            BSS_ENCRYPTION_KEY environment variable.
        """
        # Get key from parameter, environment, or generate
        if key is None:
            key = os.environ.get("BSS_ENCRYPTION_KEY")
        
        if key is None:
            logger.warning(
                "No encryption key provided. Generating random key. "
                "This key will be lost on restart - data will be unrecoverable!"
            )
            key = self.generate_key()
        
        self.key = key
        
        # Initialize Fernet if available
        if CRYPTOGRAPHY_AVAILABLE:
            self.fernet = self._create_fernet(key)
        else:
            self.fernet = None
            logger.warning("Using insecure fallback encryption!")
    
    def _create_fernet(self, key: str) -> Fernet:
        """
        Create a Fernet instance from a password/key string.
        
        Uses PBKDF2 to derive a proper key from the input string.
        
        Args:
            key: Password or key string
            
        Returns:
            Fernet instance
        """
        # Use a fixed salt (in production, this should be stored securely)
        salt = b"border_surveillance_salt_2026"
        
        # Derive a proper key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(derived_key)
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a secure random key.
        
        Returns:
            32-character hexadecimal key string
            
        Example:
            >>> key = DataEncryption.generate_key()
            >>> print(len(key))
            64
        """
        return secrets.token_hex(32)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data.
        
        Args:
            data: String or bytes to encrypt
            
        Returns:
            Base64-encoded encrypted string
            
        Example:
            >>> encrypted = crypto.encrypt("secret message")
            >>> print(encrypted)
            'gAAAAABh...'
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if self.fernet:
            encrypted = self.fernet.encrypt(data)
            return encrypted.decode('utf-8')
        else:
            # Fallback XOR encryption (NOT SECURE - for development only)
            return self._xor_encrypt(data)
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted string
            
        Raises:
            ValueError: If decryption fails (wrong key or corrupted data)
            
        Example:
            >>> decrypted = crypto.decrypt(encrypted)
            >>> print(decrypted)
            'secret message'
        """
        if self.fernet:
            try:
                decrypted = self.fernet.decrypt(encrypted_data.encode('utf-8'))
                return decrypted.decode('utf-8')
            except InvalidToken:
                raise ValueError("Decryption failed: Invalid key or corrupted data")
        else:
            # Fallback XOR decryption
            return self._xor_decrypt(encrypted_data)
    
    def _xor_encrypt(self, data: bytes) -> str:
        """
        Fallback XOR encryption (NOT SECURE).
        
        WARNING: This is only for development/testing without cryptography
        library. Do NOT use in production!
        """
        key_bytes = hashlib.sha256(self.key.encode()).digest()
        encrypted = bytes(
            data[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data))
        )
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _xor_decrypt(self, encrypted_data: str) -> str:
        """
        Fallback XOR decryption.
        """
        data = base64.b64decode(encrypted_data.encode('utf-8'))
        key_bytes = hashlib.sha256(self.key.encode()).digest()
        decrypted = bytes(
            data[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(data))
        )
        return decrypted.decode('utf-8')
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all string values in a dictionary.
        
        Useful for encrypting database records.
        
        Args:
            data: Dictionary with string values
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted
    
    def decrypt_dict(self, data: dict, keys: list) -> dict:
        """
        Decrypt specified keys in a dictionary.
        
        Args:
            data: Dictionary with encrypted values
            keys: List of keys to decrypt
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted = data.copy()
        for key in keys:
            if key in decrypted and isinstance(decrypted[key], str):
                try:
                    decrypted[key] = self.decrypt(decrypted[key])
                except Exception:
                    pass  # Keep original value if decryption fails
        return decrypted
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if data appears to be encrypted.
        
        This is a heuristic check, not foolproof.
        
        Args:
            data: String to check
            
        Returns:
            True if data appears to be encrypted
        """
        if not data:
            return False
        
        # Fernet tokens start with "gAAAAAB"
        if data.startswith("gAAAAAB"):
            return True
        
        # Check if it's valid base64 of reasonable length
        try:
            decoded = base64.b64decode(data)
            # Encrypted data is typically longer and more random
            if len(decoded) > 10:
                # Check entropy
                unique_bytes = len(set(decoded))
                entropy_ratio = unique_bytes / len(decoded)
                return entropy_ratio > 0.3
        except Exception:
            pass
        
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# FILE ENCRYPTION
# ═══════════════════════════════════════════════════════════════════════════════

class FileEncryption:
    """
    Handles encryption/decryption of files.
    
    Example:
        >>> file_crypto = FileEncryption("my-key")
        >>> file_crypto.encrypt_file("sensitive.txt", "sensitive.enc")
        >>> file_crypto.decrypt_file("sensitive.enc", "recovered.txt")
    """
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize file encryption.
        
        Args:
            key: Encryption key string
        """
        self.data_crypto = DataEncryption(key)
    
    def encrypt_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        delete_original: bool = False
    ) -> str:
        """
        Encrypt a file.
        
        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted output (default: input + .enc)
            delete_original: Whether to delete original after encryption
            
        Returns:
            Path to encrypted file
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        if output_path is None:
            output_path = str(input_path) + ".enc"
        
        # Read and encrypt file content
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.data_crypto.encrypt(data)
        
        # Write encrypted data
        with open(output_path, 'w') as f:
            f.write(encrypted)
        
        # Optionally delete original
        if delete_original:
            self._secure_delete(input_path)
        
        logger.info(f"File encrypted: {input_path} -> {output_path}")
        return output_path
    
    def decrypt_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        delete_encrypted: bool = False
    ) -> str:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted output
            delete_encrypted: Whether to delete encrypted file after
            
        Returns:
            Path to decrypted file
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        
        if output_path is None:
            # Remove .enc extension if present
            output_path = str(input_path).replace(".enc", "")
            if output_path == str(input_path):
                output_path = str(input_path) + ".dec"
        
        # Read and decrypt file content
        with open(input_path, 'r') as f:
            encrypted = f.read()
        
        decrypted = self.data_crypto.decrypt(encrypted)
        
        # Write decrypted data
        if isinstance(decrypted, str):
            with open(output_path, 'w') as f:
                f.write(decrypted)
        else:
            with open(output_path, 'wb') as f:
                f.write(decrypted)
        
        # Optionally delete encrypted file
        if delete_encrypted:
            self._secure_delete(input_path)
        
        logger.info(f"File decrypted: {input_path} -> {output_path}")
        return output_path
    
    def _secure_delete(self, path: Path) -> None:
        """
        Securely delete a file by overwriting before deletion.
        
        Args:
            path: Path to file to delete
        """
        if not path.exists():
            return
        
        # Get file size
        size = path.stat().st_size
        
        # Overwrite with random data 3 times
        for _ in range(3):
            with open(path, 'wb') as f:
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
        
        # Delete file
        path.unlink()
        logger.info(f"Securely deleted: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """
    Create a one-way hash of sensitive data.
    
    Useful for storing data that needs to be compared but not decrypted.
    
    Args:
        data: Data to hash
        salt: Optional salt for additional security
        
    Returns:
        Hex-encoded hash string
    """
    if salt:
        data = salt + data
    
    return hashlib.sha256(data.encode()).hexdigest()


def mask_sensitive_data(
    data: str,
    visible_start: int = 2,
    visible_end: int = 2,
    mask_char: str = "*"
) -> str:
    """
    Mask sensitive data for display.
    
    Example:
        >>> mask_sensitive_data("1234567890")
        '12******90'
        >>> mask_sensitive_data("password123")
        'pa*******23'
    """
    if len(data) <= visible_start + visible_end:
        return mask_char * len(data)
    
    start = data[:visible_start]
    end = data[-visible_end:] if visible_end > 0 else ""
    middle = mask_char * (len(data) - visible_start - visible_end)
    
    return start + middle + end


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("BORDER SURVEILLANCE SYSTEM - Encryption Module Test")
    print("=" * 70)
    
    # Test key generation
    print("\n1. Key Generation:")
    key = DataEncryption.generate_key()
    print(f"   Generated key: {key[:20]}...")
    
    # Test encryption/decryption
    print("\n2. Data Encryption:")
    crypto = DataEncryption(key)
    
    test_data = "CLASSIFIED: Border patrol coordinates 31.234°N, 75.456°E"
    print(f"   Original: {test_data}")
    
    encrypted = crypto.encrypt(test_data)
    print(f"   Encrypted: {encrypted[:50]}...")
    
    decrypted = crypto.decrypt(encrypted)
    print(f"   Decrypted: {decrypted}")
    print(f"   Match: {'✓ PASS' if decrypted == test_data else '✗ FAIL'}")
    
    # Test dictionary encryption
    print("\n3. Dictionary Encryption:")
    test_dict = {
        "username": "admin",
        "password": "secret123",
        "role": "supervisor"
    }
    encrypted_dict = crypto.encrypt_dict(test_dict)
    print(f"   Original password: {test_dict['password']}")
    print(f"   Encrypted: {encrypted_dict['password'][:30]}...")
    
    # Test hashing
    print("\n4. Data Hashing:")
    hashed = hash_sensitive_data("password123", salt="my-salt")
    print(f"   Hash: {hashed}")
    
    # Test masking
    print("\n5. Data Masking:")
    print(f"   Card: {mask_sensitive_data('1234567890123456', 4, 4)}")
    print(f"   Phone: {mask_sensitive_data('9876543210', 2, 2)}")
    
    # Check cryptography availability
    print(f"\n6. Cryptography Library: {'Available' if CRYPTOGRAPHY_AVAILABLE else 'NOT AVAILABLE - Using fallback'}")
    
    print("\n" + "=" * 70)
