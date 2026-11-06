import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../supabase";

type LoginProps = {
  signIn?: (email: string, password: string) => Promise<void>;
};

export default function Login({ signIn: signInProp }: LoginProps) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Show the disabled banner only in production with no supabase and no injected signIn.
  // In dev/tests, the form renders so signIn prop and supabase can be exercised.
  const showDisabled = !supabase && !signInProp;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFieldError(null);
    setBusy(true);
    try {
      if (signInProp) {
        await signInProp(email, password);
        nav("/");
      } else if (supabase) {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          throw new Error(error.message);
        }
        nav("/");
      }
    } catch (err) {
      setFieldError((err as Error).message || "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  if (showDisabled) {
    return (
      <div className="card" style={{ maxWidth: "400px", margin: "80px auto", textAlign: "center", padding: "32px" }}>
        <h1>Authentication disabled</h1>
        <p className="muted" style={{ marginTop: "12px" }}>
          Authentication is disabled in this environment (local development mode with <code className="mono">AUTH_MODE=disabled</code>).
        </p>
      </div>
    );
  }

  return (
    <form className="login" onSubmit={submit}>
      <h1>Analyst sign in</h1>
      <p className="muted" style={{ fontSize: "0.9rem", marginTop: "-4px" }}>
        Enter your credentials to access triage queues.
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
          aria-invalid={fieldError ? true : undefined}
          aria-describedby={fieldError ? "login-error" : undefined}
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
          aria-invalid={fieldError ? true : undefined}
          aria-describedby={fieldError ? "login-error" : undefined}
        />
      </div>

      <button type="submit" disabled={busy} style={{ marginTop: "8px" }}>
        {busy ? "Processing..." : "Sign in"}
      </button>

      {fieldError && <p className="error" role="alert" id="login-error" style={{ marginTop: "12px", textAlign: "center", fontSize: "0.9rem" }}>{fieldError}</p>}
    </form>
  );
}
