import json
import time

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from ..config import settings
from ..db import SessionLocal
from ..models import ExamSession, User
from ..security import decode_token
from ..services.analyzer import Finding
from ..services.risk import CLIENT_EVENTS
from ..services.violations import record_violation
from ..services.ws_manager import hub

router = APIRouter()


@router.websocket("/ws/exam/{session_id}")
async def exam_stream(ws: WebSocket, session_id: int, token: str = Query(...)):
    """Student channel. Binary messages = JPEG frames, text messages = browser events."""
    payload = decode_token(token)
    if not payload:
        await ws.close(code=4401)
        return
    with SessionLocal() as db:
        sess = db.get(ExamSession, session_id)
        user = db.get(User, int(payload["sub"]))
        if not sess or not user or sess.student_id != user.id or sess.ended_at:
            await ws.close(code=4403)
            return
        student_name = user.name
    await ws.accept()

    analyzer = ws.app.state.analyzer
    last_sent: dict[str, float] = {}  # per-kind cooldown so one long event isn't logged 40 times

    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            findings: list[Finding] = []
            is_frame = bool(msg.get("bytes"))
            if is_frame:
                findings = await run_in_threadpool(analyzer.analyze, msg["bytes"])
            elif msg.get("text"):
                try:
                    data = json.loads(msg["text"])
                except json.JSONDecodeError:
                    continue
                if data.get("event") in CLIENT_EVENTS:
                    findings = [Finding(data["event"], str(data.get("detail", "")))]

            for f in findings:
                now = time.monotonic()
                if now - last_sent.get(f.kind, -1e9) < settings.violation_cooldown_seconds:
                    continue
                last_sent[f.kind] = now
                with SessionLocal() as db:
                    v, risk, level = record_violation(db, session_id, f.kind, f.detail)
                event = {
                    "type": "violation", "session_id": session_id, "student": student_name,
                    "kind": v.kind, "detail": v.detail, "weight": v.weight,
                    "risk_score": risk, "risk_level": level, "at": v.created_at.isoformat(),
                }
                await ws.send_json(event)  # the student sees a warning too
                await hub.broadcast(event)  # and the proctors see it live
            if is_frame:
                await ws.send_json({"type": "ack"})
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/monitor")
async def monitor(ws: WebSocket, token: str = Query(...)):
    """Proctor channel: receives every violation event from every live session."""
    payload = decode_token(token)
    if not payload or payload.get("role") != "proctor":
        await ws.close(code=4401)
        return
    await hub.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; the client sends nothing meaningful
    except WebSocketDisconnect:
        hub.disconnect(ws)
