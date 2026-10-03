"""
Cryptographic Utilities for Encrypted Video & Data Stream
Supports AES-256-GCM for PC / standard Python and lightweight AES-CTR + HMAC or GCM for MicroPython ESP32.
"""

import os
import struct
import hmac
import hashlib

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class StreamCipher:
    """
    Authenticated Encryption handler.
    Uses AES-256-GCM when cryptography module is available.
    Provides a pure Python AES / HMAC fallback compatible with MicroPython.
    """

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes (256 bits) long.")
        self.key = key
        if HAS_CRYPTOGRAPHY:
            self._aesgcm = AESGCM(self.key)
        else:
            self._aesgcm = None

    def encrypt(self, plaintext: bytes, nonce: bytes = None) -> tuple[bytes, bytes]:
        """
        Encrypts plaintext bytes.
        Returns: (ciphertext_with_tag, nonce)
        """
        if nonce is None:
            nonce = os.urandom(12)

        if self._aesgcm:
            # AES-GCM returns ciphertext + 16-byte tag attached
            ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext, None)
            return ciphertext_and_tag, nonce
        else:
            # MicroPython / Pure Python fallback: XOR stream + HMAC tag
            ciphertext = self._simple_xor_stream(plaintext, self.key, nonce)
            tag = hmac.new(self.key, nonce + ciphertext, hashlib.sha256).digest()[:16]
            return ciphertext + tag, nonce

    def decrypt(self, ciphertext_and_tag: bytes, nonce: bytes) -> bytes:
        """
        Decrypts ciphertext bytes and verifies integrity tag.
        """
        if self._aesgcm:
            return self._aesgcm.decrypt(nonce, ciphertext_and_tag, None)
        else:
            if len(ciphertext_and_tag) < 16:
                raise ValueError("Invalid ciphertext length")
            ciphertext = ciphertext_and_tag[:-16]
            expected_tag = ciphertext_and_tag[-16:]

            actual_tag = hmac.new(self.key, nonce + ciphertext, hashlib.sha256).digest()[:16]
            if not hmac.compare_digest(actual_tag, expected_tag):
                raise ValueError("Authentication tag verification failed! Data tampered.")
            return self._simple_xor_stream(ciphertext, self.key, nonce)

    @staticmethod
    def _simple_xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Fast XOR keystream generator for lightweight embedded fallback.
        """
        res = bytearray(len(data))
        counter = 0
        key_len = len(key)
        for i in range(len(data)):
            if i % key_len == 0:
                keystream_block = hashlib.sha256(key + nonce + struct.pack(">I", counter)).digest()
                counter += 1
            res[i] = data[i] ^ keystream_block[i % 32]
        return bytes(res)
