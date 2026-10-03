"""
Lightweight ESP32 MicroPython Stream Encryption Helper
"""

import os
import sys

# Import common cipher if available or provide embedded wrapper
try:
    from common.crypto import StreamCipher
except ImportError:
    import struct
    import hmac
    import hashlib

    class StreamCipher:
        """
        Standalone fallback for MicroPython environment without package layout.
        """
        def __init__(self, key: bytes):
            if len(key) != 32:
                raise ValueError("Key must be 32 bytes")
            self.key = key

        def encrypt(self, plaintext: bytes, nonce: bytes = None) -> tuple[bytes, bytes]:
            if nonce is None:
                nonce = os.urandom(12)
            ciphertext = self._simple_xor_stream(plaintext, self.key, nonce)
            tag = hmac.new(self.key, nonce + ciphertext, hashlib.sha256).digest()[:16]
            return ciphertext + tag, nonce

        def decrypt(self, ciphertext_and_tag: bytes, nonce: bytes) -> bytes:
            ciphertext = ciphertext_and_tag[:-16]
            return self._simple_xor_stream(ciphertext, self.key, nonce)

        @staticmethod
        def _simple_xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
            res = bytearray(len(data))
            counter = 0
            key_len = len(key)
            for i in range(len(data)):
                if i % key_len == 0:
                    keystream_block = hashlib.sha256(key + nonce + struct.pack(">I", counter)).digest()
                    counter += 1
                res[i] = data[i] ^ keystream_block[i % 32]
            return bytes(res)


class ESP32Encryptor:
    """
    ESP32 stream encryption helper wrapper.
    """

    def __init__(self, secret_key: bytes):
        self.cipher = StreamCipher(secret_key)

    def encrypt_frame(self, frame_bytes: bytes) -> tuple[bytes, bytes]:
        """
        Encrypts raw JPEG bytes into authenticated ciphertext.
        Returns: (ciphertext_with_tag, 12-byte nonce)
        """
        return self.cipher.encrypt(frame_bytes)
