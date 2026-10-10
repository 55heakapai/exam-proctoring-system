import { useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { clearAuth, getAuth } from "./api";
import Login from "./pages/Login.jsx";
import Exams from "./pages/Exams.jsx";
import ExamRoom from "./pages/ExamRoom.jsx";
import Monitor from "./pages/Monitor.jsx";

export default function App() {
  const [auth, setAuthState] = useState(getAuth());
  const nav = useNavigate();
  const logout = () => {
    clearAuth();
    setAuthState(null);
    nav("/login");
  };

  if (!auth) {
    return (
      <Routes>
        <Route path="*" element={<Login onAuth={setAuthState} />} />
      </Routes>
    );
  }
  const home = auth.user.role === "proctor" ? "/monitor" : "/exams";
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand"><span className="dot" />ExamSentinel</div>
        <nav>
          {auth.user.role === "proctor" ? <Link to="/monitor">Control room</Link> : <Link to="/exams">My exams</Link>}
        </nav>
        <div className="who">
          <div>{auth.user.name}</div>
          <small>{auth.user.role}</small>
          <button className="ghost" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/exams" element={<Exams />} />
          <Route path="/exam/:examId" element={<ExamRoom />} />
          <Route path="/monitor" element={<Monitor />} />
          <Route path="*" element={<Navigate to={home} replace />} />
        </Routes>
      </main>
    </div>
  );
}
