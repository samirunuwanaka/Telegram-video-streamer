"""
PC Decryption, Stream Receiver, AI Upscaling & Frame Interpolation Engine
Author / Contributor: Antigravity (Google DeepMind Team)

Receives encrypted packets from ESP32, decrypts payloads, applies AI Super Resolution,
and executes dense optical-flow frame interpolation for 30/60 FPS high-framerate playback.
"""

import time
import threading
from typing import Optional, Dict, Any, List
from common.crypto import StreamCipher
from common.protocol import FramePacket, CommandPacket
from pc.decoder import FrameDecoder
from pc.upscaler import LocalUpscaler
from pc.interpolator import FrameInterpolator
from pc.config_pc import (
    SECRET_KEY,
    ENABLE_AI_UPSCALER,
    FACTOR,
    ENABLE_INTERPOLATION,
    INTERPOLATION_TARGET_FPS,
)


class StreamReceiver:
    """
    Core receiver engine for incoming ESP32 bitstream packets.
    Integrates AI Super-Resolution upscaling and motion frame interpolation.
    """

    def __init__(self):
        self.cipher = StreamCipher(SECRET_KEY)
        self.decoder = FrameDecoder()
        self.upscaler = LocalUpscaler(upscale_factor=FACTOR, enable_ai=ENABLE_AI_UPSCALER)
        self.interpolator = FrameInterpolator(target_output_fps=INTERPOLATION_TARGET_FPS)
        
        self.latest_raw_frame: Optional[bytes] = None
        self.latest_decoded_frame: Optional[Any] = None
        self.latest_upscaled_frame: Optional[Any] = None
        
        # Buffer for motion interpolation
        self.prev_processed_frame: Optional[Any] = None
        self.interpolated_frames_queue: List[Any] = []
        
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
        Decrypts incoming frame, applies AI upscaling and motion interpolation,
        and returns ACK response payload with pending control commands.
        """
        if packet.sequence <= self.last_sequence and (self.last_sequence - packet.sequence < 1000):
            print(f"⚠️ Duplicate/out-of-order frame #{packet.sequence} ignored.")

        # 1. Decrypt Payload
        try:
            decrypted_jpeg = self.cipher.decrypt(packet.encrypted_payload, packet.nonce)
        except Exception as e:
            print(f"❌ Decryption failed for frame #{packet.sequence}: {e}")
            raise ValueError(f"Decryption failed: {e}")

        # 2. Decode JPEG & Apply AI Super Resolution
        decoded_bgr = self.decoder.decode_jpeg(decrypted_jpeg)
        upscaled_bgr = self.upscaler.upscale(decoded_bgr) if decoded_bgr is not None else None

        # 3. Perform Motion Frame Interpolation (Low-FPS -> High-FPS)
        new_interpolated: List[Any] = []
        if ENABLE_INTERPOLATION and upscaled_bgr is not None:
            if self.prev_processed_frame is not None:
                # Calculate required intermediate frames count to reach target FPS
                incoming_fps = max(1, packet.fps)
                multiplier = max(1, INTERPOLATION_TARGET_FPS // incoming_fps)
                num_intermediates = multiplier - 1
                if num_intermediates > 0:
                    new_interpolated = self.interpolator.interpolate_between(
                        self.prev_processed_frame,
                        upscaled_bgr,
                        num_intermediates=num_intermediates
                    )
            self.prev_processed_frame = upscaled_bgr

        # 4. Update Thread-safe Buffer
        with self._lock:
            self.latest_raw_frame = decrypted_jpeg
            self.latest_decoded_frame = decoded_bgr
            self.latest_upscaled_frame = upscaled_bgr
            
            # Store generated motion interpolated frames
            if new_interpolated:
                self.interpolated_frames_queue.extend(new_interpolated)
                # Keep queue length bounded
                if len(self.interpolated_frames_queue) > 60:
                    self.interpolated_frames_queue = self.interpolated_frames_queue[-60:]

            self.last_sequence = packet.sequence
            self.last_timestamp = packet.timestamp
            self.frames_received_count += 1
            self.device_id = packet.device_id
            self.current_fps = packet.fps

            # Pop pending control command
            outgoing_cmd = self.pending_command
            self.pending_command = None

        cmd_json = outgoing_cmd.to_json() if outgoing_cmd else None

        return {
            "status": "ack",
            "ack_sequence": packet.sequence,
            "device_id": packet.device_id,
            "command": cmd_json,
        }

    def get_latest_jpeg(self, use_upscaled: bool = True) -> Optional[bytes]:
        """
        Returns JPEG bytes of the latest upscaled / interpolated frame.
        """
        with self._lock:
            if self.interpolated_frames_queue:
                frame = self.interpolated_frames_queue.pop(0)
                return self.decoder.encode_jpeg(frame)
            elif use_upscaled and self.latest_upscaled_frame is not None:
                return self.decoder.encode_jpeg(self.latest_upscaled_frame)
            return self.latest_raw_frame

    def set_pending_command(self, cmd: CommandPacket):
        with self._lock:
            self.pending_command = cmd

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "device_id": self.device_id,
                "is_streaming": self.is_streaming,
                "fps": self.current_fps,
                "output_target_fps": INTERPOLATION_TARGET_FPS if ENABLE_INTERPOLATION else self.current_fps,
                "interpolation_enabled": ENABLE_INTERPOLATION,
                "last_sequence": self.last_sequence,
                "total_frames_received": self.frames_received_count,
                "last_active_timestamp": self.last_timestamp,
            }
