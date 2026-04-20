from __future__ import annotations

import base64
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import uvicorn
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

