import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabase";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"in" | "up">("in");
  const [msg, setMsg] = useState<string | null>(null);

  if (!supabase) {
    return <p className="muted">Authentication is disabled in this environment (local development).</p>;
  }

  async function submit() {
    setMsg(null);
    const res = mode === "in"
      ? await supabase!.auth.signInWithPassword({ email, password })
      : await supabase!.auth.signUp({ email, password });
    if (res.error) setMsg(res.error.message);
    else if (mode === "up" && !res.data.session) setMsg("Check your inbox to confirm your email, then sign in.");
    else nav("/");
  }

  return (
    <div className="login">
      <h1>{mode === "in" ? "Sign in" : "Create account"}</h1>
      <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={() => void submit()}>{mode === "in" ? "Sign in" : "Sign up"}</button>
      <button className="link" onClick={() => setMode(mode === "in" ? "up" : "in")}>
        {mode === "in" ? "Need an account? Sign up" : "Have an account? Sign in"}
      </button>
      {msg && <p className="error">{msg}</p>}
    </div>
  );
}
