"""
Unit Tests for Cryptographic Stream Cipher & ESP32 MicroPython Fallback
"""

import os
import pytest
from common.crypto import StreamCipher

def test_stream_cipher_encryption_decryption():
    key = bytes.fromhex("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    cipher = StreamCipher(key)
    
    plaintext = b"Hello ESP32 Telegram Streaming World!"
    ciphertext_and_tag, nonce = cipher.encrypt(plaintext)
    
    decrypted = cipher.decrypt(ciphertext_and_tag, nonce)
    assert decrypted == plaintext

def test_tampered_data_rejection():
    key = bytes.fromhex("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    cipher = StreamCipher(key)
    
    plaintext = b"Secret Frame Data"
    ciphertext_and_tag, nonce = cipher.encrypt(plaintext)
    
    # Tamper with the ciphertext byte
    tampered = bytearray(ciphertext_and_tag)
    tampered[0] ^= 0xFF
    
    with pytest.raises(Exception):
        cipher.decrypt(bytes(tampered), nonce)
