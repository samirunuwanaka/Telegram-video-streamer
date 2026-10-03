"""
Unit Tests for Frame Serialization Protocol & Flow Control Framing
"""

from common.protocol import FramePacket, CommandPacket

def test_frame_packet_serialization():
    payload = b"encrypted_jpeg_data"
    nonce = b"123456789012"
    
    packet = FramePacket(
        device_id="esp32_cam_01",
        sequence=42,
        encrypted_payload=payload,
        nonce=nonce,
        width=640,
        height=480,
        fps=15
    )
    
    json_str = packet.to_json()
    reconstructed = FramePacket.from_json(json_str)
    
    assert reconstructed.device_id == "esp32_cam_01"
    assert reconstructed.sequence == 42
    assert reconstructed.encrypted_payload == payload
    assert reconstructed.nonce == nonce
    assert reconstructed.fps == 15

def test_command_packet_serialization():
    cmd = CommandPacket(action="set_fps", params={"fps": 20})
    json_str = cmd.to_json()
    reconstructed = CommandPacket.from_json(json_str)
    
    assert reconstructed.action == "set_fps"
    assert reconstructed.params["fps"] == 20
