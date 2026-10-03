"""
Standardized Message Specifications for Telegram Local Video Communicator
"""

# Telegram Bot User Commands
CMD_START = "/start"
CMD_STREAM = "/stream"
CMD_STOP = "/stop"
CMD_FPS = "/fps"
CMD_QUALITY = "/quality"
CMD_STATUS = "/status"
CMD_SNAPSHOT = "/snapshot"

# System Actions
ACTION_START_STREAM = "start_stream"
ACTION_STOP_STREAM = "stop_stream"
ACTION_SET_FPS = "set_fps"
ACTION_SET_QUALITY = "set_quality"
ACTION_ACK_FRAME = "ack_frame"

def format_status_message(device_id: str, is_streaming: bool, fps: int, width: int, height: int, seq: int) -> str:
    status_str = "🟢 Streaming Active" if is_streaming else "🔴 Stopped"
    return (
        f"<b>📷 Device Status</b>\n"
        f"• <b>ID:</b> <code>{device_id}</code>\n"
        f"• <b>State:</b> {status_str}\n"
        f"• <b>Target FPS:</b> {fps}\n"
        f"• <b>Resolution:</b> {width}x{height}\n"
        f"• <b>Last Sequence #:</b> {seq}"
    )
