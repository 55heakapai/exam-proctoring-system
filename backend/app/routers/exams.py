from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db, require_proctor
from ..models import Exam, ExamSession, Question, User, Violation
from ..schemas import ExamIn, ExamOut, SessionOut, StartOut, SubmitIn, ViolationOut
from ..services.risk import risk_level

router = APIRouter(tags=["exams"])


def _session_out(s: ExamSession) -> SessionOut:
    return SessionOut(
        id=s.id, exam_id=s.exam_id, exam_title=s.exam.title, student_name=s.student.name,
        started_at=s.started_at, ended_at=s.ended_at, score=s.score,
        risk_score=s.risk_score, risk_level=risk_level(s.risk_score),
    )


@router.get("/exams", response_model=list[ExamOut])
def list_exams(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [
        ExamOut(id=e.id, title=e.title, duration_minutes=e.duration_minutes, question_count=len(e.questions))
        for e in db.scalars(select(Exam).order_by(Exam.id.desc()))
    ]


@router.post("/exams", response_model=ExamOut, status_code=201)
def create_exam(body: ExamIn, db: Session = Depends(get_db), user: User = Depends(require_proctor)):
    for q in body.questions:
        if not 0 <= q.correct_index < len(q.options):
            raise HTTPException(422, "correct_index out of range")
    exam = Exam(title=body.title, duration_minutes=body.duration_minutes, created_by=user.id)
    exam.questions = [Question(text=q.text, options=q.options, correct_index=q.correct_index) for q in body.questions]
    db.add(exam)
    db.commit()
    return ExamOut(id=exam.id, title=exam.title, duration_minutes=exam.duration_minutes, question_count=len(exam.questions))


@router.post("/exams/{exam_id}/start", response_model=StartOut)
def start_exam(exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "student":
        raise HTTPException(403, "Only students can take exams")
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    now = datetime.now(timezone.utc)
    total = exam.duration_minutes * 60
    sess = db.scalar(
        select(ExamSession)
        .where(ExamSession.exam_id == exam.id, ExamSession.student_id == user.id, ExamSession.ended_at.is_(None))
        .order_by(ExamSession.id.desc())
    )
    if sess:
        started = sess.started_at if sess.started_at.tzinfo else sess.started_at.replace(tzinfo=timezone.utc)
        if (now - started).total_seconds() >= total:  # time ran out: close it
            sess.ended_at, sess.score = now, 0
            sess = None
    if sess is None:
        sess = ExamSession(exam_id=exam.id, student_id=user.id)
        db.add(sess)
    db.commit()
    started = sess.started_at if sess.started_at.tzinfo else sess.started_at.replace(tzinfo=timezone.utc)
    remaining = max(0, int(total - (now - started).total_seconds()))
    return StartOut(
        session_id=sess.id, title=exam.title, duration_minutes=exam.duration_minutes,
        remaining_seconds=remaining,
        questions=[{"id": q.id, "text": q.text, "options": q.options} for q in exam.questions],
    )


@router.post("/sessions/{session_id}/submit", response_model=SessionOut)
def submit(session_id: int, body: SubmitIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sess = db.get(ExamSession, session_id)
    if not sess or sess.student_id != user.id:
        raise HTTPException(404, "Session not found")
    if sess.ended_at:
        raise HTTPException(409, "Already submitted")
    questions = {q.id: q for q in sess.exam.questions}
    sess.score = sum(1 for qid, ans in body.answers.items() if qid in questions and questions[qid].correct_index == ans)
    sess.ended_at = datetime.now(timezone.utc)
    db.commit()
    return _session_out(sess)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(ExamSession).order_by(ExamSession.id.desc()).limit(200)
    if user.role != "proctor":
        stmt = stmt.where(ExamSession.student_id == user.id)
    return [_session_out(s) for s in db.scalars(stmt)]


@router.get("/sessions/{session_id}/violations", response_model=list[ViolationOut])
def session_violations(session_id: int, db: Session = Depends(get_db), _: User = Depends(require_proctor)):
    return list(db.scalars(select(Violation).where(Violation.session_id == session_id).order_by(Violation.id)))
