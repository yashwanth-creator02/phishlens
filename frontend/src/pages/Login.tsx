import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { supabase } from "../supabase";
import { Logo } from "../components/Logo";
import { usePendingAction } from "../hooks/usePendingAction";
import type { ForwardingConfig } from "../types";

type LoginProps = {
  signIn?: (email: string, password: string) => Promise<void>;
  signInAsGuest?: () => Promise<void>;
};

function getFriendlyError(err: unknown): string {
  const msg = (err as Error)?.message || String(err);
  if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || err instanceof TypeError) {
    console.error("Network/Fetch error:", err);
    return "Could not reach the server. Check that the API is running.";
  }
  return msg;
}

export default function Login({ signIn: signInProp, signInAsGuest: signInAsGuestProp }: LoginProps) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const { pending, run } = usePendingAction<"email" | "google" | "guest">();
  const [forwardingConfig, setForwardingConfig] = useState<ForwardingConfig | null | undefined>(undefined);

  useEffect(() => {
    api.forwardingConfig()
      .then((cfg) => setForwardingConfig(cfg))
      .catch(() => {
        setForwardingConfig(null);
      });
  }, []);

  const showDisabled = !supabase && !signInProp && !signInAsGuestProp;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFieldError(null);
    await run("email", async () => {
      try {
        if (signInProp) {
          await signInProp(email, password);
          nav("/");
        } else if (supabase) {
          const { error } = await supabase.auth.signInWithPassword({ email, password });
          if (error) throw new Error(error.message);
          nav("/");
        }
      } catch (err) {
        throw new Error(getFriendlyError(err));
      }
    }).catch((err) => {
      setFieldError((err as Error).message || "Sign-in failed.");
    });
  }

  async function handleGoogle() {
    setFieldError(null);
    await run("google", async () => {
      try {
        if (!supabase) return;
        const { error } = await supabase.auth.signInWithOAuth({
          provider: "google",
          options: { redirectTo: window.location.origin },
        });
        if (error) throw new Error(error.message);
      } catch (err) {
        throw new Error(getFriendlyError(err));
      }
    }).catch((err) => {
      setFieldError((err as Error).message || "Google sign-in failed.");
    });
  }

  async function handleGuest() {
    setFieldError(null);
    await run("guest", async () => {
      try {
        if (signInAsGuestProp) {
          await signInAsGuestProp();
        } else if (supabase) {
          const { error } = await supabase.auth.signInAnonymously();
          if (error) throw new Error(error.message);
        }
        nav("/");
      } catch (err) {
        throw new Error(getFriendlyError(err));
      }
    }).catch((err) => {
      setFieldError((err as Error).message || "Guest sign-in failed.");
    });
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

      {forwardingConfig === undefined ? (
        <div className="card" style={{ padding: "16px", marginBottom: "20px", marginTop: 0 }}>
          <p className="muted" style={{ fontSize: "0.85rem", margin: 0 }}>Loading forwarding configuration...</p>
        </div>
      ) : forwardingConfig ? (
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
      ) : null}

      <form className="login" onSubmit={submit} aria-busy={pending !== null} style={{ margin: 0, maxWidth: "100%" }}>
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
            disabled={pending !== null}
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
            disabled={pending !== null}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            aria-invalid={fieldError ? true : undefined}
            aria-describedby={fieldError ? "login-error" : undefined}
          />
        </div>

        <button type="submit" disabled={pending !== null} style={{ marginTop: "8px" }}>
          {pending === "email" ? "Signing in..." : "Sign in"}
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
              disabled={pending !== null}
              style={{ width: "100%" }}
            >
              {pending === "google" ? "Opening Google..." : "Continue with Google"}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={handleGuest}
              disabled={pending !== null}
              style={{ width: "100%" }}
            >
              {pending === "guest" ? "Starting guest session..." : "Try it as a guest"}
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
