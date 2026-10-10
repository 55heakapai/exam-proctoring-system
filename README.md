# ExamSentinel — Real-Time AI Exam Proctoring

A web app where students take timed exams while their webcam is analysed live, and proctors watch violations arrive on a real-time dashboard.

**Stack:** React · FastAPI · OpenCV · YOLOv8 · MediaPipe · WebSockets · PostgreSQL · JWT

## What it detects
| Violation | How | Risk weight |
|---|---|---|
| Multiple faces | MediaPipe face detection on each frame | 15 |
| No face in view | MediaPipe | 8 |
| Prohibited objects (phone, book, laptop) | YOLOv8n via Ultralytics | 20 |
| Tab / window switch | Browser `visibilitychange` event | 5 |
| Leaving fullscreen | `fullscreenchange` event | 5 |
| Copy / paste / cut | Clipboard events (blocked + logged) | 3 |

Each violation raises the session's risk score (`low` < 20 ≤ `medium` < 50 ≤ `high`). Weights live in `backend/app/services/risk.py`.

## Architecture
```
Browser (React) ──JPEG frames + events──▶ /ws/exam/{id} ─▶ OpenCV decode ─▶ MediaPipe + YOLOv8
                                                    │                         │
                                                    ▼                         ▼
                                              PostgreSQL ◀── violations ── decision logic
                                                    │
Proctor dashboard (React) ◀── /ws/monitor ◀── live broadcast
```
- **Auth:** bcrypt-hashed passwords, JWT bearer tokens, role-based access (`student` / `proctor`). WebSockets authenticate with the token and verify the session belongs to the caller.
- **Back-pressure:** the browser sends the next frame only after the server acknowledges the previous one.
- **Spam control:** per-session, per-type cooldown so one long event isn't logged dozens of times.
- **Answer safety:** correct answers never leave the server.

## Run it
```bash
# Install PostgreSQL locally, then create user and database "proctor" (password "proctor")
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed                           # demo users + sample exam
uvicorn app.main:app --reload                # http://localhost:8000/docs

cd ../frontend && cp .env.example .env && npm install && npm run dev   # http://localhost:5173
```
Demo logins (dev only): `proctor@example.com / proctor123`, `student@example.com / student123`.
The first frame triggers a one-time download of the YOLOv8n weights.

## Tests
```bash
cd backend && pytest
```
Covers auth, role checks, answer hiding, scoring, WebSocket event flow, live broadcast, risk scoring and the detection decision logic (the ML models are swapped for a fake analyzer in tests).

## Limitations / roadmap
- Detection is per-frame; no gaze or head-pose tracking yet.
- YOLOv8n false positives are possible (e.g. a laptop on a desk) — thresholds are configurable.
- No exam-creation UI yet (exams are created via the API / seed script).
- Tables are created on startup; Alembic migrations are the next step.

