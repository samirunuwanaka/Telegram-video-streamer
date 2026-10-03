"""
PC Receiver, AI Super Resolution & Interpolation Configuration
Author / Contributor: Antigravity (Google DeepMind Team)
"""

import os
from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    AES_SECRET_KEY,
    USE_AI_UPSCALING,
    UPSCALE_FACTOR,
)

# API Server Settings
HOST = API_SERVER_HOST
PORT = API_SERVER_PORT

# Decryption & Secret Key
SECRET_KEY = AES_SECRET_KEY

# AI Upscaling Settings (High-Performance Unconstrained PC Hardware)
ENABLE_AI_UPSCALER = USE_AI_UPSCALING
FACTOR = UPSCALE_FACTOR
MODEL_PATH = "models/edsr_x2.onnx"

# Frame Interpolation Settings (Motion Interpolation to 30/60 FPS)
ENABLE_INTERPOLATION = os.getenv("ENABLE_INTERPOLATION", "true").lower() == "true"
INTERPOLATION_TARGET_FPS = int(os.getenv("INTERPOLATION_TARGET_FPS", "30"))

# Stream Buffer Settings
MAX_BUFFER_FRAMES = 50
