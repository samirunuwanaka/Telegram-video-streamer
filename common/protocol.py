"""
Protocol Framing & Serialization Standard for Telegram Local AI Stream
Defines frame headers, metadata schema, and packet encapsulation.
"""

import json
import time
import base64
from typing import Optional, Dict, Any


class FramePacket:
    """
    Encapsulates a video frame or data packet with cryptographic payload and metadata.
    """

    PROTOCOL_VERSION = 1

    def __init__(
        self,
        device_id: str,
        sequence: int,
        encrypted_payload: bytes,
        nonce: bytes,
        width: int = 640,
        height: int = 480,
        fps: int = 10,
        timestamp: Optional[float] = None,
        codec: str = "jpeg",
    ):
        self.version = self.PROTOCOL_VERSION
        self.device_id = device_id
        self.sequence = sequence
        self.encrypted_payload = encrypted_payload
        self.nonce = nonce
        self.width = width
        self.height = height
        self.fps = fps
        self.timestamp = timestamp or time.time()
        self.codec = codec

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes packet to a JSON-compatible dictionary.
        Encodes binary payload and nonce to Base64 strings.
        """
        return {
            "version": self.version,
            "device_id": self.device_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "codec": self.codec,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "nonce": base64.b64encode(self.nonce).decode("utf-8"),
            "payload": base64.b64encode(self.encrypted_payload).decode("utf-8"),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FramePacket":
        nonce = base64.b64decode(data["nonce"])
        payload = base64.b64decode(data["payload"])
        pkt = cls(
            device_id=data.get("device_id", "unknown"),
            sequence=data.get("sequence", 0),
            encrypted_payload=payload,
            nonce=nonce,
            width=data.get("width", 640),
            height=data.get("height", 480),
            fps=data.get("fps", 10),
            timestamp=data.get("timestamp", time.time()),
            codec=data.get("codec", "jpeg"),
        )
        pkt.version = data.get("version", 1)
        return pkt

    @classmethod
    def from_json(cls, json_str: str) -> "FramePacket":
        return cls.from_dict(json.loads(json_str))


class CommandPacket:
    """
    Control Command Packet (e.g. set_fps, start_stream, stop_stream, ack_frame).
    """

    def __init__(self, action: str, params: Optional[Dict[str, Any]] = None):
        self.action = action  # e.g., "start", "stop", "set_fps", "ack"
        self.params = params or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "params": self.params,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "CommandPacket":
        data = json.loads(json_str)
        cmd = cls(action=data["action"], params=data.get("params", {}))
        cmd.timestamp = data.get("timestamp", time.time())
        return cmd
