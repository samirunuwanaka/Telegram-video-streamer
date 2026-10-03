"""
ESP32 Embedded Main Application Entry Point
Supports MicroPython on ESP32 & Standard Python fallback for testing.

Pipeline:
1. Capture frame from camera.
2. Downscale / JPEG compression for bandwidth reduction.
3. Encrypt payload with authenticated cipher (AES-GCM / HMAC).
4. Transmit frame & Wait for ACK / next frame slot (Stop-and-Wait flow control).
5. Handle stop / start / set_fps commands in real-time.
"""

import sys
import time

# ==============================================================================
# EMBEDDED CONFIGURATION VARIABLES (TOP LEVEL)
# ==============================================================================
try:
    from embedded.config_esp32 import (
        DEVICE_ID,
        PC_SERVER_URL,
        TARGET_FPS,
        FRAME_WIDTH,
        FRAME_HEIGHT,
        JPEG_QUALITY,
        SECRET_KEY,
        WAIT_FOR_ACK,
        TELEGRAM_CHAT_ID,
    )
except ImportError:
    # Top-level standalone fallbacks for ESP32 micro-environment
    DEVICE_ID = "esp32_cam_01"
    PC_SERVER_URL = "http://127.0.0.1:8000/api/v1/stream/push"
    TARGET_FPS = 10
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    JPEG_QUALITY = 50
    SECRET_KEY = bytes.fromhex("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    WAIT_FOR_ACK = True
    TELEGRAM_CHAT_ID = None

from embedded.camera import CameraSensor
from embedded.downscaler import Downscaler
from embedded.crypto_esp32 import ESP32Encryptor
from embedded.uploader import BitstreamUploader
from embedded.device_commands import DeviceCommandHandler
from common.protocol import FramePacket


class ESP32Streamer:
    """
    Main Streamer pipeline for ESP32.
    """

    def __init__(self):
        self.device_state = {
            "device_id": DEVICE_ID,
            "is_streaming": True,
            "fps": TARGET_FPS,
            "width": FRAME_WIDTH,
            "height": FRAME_HEIGHT,
            "quality": JPEG_QUALITY,
            "sequence": 0,
        }

        self.camera = CameraSensor(width=FRAME_WIDTH, height=FRAME_HEIGHT, quality=JPEG_QUALITY)
        self.downscaler = Downscaler(target_width=FRAME_WIDTH, target_height=FRAME_HEIGHT, quality=JPEG_QUALITY)
        self.encryptor = ESP32Encryptor(SECRET_KEY)
        self.uploader = BitstreamUploader(
            server_url=PC_SERVER_URL,
            device_id=DEVICE_ID,
            wait_for_ack=WAIT_FOR_ACK,
            telegram_chat_id=TELEGRAM_CHAT_ID,
        )
        self.cmd_handler = DeviceCommandHandler(self.device_state)

    def start(self):
        """
        Main execution loop.
        """
        print(f"🚀 Initializing ESP32 Streamer [{DEVICE_ID}]...")
        if not self.camera.init():
            print("❌ Camera initialization failed!")
            return

        print(f"✅ Camera online. Target FPS: {self.device_state['fps']}. Pushing to {PC_SERVER_URL}")

        try:
            while True:
                if not self.device_state["is_streaming"]:
                    time.sleep(0.5)
                    continue

                start_time = time.time()

                # 1. Capture Raw Frame
                raw_frame = self.camera.capture_frame()
                if not raw_frame:
                    time.sleep(0.1)
                    continue

                # 2. Increment Sequence Counter
                self.device_state["sequence"] += 1
                seq = self.device_state["sequence"]

                # 3. Low-computational Encryption
                encrypted_payload, nonce = self.encryptor.encrypt_frame(raw_frame)

                # 4. Wrap into Protocol FramePacket
                packet = FramePacket(
                    device_id=self.device_state["device_id"],
                    sequence=seq,
                    encrypted_payload=encrypted_payload,
                    nonce=nonce,
                    width=self.device_state["width"],
                    height=self.device_state["height"],
                    fps=self.device_state["fps"],
                    codec="jpeg",
                )

                # 5. Push Bitstream Frame & Wait for ACK (Stop-and-Wait Flow Control)
                success, incoming_cmd = self.uploader.send_frame(packet)

                if success:
                    print(f"📦 Frame #{seq} sent & ACKed successfully ({len(encrypted_payload)} bytes).")
                else:
                    print(f"⚠️ Frame #{seq} send/ACK failed or timed out.")

                # 6. Process Incoming Command if returned in ACK response
                if incoming_cmd:
                    print(f"📩 Command received: {incoming_cmd.action}")
                    self.cmd_handler.process_command(incoming_cmd)

                # 7. Adaptive Frame Rate Control (Throttle to set FPS)
                target_interval = 1.0 / float(max(1, self.device_state["fps"]))
                elapsed = time.time() - start_time
                sleep_time = target_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n🛑 Stopping ESP32 Streamer...")
        finally:
            self.camera.deinit()
            print("✅ Resources released.")


if __name__ == "__main__":
    streamer = ESP32Streamer()
    streamer.start()
