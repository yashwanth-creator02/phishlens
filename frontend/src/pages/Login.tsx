import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { supabase } from "../supabase";
import { Logo } from "../components/Logo";
import type { ForwardingConfig } from "../types";

type LoginProps = {
  signIn?: (email: string, password: string) => Promise<void>;
  signInAsGuest?: () => Promise<void>;
};

export default function Login({ signIn: signInProp, signInAsGuest: signInAsGuestProp }: LoginProps) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [forwardingConfig, setForwardingConfig] = useState<ForwardingConfig | null>(null);

  useEffect(() => {
    api.forwardingConfig()
      .then((cfg) => setForwardingConfig(cfg))
      .catch(() => {
        setForwardingConfig(null);
      });
  }, []);

  // Show the disabled banner only in production with no supabase and no injected signIn.
  // In dev/tests, the form renders so signIn prop and supabase can be exercised.
  const showDisabled = !supabase && !signInProp && !signInAsGuestProp;

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

  async function handleGoogle() {
    setFieldError(null);
    try {
      if (!supabase) return;
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: window.location.origin },
      });
      if (error) {
        throw new Error(error.message);
      }
    } catch (err) {
      setFieldError((err as Error).message || "Google sign-in failed.");
    }
  }

  async function handleGuest() {
    setFieldError(null);
    setBusy(true);
    try {
      if (signInAsGuestProp) {
        await signInAsGuestProp();
      } else if (supabase) {
        const { error } = await supabase.auth.signInAnonymously();
        if (error) {
          throw new Error(error.message);
        }
      }
      nav("/");
    } catch (err) {
      setFieldError((err as Error).message || "Guest sign-in failed.");
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
    <div style={{ maxWidth: "380px", margin: "40px auto" }}>
      <div style={{ textAlign: "center", marginBottom: "20px" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <Logo size={32} />
          <h1 style={{ margin: 0, fontSize: "1.5rem", letterSpacing: "-0.02em" }}>PhishLens</h1>
        </div>
        <span className="brand-subtitle" style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", letterSpacing: "0.02em" }}>
          Explainable phishing-triage console
        </span>
        <p className="muted" style={{ fontSize: "0.9rem", marginTop: "10px", lineHeight: "1.4" }}>
          An explainable phishing-triage tool. Analysts forward suspicious emails to receive a Low, Medium, or High risk score with evidence-verified reasons.
        </p>
      </div>

      {forwardingConfig && (
        <div className="card" role="region" aria-labelledby="forwarding-info-heading" style={{ padding: "16px", marginBottom: "20px", marginTop: 0 }}>
          <h2 id="forwarding-info-heading" style={{ marginTop: 0, fontSize: "0.95rem" }}>Forwarding inbox</h2>
          <p className="muted" style={{ fontSize: "0.85rem", margin: "4px 0" }}>
            Domain: <span className="mono">{forwardingConfig.alias_domain}</span> (Pattern: <span className="mono">{forwardingConfig.alias_pattern}</span>)
          </p>
          <p className="muted" style={{ fontSize: "0.85rem", margin: "4px 0" }}>
            Your own address appears on your Profile once you sign in.
          </p>
          {!forwardingConfig.inbound_configured && (
            <p className="error" style={{ fontSize: "0.85rem", margin: "8px 0 0" }}>
              Inbound forwarding is not connected yet.
            </p>
          )}
        </div>
      )}

      <form className="login" onSubmit={submit} style={{ margin: 0, maxWidth: "100%" }}>
        <h2>Analyst sign in</h2>
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

        {supabase && (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "8px 0" }}>
              <div style={{ flex: 1, height: "1px", background: "var(--line)" }} />
              <span className="muted" style={{ fontSize: "0.80rem" }}>or</span>
              <div style={{ flex: 1, height: "1px", background: "var(--line)" }} />
            </div>
            <button
              type="button"
              className="secondary"
              onClick={handleGoogle}
              style={{ width: "100%" }}
            >
              Continue with Google
            </button>
            <button
              type="button"
              className="secondary"
              onClick={handleGuest}
              disabled={busy}
              style={{ width: "100%" }}
            >
              Try it as a guest
            </button>
            <p className="muted" style={{ fontSize: "0.8rem", textAlign: "center", margin: "4px 0 0" }}>
              A guest can upload emails and use the whole triage flow, but has no forwarding address, because a forwarding address belongs to a confirmed email account.
            </p>
          </>
        )}

        {fieldError && <p className="error" role="alert" id="login-error" style={{ marginTop: "12px", textAlign: "center", fontSize: "0.9rem" }}>{fieldError}</p>}
      </form>
    </div>
  );
}
