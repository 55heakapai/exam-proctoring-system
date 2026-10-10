from sqlalchemy.orm import Session

from ..models import ExamSession, Violation
from .risk import WEIGHTS, risk_level


def record_violation(db: Session, session_id: int, kind: str, detail: str = "") -> tuple[Violation, int, str]:
    sess = db.get(ExamSession, session_id)
    weight = WEIGHTS.get(kind, 1)
    v = Violation(session_id=session_id, kind=kind, detail=detail[:255], weight=weight)
    sess.risk_score += weight
    db.add(v)
    db.commit()
    return v, sess.risk_score, risk_level(sess.risk_score)
