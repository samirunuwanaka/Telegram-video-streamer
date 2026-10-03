"""
PC Video Frame Decoder
Decodes raw JPEG byte streams into OpenCV image matrix format (BGR numpy array).
"""

from typing import Optional
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


class FrameDecoder:
    """
    Decodes compressed stream payloads into raw frames for display or processing.
    """

    def __init__(self):
        pass

    def decode_jpeg(self, jpeg_bytes: bytes) -> Optional[np.ndarray]:
        """
        Decodes JPEG byte buffer into an OpenCV BGR frame (numpy uint8 matrix).
        """
        if cv2 is None or not jpeg_bytes:
            return None

        try:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"❌ Error decoding JPEG frame: {e}")
            return None

    def encode_jpeg(self, frame: np.ndarray, quality: int = 80) -> bytes:
        """
        Encodes OpenCV BGR image matrix to JPEG byte string.
        """
        if cv2 is None or frame is None:
            return b""
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, buf = cv2.imencode(".jpg", frame, encode_params)
        return buf.tobytes()
