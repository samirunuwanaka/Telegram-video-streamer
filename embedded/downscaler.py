"""
ESP32 Low-Computational Frame Downscaler & Compression Control
Optimized for low RAM and minimal CPU overhead on microcontrollers.
"""

class Downscaler:
    """
    Manages resolution scaling and quality parameters for bandwidth reduction.
    """

    RESOLUTIONS = {
        "1080p": (1920, 1080),
        "720p": (1280, 720),
        "VGA": (640, 480),
        "QVGA": (320, 240),
        "QQVGA": (160, 120),
    }

    def __init__(self, target_width: int = 640, target_height: int = 480, quality: int = 50):
        self.width = target_width
        self.height = target_height
        self.quality = quality  # JPEG Compression Quality (1 - 100)

    def set_resolution(self, width: int, height: int):
        self.width = width
        self.height = height

    def set_preset(self, preset_name: str):
        if preset_name in self.RESOLUTIONS:
            self.width, self.height = self.RESOLUTIONS[preset_name]

    def set_quality(self, quality: int):
        self.quality = max(10, min(90, quality))
