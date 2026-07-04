"""
KOVIRX Endpoint Agent — Payload Encryption.

AES-256-GCM encryption layer for sensitive telemetry data.
Key is derived from the device JWT or a pre-shared key.
"""

import base64
import hashlib
import logging
import os

logger = logging.getLogger("kovirx.agent.encryption")


def derive_key(secret: str) -> bytes:
    """
    Derive a 256-bit AES key from a secret string using SHA-256.

    Args:
        secret: Secret string (e.g., JWT token or pre-shared key)

    Returns:
        32-byte key suitable for AES-256
    """
    return hashlib.sha256(secret.encode("utf-8")).digest()


def encrypt_payload(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data using AES-256-GCM.

    Returns:
        Concatenation of nonce (12 bytes) + ciphertext + tag (16 bytes),
        base64 encoded.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        logger.debug("cryptography library not available; returning unencrypted payload.")
        return data

    try:
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        # Encode: nonce + ciphertext (includes tag)
        encrypted = base64.b64encode(nonce + ciphertext)
        logger.debug("Payload encrypted: %d → %d bytes", len(data), len(encrypted))
        return encrypted
    except Exception as e:
        logger.error("Encryption failed: %s", e)
        return data


def decrypt_payload(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypt AES-256-GCM encrypted data.

    Args:
        encrypted_data: Base64-encoded nonce + ciphertext + tag
        key: 32-byte AES key

    Returns:
        Decrypted plaintext bytes
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        logger.debug("cryptography library not available; returning data as-is.")
        return encrypted_data

    try:
        raw = base64.b64decode(encrypted_data)
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        logger.error("Decryption failed: %s", e)
        raise
