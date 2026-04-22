<<<<<<< HEAD
﻿from __future__ import annotations

import base64
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
=======
import os
import tempfile
>>>>>>> origin/main

import cv2
import numpy as np
import uvicorn
<<<<<<< HEAD
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from schemas import AnalyzeMode, TacticalChatRequest
from settings import settings
from services.pipeline import pipeline
from services.reference_images import resolve_reference_image
from services.shooting_training import ShootingCoachSession


DOCX_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


app = FastAPI(title="CAPTP API", version="2.0.0")
shooting_coach_sessions: dict[int, ShootingCoachSession] = {}
reference_image_resolution = resolve_reference_image()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
=======
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
>>>>>>> origin/main
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD

def _decode_data_url(data: str) -> bytes:
    if "," in data:
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


def _mode_from_legacy(mode: str) -> AnalyzeMode:
    m = (mode or "").strip().upper()
    if m in {"SHOOTING_POSTURE", "SHOOTING_WEAPON"}:
        return AnalyzeMode.shooting_posture
    if m in {"SHOOTING_TARGET", "SHOOTING_FLOW"}:
        return AnalyzeMode.shooting_flow
    if m == "COMBAT_FIGHT":
        return AnalyzeMode.combat_action
    return AnalyzeMode.combat_full


def _format_legacy_text(result) -> str:
    shooting = result.shooting
    combat = result.combat
    lines = [
        "综合评估结果",
        f"- 姿势合规: {'是' if shooting.posture_compliance else '否'} (score={shooting.posture_score:.2f})",
        f"- 射击流程阶段: {shooting.flow_stage.value}",
        f"- 流程顺序正确: {'是' if shooting.flow_order_ok else '否'}",
    ]
    if shooting.violations:
        lines.append("- 姿势/安全问题:")
        for v in shooting.violations:
            lines.append(f"  * [{v.severity}] {v.code}: {v.description}")

    if combat.actions:
        lines.append("- 格斗动作:")
        for a in combat.actions[:6]:
            lines.append(f"  * {a.action} (conf={a.confidence:.2f})")

    if combat.quartets:
        lines.append("- 格斗四元组:")
        for q in combat.quartets[:4]:
            lines.append(f"  * <{q.action} | {q.effect} | {q.reason} | {q.suggestion}>")

    lines.append(f"- 体力状态: {combat.fatigue.level} (score={combat.fatigue.score:.2f})")
    lines.append(f"- 稳定性: {combat.stability:.2f}")
    lines.append(f"- 识别人数: {result.meta.persons}, 设备: {result.meta.device}, fallback={result.meta.fallback_used}")
    if result.reasoning:
        lines.append("- 解释增强:")
        lines.append(result.reasoning)
    return "\n".join(lines)


