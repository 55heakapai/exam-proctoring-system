import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { useProctor } from "../hooks/useProctor";

const LABELS = {
  tab_switch: "You left the exam tab",
  multiple_faces: "More than one person is visible",
  no_face: "Your face is not visible",
  prohibited_object: "A prohibited object was detected",
  fullscreen_exit: "You left fullscreen",
  copy_paste: "Copy/paste is disabled",
};

export default function ExamRoom() {
  const { examId } = useParams();
  const videoRef = useRef(null);
  const [exam, setExam] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [error, setError] = useState("");
  const [secondsLeft, setSecondsLeft] = useState(0);

  const status = useProctor({
    sessionId: exam?.session_id,
    videoRef,
    active: !!exam && !result,
    onViolation: (v) => setWarnings((w) => [v, ...w].slice(0, 5)),
  });

  const begin = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
      videoRef.current.srcObject = stream;
      await document.documentElement.requestFullscreen?.();
      const data = await api(`/exams/${examId}/start`, { method: "POST" });
      setExam(data);
      setSecondsLeft(data.remaining_seconds);  
    } catch (e) {
      setError(e.message.includes("Permission") ? "Camera access is required to take this exam." : e.message);
    }
  };

  const submit = async () => {
    const res = await api(`/sessions/${exam.session_id}/submit`, { method: "POST", body: { answers } });
    videoRef.current?.srcObject?.getTracks().forEach((t) => t.stop());
    document.fullscreenElement && document.exitFullscreen();
    setResult(res);
  };

  useEffect(() => {
    if (!exam || result) return;
    const t = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, [exam, result]);
  useEffect(() => {
    if (exam && !result && secondsLeft <= 0) submit();
  }, [secondsLeft]);

  if (result) {
    return (
      <div className="card">
        <h1>Submitted</h1>
        <p>Your score: <b>{result.score}</b> / {exam.questions.length}</p>
      </div>
    );
  }

  return (
    <div className="room">
      <section>
        {!exam ? (
          <div className="card">
            <h1>Before you begin</h1>
            <ul className="muted">
              <li>Your webcam is analysed live while you take the exam.</li>
              <li>Keep only your face in view and stay on this tab, in fullscreen.</li>
              <li>Phones, books and other devices in view are flagged.</li>
            </ul>
            {error && <div className="error">{error}</div>}
            <button className="primary" onClick={begin}>Enable camera and start</button>
          </div>
        ) : (
          <>
            <div className="bar">
              <h1>{exam.title}</h1>
              <span className="timer">{String(Math.floor(secondsLeft / 60)).padStart(2, "0")}:{String(Math.max(secondsLeft, 0) % 60).padStart(2, "0")}</span>
            </div>
            {exam.questions.map((q, i) => (
              <div className="card q" key={q.id}>
                <b>{i + 1}. {q.text}</b>
                {q.options.map((o, idx) => (
                  <label key={idx}>
                    <input type="radio" name={`q${q.id}`} checked={answers[q.id] === idx} onChange={() => setAnswers({ ...answers, [q.id]: idx })} />
                    {o}
                  </label>
                ))}
              </div>
            ))}
            <button className="primary" onClick={submit}>Submit exam</button>
          </>
        )}
      </section>
      <aside>
        <div className="card cam">
          <video ref={videoRef} autoPlay muted playsInline />
          <div className={`pill ${status === "live" ? "ok" : ""}`}>{status === "live" ? "Proctoring active" : "Proctoring off"}</div>
        </div>
        {warnings.map((w, i) => (
          <div className="warn" key={i}>⚠ {LABELS[w.kind] || w.kind}{w.detail ? ` — ${w.detail}` : ""}</div>
        ))}
      </aside>
    </div>
  );
}
