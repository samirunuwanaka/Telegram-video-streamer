"""
PC Stream API Server (FastAPI)
Provides REST & MJPEG Video Streaming Endpoints for External Programs.
Allows external applications to:
1. Read decrypted video stream & latest frames.
2. Control ESP32 frame rate (FPS).
3. Start / Stop streaming.
"""

import asyncio
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from common.protocol import FramePacket, CommandPacket
from common.messages import ACTION_START_STREAM, ACTION_STOP_STREAM, ACTION_SET_FPS
from pc.receiver import StreamReceiver

# Initialize FastAPI App & Stream Receiver Engine
app = FastAPI(
    title="Telegram Local Video Streamer API",
    description="API for reading decrypted ESP32 video streams and controlling frame rates dynamically.",
    version="1.0.0",
)

# Global Stream Receiver Singleton
receiver_engine = StreamReceiver()


# Pydantic Request Models
class FpsControlRequest(BaseModel):
    fps: int


class StreamControlRequest(BaseModel):
    action: str  # "start" or "stop"


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Telegram Local Video AI Streamer API",
        "endpoints": {
            "stream_feed": "/api/v1/stream/feed",
            "latest_frame": "/api/v1/stream/frame",
            "stream_status": "/api/v1/stream/status",
            "control_fps": "/api/v1/control/fps",
            "control_stream": "/api/v1/control/stream",
        }
    }


# ==============================================================================
# 1. BITSTREAM INGESTION ENDPOINT (Called by ESP32 Uploader)
# ==============================================================================
@app.post("/api/v1/stream/push")
async def push_frame(packet_dict: Dict[str, Any]):
    """
    Ingests encrypted frame packet from ESP32.
    Implements stop-and-wait flow control: Returns ACK sequence & pending commands.
    """
    try:
        packet = FramePacket.from_dict(packet_dict)
        ack_response = receiver_engine.process_packet(packet)
        return JSONResponse(content=ack_response, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid stream packet: {str(e)}")


# ==============================================================================
# 2. DATA STREAM READ ENDPOINTS (For External Applications / Clients)
# ==============================================================================
@app.get("/api/v1/stream/frame")
async def get_latest_frame(upscaled: bool = True):
    """
    Returns the latest decrypted JPEG frame for external applications to read.
    """
    jpeg_bytes = receiver_engine.get_latest_jpeg(use_upscaled=upscaled)
    if not jpeg_bytes:
        raise HTTPException(status_code=404, detail="No active stream frame available")

    return Response(content=jpeg_bytes, media_type="image/jpeg")


async def generate_mjpeg_stream():
    """
    Generator for multipart MJPEG video feed.
    """
    while True:
        jpeg_bytes = receiver_engine.get_latest_jpeg(use_upscaled=True)
        if jpeg_bytes:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
        await asyncio.sleep(0.05)


@app.get("/api/v1/stream/feed")
async def video_feed():
    """
    Continuous MJPEG video stream feed API.
    Can be opened directly in OpenCV, VLC, web browser, or Python scripts.
    """
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/v1/stream/status")
async def get_stream_status():
    """
    Returns current stream state, device ID, sequence number, and FPS.
    """
    return receiver_engine.get_status()


# ==============================================================================
# 3. CONTROL ENDPOINTS (Set Frame Rate & Start/Stop Stream)
# ==============================================================================
@app.post("/api/v1/control/fps")
async def set_frame_rate(req: FpsControlRequest):
    """
    Sets the target frame rate (FPS) of the embedded ESP32 device dynamically.
    The new FPS command is delivered to the device on the next frame ACK token.
    """
    if req.fps < 1 or req.fps > 30:
        raise HTTPException(status_code=400, detail="FPS must be between 1 and 30")

    cmd = CommandPacket(action=ACTION_SET_FPS, params={"fps": req.fps})
    receiver_engine.set_pending_command(cmd)
    receiver_engine.current_fps = req.fps

    return {
        "status": "success",
        "message": f"Frame rate command set to {req.fps} FPS. Pending delivery to device.",
        "target_fps": req.fps
    }


@app.post("/api/v1/control/stream")
async def control_stream(req: StreamControlRequest):
    """
    Starts or stops streaming on the embedded device.
    """
    action_str = req.action.lower()
    if action_str not in ["start", "stop"]:
        raise HTTPException(status_code=400, detail="Action must be 'start' or 'stop'")

    target_action = ACTION_START_STREAM if action_str == "start" else ACTION_STOP_STREAM
    cmd = CommandPacket(action=target_action)
    receiver_engine.set_pending_command(cmd)
    receiver_engine.is_streaming = (action_str == "start")

    return {
        "status": "success",
        "message": f"Stream control action '{action_str}' issued to device.",
        "is_streaming": receiver_engine.is_streaming
    }
