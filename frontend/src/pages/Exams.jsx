import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Exams() {
  const [exams, setExams] = useState([]);
  const [sessions, setSessions] = useState([]);
  useEffect(() => {
    api("/exams").then(setExams);
    api("/sessions").then(setSessions);
  }, []);

  return (
    <>
      <h1>Available exams</h1>
      <div className="grid">
        {exams.map((e) => (
          <div className="card" key={e.id}>
            <h3>{e.title}</h3>
            <p className="muted">{e.question_count} questions · {e.duration_minutes} min</p>
           <Link className="primary btn" to={`/exam/${e.id}`}>
  {sessions.some((s) => s.exam_id === e.id && !s.ended_at) ? "Resume exam" : "Start exam"}
</Link>
          </div>
        ))}
        {!exams.length && <p className="muted">No exams yet. Ask a proctor to create one.</p>}
      </div>
      <h2>Your attempts</h2>
      <table>
        <thead><tr><th>Exam</th><th>Started</th><th>Score</th></tr></thead>
        <tbody>
          {sessions.map((s) => (
            <tr key={s.id}>
              <td>{s.exam_title}</td>
              <td>{new Date(s.started_at).toLocaleString()}</td>
              <td>{s.score ?? "in progress"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
