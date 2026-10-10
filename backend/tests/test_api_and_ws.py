import uuid

from app.services.analyzer import Finding, findings_from_detections
from conftest import auth, register


def make_exam(client, proctor_token):
    r = client.post("/exams", headers=auth(proctor_token), json={
        "title": "T", "duration_minutes": 5,
        "questions": [{"text": "1+1?", "options": ["1", "2"], "correct_index": 1}],
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_auth_required_and_roles(client):
    assert client.get("/exams").status_code == 401
    student = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    r = client.post("/exams", headers=auth(student), json={"title": "x", "questions": []})
    assert r.status_code in (403, 422)


def test_wrong_password_rejected(client):
    email = f"u{uuid.uuid4().hex[:6]}@x.com"
    register(client, email, "student")
    assert client.post("/auth/login", json={"email": email, "password": "nope-nope"}).status_code == 401


def test_students_never_receive_answers(client):
    p = register(client, f"p{uuid.uuid4().hex[:6]}@x.com", "proctor")
    s = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    exam_id = make_exam(client, p)
    start = client.post(f"/exams/{exam_id}/start", headers=auth(s)).json()
    assert "correct_index" not in start["questions"][0]


def test_submit_scores_and_blocks_resubmit(client):
    p = register(client, f"p{uuid.uuid4().hex[:6]}@x.com", "proctor")
    s = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    start = client.post(f"/exams/{make_exam(client, p)}/start", headers=auth(s)).json()
    qid = start["questions"][0]["id"]
    r = client.post(f"/sessions/{start['session_id']}/submit", headers=auth(s), json={"answers": {qid: 1}})
    assert r.json()["score"] == 1
    assert client.post(f"/sessions/{start['session_id']}/submit", headers=auth(s), json={"answers": {}}).status_code == 409


def test_tab_switch_event_is_stored_and_broadcast_live(client):
    p = register(client, f"p{uuid.uuid4().hex[:6]}@x.com", "proctor")
    s = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    start = client.post(f"/exams/{make_exam(client, p)}/start", headers=auth(s)).json()
    sid = start["session_id"]
    with client.websocket_connect(f"/ws/monitor?token={p}") as mon:
        with client.websocket_connect(f"/ws/exam/{sid}?token={s}") as stu:
            stu.send_json({"event": "tab_switch", "detail": "tab hidden"})
            assert stu.receive_json()["kind"] == "tab_switch"
        live = mon.receive_json()
        assert live["kind"] == "tab_switch" and live["session_id"] == sid
    rows = client.get(f"/sessions/{sid}/violations", headers=auth(p)).json()
    assert [r["kind"] for r in rows] == ["tab_switch"]


def test_frame_findings_become_violations_and_raise_risk(client):
    p = register(client, f"p{uuid.uuid4().hex[:6]}@x.com", "proctor")
    s = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    start = client.post(f"/exams/{make_exam(client, p)}/start", headers=auth(s)).json()
    sid = start["session_id"]
    client.app.state.analyzer.next = [Finding("multiple_faces", "2 faces detected"), Finding("prohibited_object", "cell phone")]
    with client.websocket_connect(f"/ws/exam/{sid}?token={s}") as stu:
        stu.send_bytes(b"fake-jpeg")
        kinds = [stu.receive_json()["kind"], stu.receive_json()["kind"]]
        assert stu.receive_json()["type"] == "ack"
    assert kinds == ["multiple_faces", "prohibited_object"]
    sessions = client.get("/sessions", headers=auth(p)).json()
    assert next(x for x in sessions if x["id"] == sid)["risk_score"] == 35


def test_ws_rejects_other_students_and_bad_tokens(client):
    p = register(client, f"p{uuid.uuid4().hex[:6]}@x.com", "proctor")
    s1 = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    s2 = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    sid = client.post(f"/exams/{make_exam(client, p)}/start", headers=auth(s1)).json()["session_id"]
    for tok in (s2, "garbage"):
        try:
            with client.websocket_connect(f"/ws/exam/{sid}?token={tok}") as ws:
                ws.receive_json()
            assert False, "should have been rejected"
        except Exception:
            pass


def test_detection_decision_logic():
    assert [f.kind for f in findings_from_detections(0, [])] == ["no_face"]
    assert [f.kind for f in findings_from_detections(1, [])] == []
    assert [f.kind for f in findings_from_detections(2, [])] == ["multiple_faces"]
    got = findings_from_detections(1, ["person", "cell phone", "cell phone", "chair"])
    assert [(f.kind, f.detail) for f in got] == [("prohibited_object", "cell phone")]

def test_start_resumes_unfinished_attempt(client):
    p = register(client, f"p{uuid.uuid4().hex[:6]}@x.com", "proctor")
    s = register(client, f"s{uuid.uuid4().hex[:6]}@x.com", "student")
    exam_id = make_exam(client, p)
    first = client.post(f"/exams/{exam_id}/start", headers=auth(s)).json()
    again = client.post(f"/exams/{exam_id}/start", headers=auth(s)).json()
    assert again["session_id"] == first["session_id"]
    assert 0 < again["remaining_seconds"] <= 300
    qid = first["questions"][0]["id"]
    client.post(f"/sessions/{first['session_id']}/submit", headers=auth(s), json={"answers": {qid: 1}})
    fresh = client.post(f"/exams/{exam_id}/start", headers=auth(s)).json()
    assert fresh["session_id"] != first["session_id"]