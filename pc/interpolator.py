"""
PC High-Performance Frame Interpolation Engine
Author / Contributor: Antigravity (Google DeepMind Team)

Uses OpenCV Dense Optical Flow (Farneback) and weighted motion blending
to synthesize intermediate frames between low-FPS input frames, producing
smooth high-framerate (e.g., 30 FPS or 60 FPS) video output streams.
"""

import time
from typing import List, Optional
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


class FrameInterpolator:
    """
    High-performance Motion Interpolation Engine.
    Takes sparse low-FPS input frames (e.g. 10 FPS) and generates intermediate
    frames via optical flow motion estimation to output smooth 30/60 FPS video.
    """

    def __init__(self, target_output_fps: int = 30):
        self.target_output_fps = target_output_fps
        self.prev_frame: Optional[np.ndarray] = None
        self.prev_gray: Optional[np.ndarray] = None

    def interpolate_between(
        self,
        frame_start: np.ndarray,
        frame_end: np.ndarray,
        num_intermediates: int = 2
    ) -> List[np.ndarray]:
        """
        Generates intermediate frames between frame_start and frame_end.
        Uses Dense Optical Flow vector field mapping for realistic motion synthesis.
        """
        if cv2 is None or frame_start is None or frame_end is None:
            return [frame_start]

        if frame_start.shape != frame_end.shape:
            return [frame_start]

        intermediates = []

        try:
            # Convert to grayscale for motion estimation
            gray1 = cv2.cvtColor(frame_start, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame_end, cv2.COLOR_BGR2GRAY)

            # Compute Dense Optical Flow (Farneback algorithm)
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )

            h, w = gray1.shape
            flow_x, flow_y = flow[..., 0], flow[..., 1]
            grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))

            # Synthesize intermediate frames at fractional time steps alpha in (0, 1)
            for i in range(1, num_intermediates + 1):
                alpha = i / (num_intermediates + 1)

                # Warp map for motion compensation
                map_x = (grid_x - flow_x * alpha).astype(np.float32)
                map_y = (grid_y - flow_y * alpha).astype(np.float32)

                warped_start = cv2.remap(frame_start, map_x, map_y, cv2.INTER_LINEAR)

                # Reverse warp from end frame
                map_x_rev = (grid_x + flow_x * (1.0 - alpha)).astype(np.float32)
                map_y_rev = (grid_y + flow_y * (1.0 - alpha)).astype(np.float32)
                warped_end = cv2.remap(frame_end, map_x_rev, map_y_rev, cv2.INTER_LINEAR)

                # Blend warped frames
                blended = cv2.addWeighted(warped_start, 1.0 - alpha, warped_end, alpha, 0)
                intermediates.append(blended)

        except Exception as e:
            # High performance fallback: weighted linear blending
            for i in range(1, num_intermediates + 1):
                alpha = i / (num_intermediates + 1)
                blended = cv2.addWeighted(frame_start, 1.0 - alpha, frame_end, alpha, 0)
                intermediates.append(blended)

        return intermediates
