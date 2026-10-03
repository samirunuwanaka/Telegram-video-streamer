"""
Global Configuration for Telegram Video Communicator
All configurable parameters are defined at the top for easy maintenance.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# ==============================================================================
# 1. TELEGRAM BOT SETTINGS
# ==============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
_auth_users_str = os.getenv("AUTHORIZED_USER_IDS", "")
AUTHORIZED_USER_IDS = [
    int(uid.strip()) for uid in _auth_users_str.split(",") if uid.strip().isdigit()
]

# ==============================================================================
# 2. DEVICE & VIDEO SETTINGS
# ==============================================================================
DEVICE_ID = os.getenv("DEVICE_ID", "esp32_cam_01")
DEFAULT_FPS = int(os.getenv("EMBEDDED_TARGET_FPS", "10"))
DEFAULT_WIDTH = int(os.getenv("EMBEDDED_RESOLUTION_WIDTH", "640"))
DEFAULT_HEIGHT = int(os.getenv("EMBEDDED_RESOLUTION_HEIGHT", "480"))
DEFAULT_JPEG_QUALITY = int(os.getenv("EMBEDDED_JPEG_QUALITY", "60"))

# ==============================================================================
# 3. SECURITY & ENCRYPTION SETTINGS
# ==============================================================================
# 32-byte secret key represented in hex (64 characters)
DEFAULT_HEX_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
AES_SECRET_KEY_HEX = os.getenv("AES_SECRET_KEY", DEFAULT_HEX_KEY)
try:
    AES_SECRET_KEY = bytes.fromhex(AES_SECRET_KEY_HEX)
except ValueError:
    AES_SECRET_KEY = DEFAULT_HEX_KEY.encode("utf-8")[:32]

# ==============================================================================
# 4. PC API SERVER SETTINGS
# ==============================================================================
API_SERVER_HOST = os.getenv("API_SERVER_HOST", "0.0.0.0")
API_SERVER_PORT = int(os.getenv("API_SERVER_PORT", "8000"))
USE_AI_UPSCALING = os.getenv("USE_AI_UPSCALING", "true").lower() == "true"
UPSCALE_FACTOR = 2  # 2x super resolution

# ==============================================================================
# 5. STORAGE & CLEANUP DIRECTORIES
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
TEMP_DATA_DIR = Path(os.getenv("TEMP_DATA_DIR", BASE_DIR / "data" / "temporary"))
INCOMING_DATA_DIR = Path(os.getenv("INCOMING_DATA_DIR", BASE_DIR / "data" / "incoming"))
PROCESSING_DATA_DIR = Path(os.getenv("PROCESSING_DATA_DIR", BASE_DIR / "data" / "processing"))

# Ensure directories exist
for folder in [TEMP_DATA_DIR, INCOMING_DATA_DIR, PROCESSING_DATA_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
