"""
ESP32 Embedded Config & Variables
Variables placed at the top for easy embedded deployment configuration.
"""

# Device Information
DEVICE_ID = "esp32_cam_01"

# Network & Server Endpoints (for PC or Telegram API server)
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"
PC_SERVER_URL = "http://192.168.1.100:8000/api/v1/stream/push"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# Video Capture Settings
TARGET_FPS = 10
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
JPEG_QUALITY = 50  # 1-100 (lower number = higher compression / lower bandwidth)

# Encryption Key (32-byte key)
SECRET_KEY_HEX = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
SECRET_KEY = bytes.fromhex(SECRET_KEY_HEX)

# Flow Control
WAIT_FOR_ACK = True   # Stop-and-wait mode: Wait for PC/Bot ACK before sending next frame
ACK_TIMEOUT_SEC = 2.0
