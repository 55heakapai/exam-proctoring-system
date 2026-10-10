import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["VIOLATION_COOLDOWN_SECONDS"] = "0"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.analyzer import Finding


class FakeAnalyzer:
    def __init__(self):
        self.next = []

    def analyze(self, jpeg: bytes):
        return self.next


@pytest.fixture()
def client():
    app.state.analyzer = FakeAnalyzer()
    with TestClient(app) as c:
        yield c


def register(client, email, role):
    r = client.post("/auth/register", json={"email": email, "name": email.split("@")[0], "password": "password123", "role": role})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
