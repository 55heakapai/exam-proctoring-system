from datetime import datetime

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: str = "student"


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    user: UserOut


class QuestionIn(BaseModel):
    text: str
    options: list[str] = Field(min_length=2)
    correct_index: int


class ExamIn(BaseModel):
    title: str
    duration_minutes: int = Field(default=30, ge=1, le=240)
    questions: list[QuestionIn] = Field(min_length=1)


class QuestionOut(BaseModel):  # no correct answer leaves the server
    id: int
    text: str
    options: list[str]
    model_config = {"from_attributes": True}


class ExamOut(BaseModel):
    id: int
    title: str
    duration_minutes: int
    question_count: int


class StartOut(BaseModel):
    session_id: int
    title: str
    duration_minutes: int
    remaining_seconds: int 
    questions: list[QuestionOut]


class SubmitIn(BaseModel):
    answers: dict[int, int]  # question_id -> chosen option index


class SessionOut(BaseModel):
    id: int
    exam_title: str
    student_name: str
    started_at: datetime
    ended_at: datetime | None
    score: int | None
    risk_score: int
    risk_level: str


class ViolationOut(BaseModel):
    id: int
    kind: str
    detail: str
    weight: int
    created_at: datetime
    model_config = {"from_attributes": True}
