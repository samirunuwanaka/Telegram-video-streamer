"""
PC Receiver & API Server Configuration
Configurable parameters placed at top.
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

# AI Upscaling Settings
ENABLE_AI_UPSCALER = USE_AI_UPSCALING
FACTOR = UPSCALE_FACTOR
MODEL_PATH = "models/edsr_x2.onnx"

# Stream Buffer Settings
MAX_BUFFER_FRAMES = 30
