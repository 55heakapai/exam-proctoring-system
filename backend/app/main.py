from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routers import auth, exams, ws
from .services.analyzer import FrameAnalyzer


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if not hasattr(app.state, "analyzer"):  # tests inject a fake before startup
        app.state.analyzer = FrameAnalyzer()
    yield


app = FastAPI(title="ExamSentinel API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(exams.router)
app.include_router(ws.router)


@app.get("/health")
def health():
    return {"status": "ok"}
