from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from main import app
from schemas import AnalyzeMode
from services.pipeline import pipeline


def test_rtsp_frame_endpoint_returns_analysis_and_image(monkeypatch):
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    original_analyze_frame = pipeline.analyze_frame

    def fake_capture(url: str):
        assert url == "rtsp://demo/stream"
        return frame

    def fake_analyze_frame(frame, mode, frame_index, fps):
        assert mode == AnalyzeMode.combat_full
        return original_analyze_frame(frame=frame, mode=mode, frame_index=frame_index, fps=fps)

    monkeypatch.setattr(pipeline.video_input, "capture_rtsp_frame", fake_capture)
    monkeypatch.setattr(pipeline, "analyze_frame", fake_analyze_frame)

    client = TestClient(app)
    response = client.post(
        "/api/v2/analyze/rtsp-frame",
        json={"url": "rtsp://demo/stream", "mode": "combat_full", "frame_index": 3, "fps": 12},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["frame_b64"]
    assert payload["analysis"]["combat"]["supported_actions"]
