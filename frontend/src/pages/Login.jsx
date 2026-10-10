import { useState } from "react";
import { api, setAuth } from "../api";

export default function Login({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", name: "", role: "student" });
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const data = await api(mode === "login" ? "/auth/login" : "/auth/register", { method: "POST", body: form });
      setAuth(data);
      onAuth(data);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-wrap">
      <form className="card login" onSubmit={submit}>
        <div className="brand"><span className="dot" />ExamSentinel</div>
        <p className="muted">Live AI-assisted exam proctoring</p>
        {mode === "register" && <input placeholder="Full name" value={form.name} onChange={set("name")} required />}
        <input placeholder="Email" type="email" value={form.email} onChange={set("email")} required />
        <input placeholder="Password (min 8 chars)" type="password" value={form.password} onChange={set("password")} required minLength={8} />
        {mode === "register" && (
          <select value={form.role} onChange={set("role")}>
            <option value="student">Student</option>
            <option value="proctor">Proctor</option>
          </select>
        )}
        {error && <div className="error">{error}</div>}
        <button className="primary">{mode === "login" ? "Sign in" : "Create account"}</button>
        <button type="button" className="ghost" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
