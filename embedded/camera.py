"""
ESP32 MicroPython / Python Camera Interface
Supports ESP32 hardware camera (OV2640) in MicroPython with fallback for desktop testing.
"""

import sys
import time

# Check if running under MicroPython
IS_MICROPYTHON = sys.implementation.name == "micropython"

if IS_MICROPYTHON:
    try:
        import camera as esp_camera
    except ImportError:
        esp_camera = None
else:
    esp_camera = None
    try:
        import cv2
    except ImportError:
        cv2 = None


class CameraSensor:
    """
    Unified Camera Interface for MicroPython ESP32 and Desktop Python simulation.
    """

    def __init__(self, width: int = 640, height: int = 480, quality: int = 50):
        self.width = width
        self.height = height
        self.quality = quality
        self._is_initialized = False
        self._desktop_cap = None

    def init(self) -> bool:
        """
        Initialize the camera sensor hardware.
        """
        if IS_MICROPYTHON and esp_camera:
            # Initialize ESP32-CAM hardware
            esp_camera.init(0, format=esp_camera.JPEG)
            esp_camera.framesize(esp_camera.FRAME_VGA)
            esp_camera.quality(self.quality)
            self._is_initialized = True
            return True
        elif cv2 is not None:
            # Fallback to desktop camera capture (e.g., webcam)
            self._desktop_cap = cv2.VideoCapture(0)
            self._is_initialized = self._desktop_cap.isOpened()
            return self._is_initialized
        else:
            # Simulated software test mode
            self._is_initialized = True
            return True

    def capture_frame(self) -> bytes:
        """
        Captures a frame and returns JPEG encoded byte stream.
        """
        if not self._is_initialized:
            self.init()

        if IS_MICROPYTHON and esp_camera:
            frame_bytes = esp_camera.capture()
            return frame_bytes if frame_bytes else b""
        elif cv2 and self._desktop_cap and self._desktop_cap.isOpened():
            ret, frame = self._desktop_cap.read()
            if not ret or frame is None:
                return self._generate_synthetic_frame()
            # Downsample / resize frame to target dimensions
            resized = cv2.resize(frame, (self.width, self.height))
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            _, jpeg_buf = cv2.imencode(".jpg", resized, encode_param)
            return jpeg_buf.tobytes()
        else:
            return self._generate_synthetic_frame()

    def _generate_synthetic_frame(self) -> bytes:
        """
        Generates a minimal valid JPEG image in memory for testing when hardware camera is offline.
        """
        if cv2 is not None:
            import numpy as np
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            t = int(time.time() * 10) % 255
            # Draw moving gradient text or patterns
            cv2.putText(img, f"ESP32 Stream Test: {t}", (30, self.height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, t), 2)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            _, jpeg_buf = cv2.imencode(".jpg", img, encode_param)
            return jpeg_buf.tobytes()
        else:
            # Minimal 1x1 JPEG header fallback
            return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"

    def deinit(self):
        """
        Releases camera hardware resources.
        """
        if cv2 and self._desktop_cap:
            self._desktop_cap.release()
        if IS_MICROPYTHON and esp_camera:
            try:
                esp_camera.deinit()
            except Exception:
                pass
        self._is_initialized = False
