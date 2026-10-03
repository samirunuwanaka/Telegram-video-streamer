"""
Thread-safe Message and Frame Queue Management for Telegram Bot
"""

import queue
import time
from typing import Optional, Dict, Any


class BotQueue:
    """
    Queue system for streaming frames and Telegram messages with size limits and flow control.
    """

    def __init__(self, maxsize: int = 50):
        self.frame_queue = queue.Queue(maxsize=maxsize)

    def put_frame(self, frame_data: Dict[str, Any]) -> bool:
        """
        Adds a frame packet dictionary to the queue.
        If queue is full, drops oldest frame (ring buffer behavior) to avoid latency accumulation.
        """
        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self.frame_queue.put_nowait(frame_data)
            return True
        except queue.Full:
            return False

    def get_frame(self, timeout: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Retrieves next frame from queue.
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
