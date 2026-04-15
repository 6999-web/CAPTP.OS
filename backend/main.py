import os
import tempfile

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from ai_engine import engine

app = FastAPI(title="CAPTP API", version="1.0.0")

VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm")
VIDEO_SAMPLE_POINTS = (0.18, 0.42, 0.66, 0.84)

# 配置 CORS，允许 Vue 前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 方便开发，可指定 frontend 端口如 http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    scenario: str | None = None
    scenarioContext: str | None = None

def _normalize_mode(mode: str) -> str:
    normalized_mode = (mode or "").strip().upper()
    if engine.is_supported_vision_mode(normalized_mode):
        return normalized_mode

    supported_modes = ", ".join(engine.supported_vision_modes)
    raise HTTPException(status_code=400, detail=f"不支持的识别模式：{mode}。可用模式：{supported_modes}")

def _resize_frame(frame: np.ndarray, max_side: int) -> np.ndarray:
    height, width = frame.shape[:2]
    longest_side = max(height, width)
    if longest_side <= max_side:
        return frame

    scale = max_side / float(longest_side)
    resized_width = max(1, int(width * scale))
    resized_height = max(1, int(height * scale))
    return cv2.resize(frame, (resized_width, resized_height), interpolation=cv2.INTER_AREA)

def _encode_jpeg(frame: np.ndarray, quality: int) -> bytes:
    success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        raise ValueError("图像编码失败")
    return buffer.tobytes()

def _frame_focus_score(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def _build_contact_sheet(frames: list[np.ndarray], mode: str) -> bytes:
    max_side = 960 if mode == "SHOOTING_TARGET" else 720
    processed_frames = [_resize_frame(frame, max_side) for frame in frames]

    if len(processed_frames) == 1:
        quality = 94 if mode == "SHOOTING_TARGET" else 88
        return _encode_jpeg(processed_frames[0], quality)

    cell_height = max(frame.shape[0] for frame in processed_frames)
    cell_width = max(frame.shape[1] for frame in processed_frames)
    columns = 2
    rows = (len(processed_frames) + columns - 1) // columns
    gap = 10 if mode.startswith("COMBAT_") else 0
    canvas_height = rows * cell_height + max(0, rows - 1) * gap
    canvas_width = columns * cell_width + max(0, columns - 1) * gap
    canvas = np.full((canvas_height, canvas_width, 3), 8, dtype=np.uint8)

    for index, frame in enumerate(processed_frames):
        row = index // columns
        column = index % columns
        start_y = row * (cell_height + gap)
        start_x = column * (cell_width + gap)
        offset_y = start_y + (cell_height - frame.shape[0]) // 2
        offset_x = start_x + (cell_width - frame.shape[1]) // 2
        canvas[offset_y:offset_y + frame.shape[0], offset_x:offset_x + frame.shape[1]] = frame

    return _encode_jpeg(canvas, 88)

def _prepare_image_bytes(image_bytes: bytes, mode: str) -> bytes:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if frame is None:
        return image_bytes

    max_side = 1800 if mode == "SHOOTING_TARGET" else 1280
    quality = 94 if mode == "SHOOTING_TARGET" else 88
    frame = _resize_frame(frame, max_side)
    return _encode_jpeg(frame, quality)

def _extract_video_payload(video_bytes: bytes, mode: str) -> bytes:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise ValueError("无法开启视频解码流")

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        candidate_positions = [0]
        if total_frames > 0:
            candidate_positions = [max(0, int(total_frames * point)) for point in VIDEO_SAMPLE_POINTS]

        frames = []
        visited_positions = set()
        for position in candidate_positions:
            if position in visited_positions:
                continue

            visited_positions.add(position)
            capture.set(cv2.CAP_PROP_POS_FRAMES, position)
            success, frame = capture.read()
            if success and frame is not None:
                frames.append(frame)

        capture.release()

        if not frames:
            raise ValueError("无法从视频轨中捕获有效画面")

        if mode.startswith("COMBAT_"):
            return _build_contact_sheet(frames[:4], mode)

        best_frame = max(frames, key=_frame_focus_score)
        return _encode_jpeg(_resize_frame(best_frame, 1600), 92)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/analyze-vision")
async def analyze_vision(file: UploadFile = File(...), mode: str = Form("SHOOTING_POSTURE")):
    """
    分析射击 (POSTURE/TARGET/WEAPON) 或 格斗 (FIGHT/SCORING) 帧/视频。
    如果上传的是视频文件，后台将自动智能截取关键对抗帧进行分析。
    """
    normalized_mode = _normalize_mode(mode)
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="No file found")
        
    content_type = file.content_type or ""
    filename = (file.filename or "").lower()
    
    # 视频处理逻辑：格斗视频提取多帧拼图，其他视频提取最佳关键帧
    if content_type.startswith("video/") or filename.endswith(VIDEO_EXTENSIONS):
        try:
            contents = _extract_video_payload(contents, normalized_mode)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"视频解析失败: {str(e)}")
    else:
        contents = _prepare_image_bytes(contents, normalized_mode)
    
    if normalized_mode == "SHOOTING_TARGET":
        result = engine.analyze_shooting_target(contents)
    elif normalized_mode == "COMBAT_SCORING":
        result = engine.combat_quality_scoring(contents)
    else:
        result = engine.analyze_vision(contents, normalized_mode)

    if result["success"]:
        return {"result": result["data"]}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/api/tactical-chat")
async def tactical_chat(request: ChatRequest):
    """执法决策博弈推演"""
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    result = engine.tactical_chat(messages_dict, request.scenario, request.scenarioContext)
    if result["success"]:
        return {"result": result["data"]}
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# 如果直接运行此文件
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
