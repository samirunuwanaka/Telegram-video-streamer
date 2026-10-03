"""
PC Decryption & Stream Receiver Engine
Receives encrypted packets from ESP32 / Telegram transport, verifies authenticity, and decrypts payloads.
"""

import time
import threading
from typing import Optional, Dict, Any
from common.crypto import StreamCipher
from common.protocol import FramePacket, CommandPacket
from pc.decoder import FrameDecoder
from pc.upscaler import LocalUpscaler
from pc.config_pc import SECRET_KEY, ENABLE_AI_UPSCALER, FACTOR


class StreamReceiver:
    """
    Core receiver and manager for incoming device bitstream packets.
    """

    def __init__(self):
        self.cipher = StreamCipher(SECRET_KEY)
        self.decoder = FrameDecoder()
        self.upscaler = LocalUpscaler(upscale_factor=FACTOR, enable_ai=ENABLE_AI_UPSCALER)
        
        self.latest_raw_frame: Optional[bytes] = None
        self.latest_decoded_frame: Optional[Any] = None
        self.latest_upscaled_frame: Optional[Any] = None
        
        self.last_sequence: int = 0
        self.last_timestamp: float = time.time()
        self.frames_received_count: int = 0
        self.device_id: str = "esp32_cam_01"
        self.is_streaming: bool = True
        self.current_fps: int = 10

        self.pending_command: Optional[CommandPacket] = None
        self._lock = threading.Lock()

    def process_packet(self, packet: FramePacket) -> Dict[str, Any]:
        """
        Decrypts frame, updates latest frame buffer, and returns ACK response payload with any pending control commands.
        """
        # Replay protection / sequence check
        if packet.sequence <= self.last_sequence and (self.last_sequence - packet.sequence < 1000):
            print(f"⚠️ Duplicate or out-of-order frame #{packet.sequence} ignored.")

        # 1. Decrypt Encrypted Payload
        try:
            decrypted_jpeg = self.cipher.decrypt(packet.encrypted_payload, packet.nonce)
        except Exception as e:
            print(f"❌ Decryption failed for frame #{packet.sequence}: {e}")
            raise ValueError(f"Decryption failed: {e}")

        # 2. Decode & AI Upscale
        decoded_bgr = self.decoder.decode_jpeg(decrypted_jpeg)
        upscaled_bgr = self.upscaler.upscale(decoded_bgr) if decoded_bgr is not None else None

        # 3. Update Thread-safe Buffer
        with self._lock:
            self.latest_raw_frame = decrypted_jpeg
            self.latest_decoded_frame = decoded_bgr
            self.latest_upscaled_frame = upscaled_bgr
            self.last_sequence = packet.sequence
            self.last_timestamp = packet.timestamp
            self.frames_received_count += 1
            self.device_id = packet.device_id
            self.current_fps = packet.fps

            # Pop pending command if any exists
            outgoing_cmd = self.pending_command
            self.pending_command = None

        cmd_json = outgoing_cmd.to_json() if outgoing_cmd else None

        return {
            "status": "ack",
            "ack_sequence": packet.sequence,
            "device_id": packet.device_id,
            "command": cmd_json,
        }

    def set_pending_command(self, cmd: CommandPacket):
        """
        Queues a command (e.g., set_fps, stop_stream) to be sent to ESP32 on next frame ACK.
        """
        with self._lock:
            self.pending_command = cmd

    def get_latest_jpeg(self, use_upscaled: bool = True) -> Optional[bytes]:
        """
        Returns JPEG bytes of latest frame for streaming API.
        """
        with self._lock:
            if use_upscaled and self.latest_upscaled_frame is not None:
                return self.decoder.encode_jpeg(self.latest_upscaled_frame)
            return self.latest_raw_frame

    def get_status(self) -> Dict[str, Any]:
        """
        Returns current stream metrics and state.
        """
        with self._lock:
            return {
                "device_id": self.device_id,
                "is_streaming": self.is_streaming,
                "fps": self.current_fps,
                "last_sequence": self.last_sequence,
                "total_frames_received": self.frames_received_count,
                "last_active_timestamp": self.last_timestamp,
            }
