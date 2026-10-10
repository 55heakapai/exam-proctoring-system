# Interview prep for this project (HackerRank tech rounds, 15-20 min)

**Be upfront:** "I started from an open-source Flask/MySQL proctoring project (MyProctor.ai) to understand the problem, then rebuilt it on FastAPI + React + PostgreSQL with WebSockets, YOLOv8 and MediaPipe." Their deck says the CTO reads commits and code and penalises exaggeration, so claim exactly what you built and can explain.

## Be able to explain without notes
1. Frame flow end-to-end: getUserMedia → canvas → JPEG → WebSocket → OpenCV decode → MediaPipe/YOLO → decision logic → DB → broadcast.
2. Why WebSockets instead of polling HTTP; why ack-based back-pressure (slow inference must not build a queue).
3. JWT: what's in the token, how WebSocket auth works (query param) and its trade-off (tokens in URLs can be logged).
4. Why inference runs in a threadpool (blocking CPU work would stall the event loop) and why MediaPipe needs a lock.
5. Why the decision logic is a pure function (testable without models).
6. False positives (laptop on desk, glasses glare) and how you'd tune: confidence, cooldown, require N consecutive frames.
7. Limits: no gaze tracking, single frame decisions, privacy/consent concerns of webcam proctoring.

## Resume bullet (accurate to this repo)
Built a real-time exam proctoring system (React, FastAPI, PostgreSQL) that streams webcam frames over WebSockets and flags multiple faces (MediaPipe), prohibited objects (YOLOv8) and tab switching, with JWT role-based auth, a live proctor dashboard and a risk-scoring model; covered by an automated pytest suite.
