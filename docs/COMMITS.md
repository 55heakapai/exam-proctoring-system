# Git: clean history, only your commits

## 1. Start a fresh repo (no one else's history)
The original zip has no `.git` folder, and this project is new code, so a fresh repo carries nobody else's commits.
```bash
cd examsentinel
git init -b main
git config user.name  "Your Name"
git config user.email "<id>+55heakapai@users.noreply.github.com"   # GitHub > Settings > Emails; makes commits count on your profile
git remote add origin https://github.com/55heakapai/examsentinel.git
```
**If you ever cloned the original repo** and see its commits: `git log --oneline` / `git remote -v` will show them. Remove with:
```bash
rm -rf .git && git init -b main      # then re-add your remote
git push -u --force origin main      # only on YOUR brand-new, empty repo
```
Verify: `git log --format='%an <%ae> %s'` should list only you.

## 2. Commit in real, logical steps (run the thing before each commit)
Don't backdate or fake timestamps — interviewers can read the log, and a believable history is just you committing as you understand each piece.

| # | Commit message | Add |
|---|---|---|
| 1 | `chore: init repo with gitignore` | `.gitignore` |
| 2 | `feat(backend): FastAPI app skeleton and PostgreSQL models` | `backend/app/{main,config,db,models}.py`, `requirements.txt`, `.env.example` |
| 3 | `feat(auth): JWT login/register with bcrypt and role checks` | `security.py`, `deps.py`, `schemas.py`, `routers/auth.py` |
| 4 | `feat(exams): exam CRUD, sessions, scoring, hide answers` | `routers/exams.py`, `seed.py` |
| 5 | `feat(proctor): MediaPipe face + YOLOv8 object analyzer` | `services/analyzer.py` |
| 6 | `feat(risk): violation weights, cooldown, risk levels` | `services/risk.py`, `services/violations.py` |
| 7 | `feat(ws): student stream and proctor monitor WebSockets` | `routers/ws.py`, `services/ws_manager.py` |
| 8 | `test(backend): API, websocket and detection-logic tests` | `backend/tests/`, `pytest.ini` |
| 9 | `feat(frontend): Vite + React shell, auth and routing` | `frontend/` config, `App.jsx`, `api.js`, `Login.jsx` |
| 10 | `feat(frontend): exam room with webcam streaming and tab-switch detection` | `ExamRoom.jsx`, `hooks/useProctor.js` |
| 11 | `feat(frontend): live proctor control room` | `Monitor.jsx`, `Exams.jsx`, `styles.css` |
| 12 | `docs: README with architecture and run guide` | `README.md`, `docs/` |

Then keep going with real follow-ups (each a genuine commit): exam-creation UI, head-pose/gaze via MediaPipe FaceMesh, Alembic migrations, GitHub Actions running `pytest`, screenshot/snapshot evidence on violations.
