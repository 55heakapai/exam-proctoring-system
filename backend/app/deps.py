from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(creds.credentials) if creds else None
    user = db.get(User, int(payload["sub"])) if payload else None
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing token")
    return user


def require_proctor(user: User = Depends(get_current_user)) -> User:
    if user.role != "proctor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Proctor access only")
    return user
