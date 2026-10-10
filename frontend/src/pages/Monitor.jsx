import { useEffect, useState } from "react";
import { WS_BASE, api, getToken } from "../api";

export default function Monitor() {
  const [sessions, setSessions] = useState([]);
  const [feed, setFeed] = useState([]);
  const [live, setLive] = useState(false);

  useEffect(() => {
    api("/sessions").then(setSessions);
    const ws = new WebSocket(`${WS_BASE}/ws/monitor?token=${getToken()}`);
    ws.onopen = () => setLive(true);
    ws.onclose = () => setLive(false);
    const ping = setInterval(() => ws.readyState === 1 && ws.send("ping"), 20000);
    ws.onmessage = (e) => {
      const v = JSON.parse(e.data);
      setFeed((f) => [v, ...f].slice(0, 50));
      setSessions((list) => {
        if (!list.some((s) => s.id === v.session_id)) {
          api("/sessions").then(setSessions);
          return list;
        }
        return list.map((s) => (s.id === v.session_id ? { ...s, risk_score: v.risk_score, risk_level: v.risk_level } : s));
      });
    };
    return () => { clearInterval(ping); ws.close(); };
  }, []);

  const active = sessions.filter((s) => !s.ended_at);
  const flagged = sessions.filter((s) => s.risk_level === "high").length;

  return (
    <>
      <div className="bar">
        <h1>Control room</h1>
        <div className={`pill ${live ? "ok" : ""}`}>{live ? "Live" : "Reconnecting…"}</div>
      </div>
      <div className="stats">
        <div className="card stat"><b>{active.length}</b><small>Exams in progress</small></div>
        <div className="card stat"><b>{flagged}</b><small>High-risk sessions</small></div>
        <div className="card stat"><b>{feed.length}</b><small>Events this visit</small></div>
      </div>
      <div className="two">
        <div>
          <h2>Sessions</h2>
          <table>
            <thead><tr><th>Student</th><th>Exam</th><th>Status</th><th>Risk</th></tr></thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id}>
                  <td>{s.student_name}</td>
                  <td>{s.exam_title}</td>
                  <td>{s.ended_at ? "submitted" : "live"}</td>
                  <td><span className={`risk ${s.risk_level}`}>{s.risk_score} · {s.risk_level}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h2>Live feed</h2>
          <div className="feed">
            {feed.map((v, i) => (
              <div className={`event ${v.risk_level}`} key={i}>
                <b>{v.student}</b> · {v.kind.replace("_", " ")}
                {v.detail && <small> — {v.detail}</small>}
                <small>{new Date(v.at).toLocaleTimeString()}</small>
              </div>
            ))}
            {!feed.length && <p className="muted">Waiting for events…</p>}
          </div>
        </div>
      </div>
    </>
  );
}