@app.post("/api/v2/analyze/file")
async def analyze_file_v2(file: UploadFile = File(...), mode: AnalyzeMode = Form(AnalyzeMode.combat_full)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    result = pipeline.analyze_file(content=content, filename=file.filename or "", content_type=file.content_type or "", mode=mode)
    return result.model_dump()


@app.post("/api/v2/analyze/frame")
async def analyze_frame_v2(file: UploadFile = File(...), mode: AnalyzeMode = Form(AnalyzeMode.combat_full), frame_index: int = Form(0), fps: float = Form(0.0)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty frame")

    frame = pipeline.video_input.decode_image(content)
    result = pipeline.analyze_frame(frame=frame, mode=mode, frame_index=frame_index, fps=fps)
    return result.model_dump()


@app.websocket("/api/v2/stream/analyze")
async def analyze_stream_v2(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            mode = AnalyzeMode(data.get("mode", AnalyzeMode.combat_full))
            frame_b64 = data.get("frame")
            frame_index = int(data.get("frame_index", 0))
            fps = float(data.get("fps", 0.0))
            if not frame_b64:
                await websocket.send_json({"error": "missing frame"})
                continue

            frame_bytes = _decode_data_url(frame_b64)
            arr = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                await websocket.send_json({"error": "invalid frame"})
                continue

            result = pipeline.analyze_frame(frame=frame, mode=mode, frame_index=frame_index, fps=fps)
            await websocket.send_json(result.model_dump())
    except WebSocketDisconnect:
        return


@app.websocket("/api/v2/stream/shooting-coach")
async def shooting_coach_stream(websocket: WebSocket):
    await websocket.accept()
    session = ShootingCoachSession(standard_ref_url=reference_image_resolution.selected_url)
    shooting_coach_sessions[id(websocket)] = session
    try:
        await websocket.send_json({"event": "stage:update", "data": {"stage": session.machine.stage.value}})
        while True:
            packet = await websocket.receive_json()
            events = session.process_packet(packet)
            for event in events:
                await websocket.send_json(event)
    except WebSocketDisconnect:
        return
    finally:
        shooting_coach_sessions.pop(id(websocket), None)


@app.get("/api/v2/health/models")
def model_health():
    return pipeline.model_health()


@app.get("/api/v2/reference-image")
def reference_image():
    return {
        "url": reference_image_resolution.selected_url,
        "fallback_used": reference_image_resolution.fallback_used,
        "reason": reference_image_resolution.reason,
    }


# v1 compatibility
@app.post("/api/analyze-vision")
async def analyze_vision(file: UploadFile = File(...), mode: str = Form("SHOOTING_POSTURE")):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="No file found")

    result = pipeline.analyze_file(content=content, filename=file.filename or "", content_type=file.content_type or "", mode=_mode_from_legacy(mode))
    return {"result": _format_legacy_text(result)}


@app.post("/api/tactical-chat")
async def tactical_chat(request: TacticalChatRequest):
    scenario = request.scenario or "常规道路拦截盘查"
    last_user = next((m.content for m in reversed(request.messages) if m.role == "user"), "请给出处置建议")
    response = (
        f"现场反馈：基于场景【{scenario}】，你当前处置已形成初步控制。\n"
        f"处置点评：重点是先稳控再分工，避免越级接触高风险对象。\n"
        f"下一问题：在你刚才“{last_user[:40]}”这一步之后，你如何安排证据固定和通道管制的责任人？"
    )
    return {"result": response}


def _pick_case_docx() -> Path | None:
    root_dir = Path(__file__).resolve().parent.parent
    docx_files = sorted(root_dir.glob("*.docx"))
    if not docx_files:
        return None
    return docx_files[0]


def _extract_docx_lines(file_path: Path) -> list[str]:
    with zipfile.ZipFile(file_path) as archive:
        xml_bytes = archive.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    lines: list[str] = []
    for paragraph in root.findall(".//w:p", DOCX_NAMESPACE):
        pieces = [node.text or "" for node in paragraph.findall(".//w:t", DOCX_NAMESPACE)]
        merged = "".join(pieces).strip()
        if merged:
            lines.append(merged)
    return lines


def _parse_tactical_cases(lines: list[str]) -> list[dict]:
    title_pattern = re.compile(r"^\d{1,2}[\.、]\d{1,2}")
    out = []
    for idx, line in enumerate(lines):
        if title_pattern.match(line.replace(" ", "")):
            out.append({"id": f"case-{len(out)+1}", "title": line.strip(), "material": "\n".join(lines[idx + 1: idx + 6]), "questions": ["第一到场你如何口头控制现场？", "你如何进行站位和分工？", "你如何固定证据并控制升级风险？"]})
    if out:
        return out
    return [{"id": "case-1", "title": "题库案例", "material": "\n".join(lines[:8]), "questions": ["你如何做第一轮处置？"]}]


@app.get("/api/tactical-cases")
def tactical_cases():
    file_path = _pick_case_docx()
    if file_path is None:
        raise HTTPException(status_code=404, detail="题库文件未找到")

    lines = _extract_docx_lines(file_path)
    return {"source": file_path.name, "cases": _parse_tactical_cases(lines)}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "device": settings.device}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)

=======
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
>>>>>>> origin/main
