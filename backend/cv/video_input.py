from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np


VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm")


class VideoInputService:
    def decode_image(self, data: bytes) -> np.ndarray:
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid image input")
        return frame

    def sample_video_frames(self, data: bytes, max_frames: int = 24) -> tuple[list[np.ndarray], float]:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
            temp.write(data)
            path = Path(temp.name)

        try:
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                raise ValueError("Unable to open video stream")

            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            if total <= 0:
                indices = list(range(max_frames))
            else:
                step = max(1, total // max_frames)
                indices = list(range(0, total, step))[:max_frames]

            frames: list[np.ndarray] = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if ok and frame is not None:
                    frames.append(frame)

            cap.release()
            if not frames:
                raise ValueError("No valid frame decoded from video")

            return frames, fps
        finally:
            path.unlink(missing_ok=True)

    def infer_source_type(self, filename: str, content_type: str) -> str:
        lower = (filename or "").lower()
        if (content_type or "").startswith("video/") or lower.endswith(VIDEO_EXTENSIONS):
            return "video"
        return "image"

