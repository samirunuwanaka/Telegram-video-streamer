"""
ESP32 Bitstream Uploader with Flow Control (Stop-and-Wait ACK per Frame)
Prevents network congestion and memory overflow on microcontrollers.
"""

import time
import requests
from typing import Optional
from common.protocol import FramePacket, CommandPacket


class BitstreamUploader:
    """
    Handles streaming frame packets to the PC Server or Telegram interface.
    Implements flow-control stop-and-wait mechanism per frame.
    """

    def __init__(
        self,
        server_url: str,
        device_id: str,
        wait_for_ack: bool = True,
        ack_timeout_sec: float = 2.0,
        telegram_chat_id: Optional[str] = None,
    ):
        self.server_url = server_url
        self.device_id = device_id
        self.wait_for_ack = wait_for_ack
        self.ack_timeout_sec = ack_timeout_sec
        self.telegram_chat_id = telegram_chat_id
        self.session = requests.Session()

    def send_frame(self, packet: FramePacket) -> tuple[bool, Optional[CommandPacket]]:
        """
        Pushes an encrypted frame packet to the receiver API or Telegram tunnel endpoint.
        If wait_for_ack is enabled, blocks until server/relay responds with ACK or control commands.
        Returns: (success_boolean, optional_command_packet_received)
        """
        payload_data = packet.to_dict()
        try:
            # Check if using Telegram Bot API Tunneling
            if "api.telegram.org" in self.server_url:
                import json
                tg_payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": f"FRAME:{json.dumps(payload_data)}",
                }
                response = self.session.post(
                    self.server_url,
                    json=tg_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.ack_timeout_sec,
                )
                if response.status_code == 200:
                    return True, None
                return False, None

            # Standard HTTP REST API push
            response = self.session.post(
                self.server_url,
                json=payload_data,
                headers={"Content-Type": "application/json"},
                timeout=self.ack_timeout_sec,
            )

            if response.status_code == 200:
                res_json = response.json()

                # Check if server returned a pending command (e.g. set_fps, stop)
                incoming_cmd = None
                if "command" in res_json and res_json["command"]:
                    incoming_cmd = CommandPacket.from_json(res_json["command"])

                # Verification check: Ensure ACK returned for sequence
                ack_seq = res_json.get("ack_sequence", None)
                if self.wait_for_ack and ack_seq != packet.sequence:
                    return False, incoming_cmd

                return True, incoming_cmd
            else:
                return False, None

        except Exception as e:
            # Network timeout or disconnection handling
            return False, None
