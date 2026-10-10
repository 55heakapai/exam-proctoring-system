"""Dev seed: python -m app.seed  (creates a proctor, a student and a sample exam)."""
from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import Exam, Question, User
from .security import hash_password

Base.metadata.create_all(engine)
with SessionLocal() as db:
    if not db.scalar(select(User).where(User.email == "proctor@example.com")):
        proctor = User(email="proctor@example.com", name="Demo Proctor", role="proctor",
                       hashed_password=hash_password("proctor123"))
        student = User(email="student@example.com", name="Demo Student", role="student",
                       hashed_password=hash_password("student123"))
        db.add_all([proctor, student])
        db.flush()
        exam = Exam(title="Python Basics Quiz", duration_minutes=15, created_by=proctor.id)
        exam.questions = [
            Question(text="Which keyword defines a function in Python?", options=["func", "def", "lambda", "fn"], correct_index=1),
            Question(text="What is the output of len([1, 2, 3])?", options=["2", "3", "4", "Error"], correct_index=1),
            Question(text="Which data type is immutable?", options=["list", "dict", "tuple", "set"], correct_index=2),
            Question(text="What does HTTP status 404 mean?", options=["Server error", "Not found", "Forbidden", "Redirect"], correct_index=1),
        ]
        db.add(exam)
        db.commit()
        print("Seeded: proctor@example.com / proctor123, student@example.com / student123")
    else:
        print("Already seeded")
