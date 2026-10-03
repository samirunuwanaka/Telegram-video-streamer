"""
PC AI/ML Super-Resolution Local Upscaler
Upscales downsampled video frames locally on the PC using OpenCV / ONNX Runtime.
"""

from typing import Optional
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


class LocalUpscaler:
    """
    Local AI/ML Super Resolution Upscaler for video stream reconstruction.
    """

    def __init__(self, upscale_factor: int = 2, enable_ai: bool = True):
        self.upscale_factor = upscale_factor
        self.enable_ai = enable_ai
        self.sr_model = None

        if self.enable_ai and cv2 is not None:
            # Check for OpenCV DNN Super Resolution module support
            try:
                if hasattr(cv2, 'dnn_superres'):
                    self.sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
                    # Fallback to bicubic if specific model file is missing
            except Exception:
                self.sr_model = None

    def upscale(self, frame: np.ndarray) -> np.ndarray:
        """
        Upscales input frame by factor (e.g. 2x).
        Uses AI Super Resolution if available, otherwise fast high-quality Bicubic interpolation.
        """
        if frame is None:
            return frame

        h, w = frame.shape[:2]
        target_w, target_h = w * self.upscale_factor, h * self.upscale_factor

        if self.sr_model:
            try:
                return self.sr_model.upsample(frame)
            except Exception:
                pass

        # High quality bicubic upscaling fallback
        if cv2 is not None:
            return cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        else:
            return frame
