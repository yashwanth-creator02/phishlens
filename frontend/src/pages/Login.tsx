import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabase";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"in" | "up">("in");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!supabase) {
    return (
      <div className="card" style={{ maxWidth: "400px", margin: "80px auto", textAlign: "center", padding: "32px" }}>
        <h1>Authentication disabled</h1>
        <p className="muted" style={{ marginTop: "12px" }}>
          Authentication is disabled in this environment (local development mode with <code className="mono">AUTH_MODE=disabled</code>).
        </p>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      const res = mode === "in"
        ? await supabase!.auth.signInWithPassword({ email, password })
        : await supabase!.auth.signUp({ email, password });
      if (res.error) {
        setMsg(res.error.message);
      } else if (mode === "up" && !res.data.session) {
        setMsg("Check your inbox to confirm your email address, then sign in.");
      } else {
        nav("/");
      }
    } catch (err) {
      setMsg((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="login" onSubmit={submit}>
      <h1>{mode === "in" ? "Analyst sign in" : "Create account"}</h1>
      <p className="muted" style={{ fontSize: "0.9rem", marginTop: "-4px" }}>
        {mode === "in" ? "Enter your credentials to access triage queues." : "Register a new analyst account."}
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <label htmlFor="email-input" style={{ fontSize: "0.85rem", fontWeight: 500 }}>Email address</label>
        <input
          id="email-input"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="analyst@domain.com"
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        <label htmlFor="password-input" style={{ fontSize: "0.85rem", fontWeight: 500 }}>Password</label>
        <input
          id="password-input"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
      </div>

      <button type="submit" disabled={busy} style={{ marginTop: "8px" }}>
        {busy ? "Processing..." : mode === "in" ? "Sign in" : "Create account"}
      </button>

      <div style={{ textAlign: "center", marginTop: "12px" }}>
        <button
          type="button"
          className="link"
          onClick={() => setMode(mode === "in" ? "up" : "in")}
        >
          {mode === "in" ? "Need an account? Sign up" : "Have an account? Sign in"}
        </button>
      </div>

      {msg && <p className="error" role="alert" style={{ marginTop: "12px", textAlign: "center", fontSize: "0.9rem" }}>{msg}</p>}
    </form>
  );
}
