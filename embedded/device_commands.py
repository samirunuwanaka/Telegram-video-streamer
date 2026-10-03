"""
ESP32 Embedded Device Command Handler
Processes dynamic commands such as changing FPS, resolution, or stopping stream.
"""

from common.messages import ACTION_START_STREAM, ACTION_STOP_STREAM, ACTION_SET_FPS, ACTION_SET_QUALITY
from common.protocol import CommandPacket


class DeviceCommandHandler:
    """
    Manages state changes for the embedded device based on received commands.
    """

    def __init__(self, device_state: dict):
        self.state = device_state

    def process_command(self, cmd: CommandPacket) -> bool:
        """
        Executes incoming command packet. Returns True if state changed.
        """
        if not cmd or not cmd.action:
            return False

        action = cmd.action
        params = cmd.params

        if action == ACTION_START_STREAM:
            self.state["is_streaming"] = True
            return True
        elif action == ACTION_STOP_STREAM:
            self.state["is_streaming"] = False
            return True
        elif action == ACTION_SET_FPS:
            if "fps" in params:
                fps = int(params["fps"])
                self.state["fps"] = max(1, min(30, fps))
                return True
        elif action == ACTION_SET_QUALITY:
            if "quality" in params:
                q = int(params["quality"])
                self.state["quality"] = max(10, min(90, q))
                return True

        return False
