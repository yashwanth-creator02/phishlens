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
  signUp?: (email: string, password: string) => Promise<void>;
};

function getFriendlyError(err: unknown): string {
  const msg = (err as Error)?.message || String(err);
  if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || err instanceof TypeError) {
    console.error("Network/Fetch error:", err);
    return "Could not reach the server. Check that the API is running.";
  }
  return msg;
}

export default function Login({ signIn: signInProp, signInAsGuest: signInAsGuestProp, signUp: signUpProp }: LoginProps) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [signUpSuccess, setSignUpSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { pending, run } = usePendingAction<"email" | "google" | "guest">();
  const [forwardingConfig, setForwardingConfig] = useState<ForwardingConfig | null | undefined>(undefined);
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem("phishlens-dismiss-forwarding") === "true";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    api.forwardingConfig()
      .then((cfg) => setForwardingConfig(cfg))
      .catch(() => {
        setForwardingConfig(null);
      });
  }, []);

  const dismissForwarding = () => {
    setDismissed(true);
    try {
      sessionStorage.setItem("phishlens-dismiss-forwarding", "true");
    } catch {
      /* ignore */
    }
  };

  const showDisabled = !supabase && !signInProp && !signInAsGuestProp && !signUpProp;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFieldError(null);
    setSignUpSuccess(false);
    await run("email", async () => {
      try {
        if (mode === "signup") {
          if (signUpProp) {
            await signUpProp(email, password);
          } else if (supabase) {
            const { data, error } = await supabase.auth.signUp({ email, password });
            if (error) throw new Error(error.message);
            if (!data.session) {
              setSignUpSuccess(true);
              return;
            }
          }
          nav("/");
        } else {
          if (signInProp) {
            await signInProp(email, password);
          } else if (supabase) {
            const { error } = await supabase.auth.signInWithPassword({ email, password });
            if (error) throw new Error(error.message);
          }
          nav("/");
        }
      } catch (err) {
        throw new Error(getFriendlyError(err));
      }
    }).catch((err) => {
      setFieldError((err as Error).message || "Action failed.");
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
    <div className="login-layout">
      {/* LEFT: Brand & Capabilities Hero */}
      <div className="login-hero">
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "12px", marginBottom: "8px" }}>
            <Logo size={40} />
            <h1 style={{ margin: 0, fontSize: "2.25rem", letterSpacing: "-0.03em" }}>PhishLens</h1>
          </div>
          <span className="brand-subtitle" style={{ display: "block", fontSize: "0.95rem", color: "var(--accent)", letterSpacing: "0.02em", marginBottom: "16px", fontWeight: 500, textAlign: "center" }}>
            Explainable phishing-triage console
          </span>
          <p className="muted" style={{ fontSize: "1rem", lineHeight: "1.6", maxWidth: "46ch", margin: "0 auto", textAlign: "center" }}>
            Upload or forward suspicious emails to receive calibrated risk scoring, multi-vector feature extraction across 65 signals, and evidence-verified SHAP reasons.
          </p>
        </div>

        <div className="login-features-list">
          <div className="login-feature-item">
            <div className="login-feature-icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div className="login-feature-text">
              <h3>65-Feature Multi-Vector Analysis</h3>
              <p>Header authentication, URL lexical depth, NLP semantics, and sender behavioral profiles.</p>
            </div>
          </div>

          <div className="login-feature-item">
            <div className="login-feature-icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 11 12 14 22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
            </div>
            <div className="login-feature-text">
              <h3>Evidence-Verified Reasons</h3>
              <p>SHAP attributions cross-checked against raw message artifacts to eliminate false claims.</p>
            </div>
          </div>

          <div className="login-feature-item">
            <div className="login-feature-icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 14 14" />
              </svg>
            </div>
            <div className="login-feature-text">
              <h3>Calibrated Three-Tier Triage</h3>
              <p>Low, Medium, and High probability-calibrated bands designed for rapid analyst workflow.</p>
            </div>
          </div>
        </div>

        <div className="login-trust-badges">
          <span className="login-trust-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" />
            </svg>
            Zero-execution sandbox
          </span>
          <span className="login-trust-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 01-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 011-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 011.52 0C14.51 3.81 17 5 19 5a1 1 0 011 1z" />
            </svg>
            Strict RLS tenant isolation
          </span>
        </div>
      </div>

      {/* RIGHT: Form & Floating Notification */}
      <div>
        <form className="login" onSubmit={submit} aria-busy={pending !== null} style={{ margin: 0, maxWidth: "100%" }}>
          {mode === "signup" && (
            <button
              type="button"
              className="link back-button"
              onClick={() => { setMode("signin"); setSignUpSuccess(false); setFieldError(null); }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                alignSelf: "flex-start",
                justifyContent: "flex-start",
                gap: "6px",
                marginBottom: "8px",
                padding: 0,
                fontSize: "0.85rem",
                color: "var(--muted)",
                cursor: "pointer",
                background: "transparent",
                border: "none",
                textAlign: "left",
                width: "fit-content",
              }}
              aria-label="Back to sign in"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
              Back to sign in
            </button>
          )}

          <h2>{mode === "signin" ? "Analyst sign in" : "Create an account"}</h2>
          <p className="muted" style={{ fontSize: "0.9rem", marginTop: "-4px" }}>
            {mode === "signin" ? "Enter your credentials to access triage queues." : "Register a new analyst account with your email."}
          </p>

          {signUpSuccess && (
            <div className="card low" style={{ padding: "12px 16px", margin: "0 0 12px 0" }}>
              <p style={{ margin: 0, fontWeight: 500, fontSize: "0.9rem" }}>Check your email to confirm the address, then sign in.</p>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <label htmlFor="email-input" style={{ fontSize: "0.85rem", fontWeight: 500 }}>Email address</label>
            <input
              id="email-input"
              name="email"
              type="email"
              autoComplete="email"
              autoCapitalize="none"
              spellCheck={false}
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
            <div style={{ position: "relative", display: "flex" }}>
              <input
                id="password-input"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                required
                disabled={pending !== null}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                aria-invalid={fieldError ? true : undefined}
                aria-describedby={fieldError ? "login-error" : undefined}
                style={{ paddingRight: "44px" }}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((v) => !v)}
                disabled={pending !== null}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
              >
                {showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 3l18 18" />
                    <path d="M10.6 10.6a2 2 0 002.8 2.8" />
                    <path d="M9.4 5.3A9.7 9.7 0 0112 5c5 0 9 4.5 9 7a12.6 12.6 0 01-3.2 4.1" />
                    <path d="M6.2 6.7A12.8 12.8 0 003 12c0 2.5 4 7 9 7 1.6 0 3.1-.5 4.4-1.3" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 12c0-2.5 4-7 9-7s9 4.5 9 7-4 7-9 7-9-4.5-9-7z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <button type="submit" disabled={pending !== null} style={{ marginTop: "8px" }}>
            {pending === "email" ? (mode === "signin" ? "Signing in..." : "Creating account...") : (mode === "signin" ? "Sign in" : "Create account")}
          </button>

          <div style={{ textAlign: "center", marginTop: "4px" }}>
            {mode === "signin" ? (
              <button
                type="button"
                className="link"
                onClick={() => { setMode("signup"); setSignUpSuccess(false); setFieldError(null); }}
              >
                Create an account
              </button>
            ) : (
              <button
                type="button"
                className="link"
                onClick={() => { setMode("signin"); setSignUpSuccess(false); setFieldError(null); }}
              >
                Sign in to an existing account
              </button>
            )}
          </div>

          {supabase && mode === "signin" && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", margin: "4px 0" }}>
                <div style={{ flex: 1, height: "1px", background: "var(--line)" }} />
                <span className="muted" style={{ fontSize: "0.80rem" }}>or</span>
                <div style={{ flex: 1, height: "1px", background: "var(--line)" }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <button
                  type="button"
                  className="secondary"
                  onClick={handleGoogle}
                  disabled={pending !== null}
                  aria-label={pending === "google" ? "Opening Google..." : "Continue with Google"}
                  style={{ width: "100%", justifyContent: "center", padding: "10px 8px", fontSize: "0.85rem", whiteSpace: "nowrap" }}
                >
                  {/* The official four-colour Google mark. These hex values are Google's own brand
                      specification and are the one deliberate exception to the house rule that
                      colours come from the design tokens: a recoloured Google logo is a wrong logo. */}
                  <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0 }}>
                    <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"/>
                    <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.13 0-5.78-2.11-6.73-4.96H1.19v3.15C3.17 21.36 7.23 24 12 24z"/>
                    <path fill="#FBBC05" d="M5.27 14.24c-.25-.72-.39-1.49-.39-2.24s.14-1.52.39-2.24V6.6H1.19C.43 8.13 0 9.87 0 11.75s.43 3.62 1.19 5.15l4.08-2.66z"/>
                    <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.23 0 3.17 2.64 1.19 6.6l4.08 3.15c.95-2.85 3.6-4.96 6.73-4.96z"/>
                  </svg>
                  <span>{pending === "google" ? "Opening..." : "Google"}</span>
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={handleGuest}
                  disabled={pending !== null}
                  aria-label={pending === "guest" ? "Starting guest session..." : "Try it as a guest"}
                  style={{ width: "100%", justifyContent: "center", padding: "10px 8px", fontSize: "0.85rem", whiteSpace: "nowrap" }}
                >
                  <Logo size={18} />
                  <span>{pending === "guest" ? "Starting..." : "Guest"}</span>
                </button>
              </div>
              <p className="muted" style={{ fontSize: "0.8rem", textAlign: "center", margin: "4px 0 0" }}>
                A guest can upload emails and use the whole triage flow, but has no forwarding address, because a forwarding address belongs to a confirmed email account.
              </p>
            </>
          )}

          {fieldError && <p className="error" role="alert" id="login-error" style={{ marginTop: "12px", textAlign: "center", fontSize: "0.9rem" }}>{fieldError}</p>}
        </form>
      </div>

      {/* Forwarding Inbox Notice */}
      {forwardingConfig && !dismissed && (
        <aside
          className="card forwarding-notice"
          role="region"
          aria-label="Forwarding inbox notice"
        >
          <div className="forwarding-notice-inner">
            <div className="forwarding-notice-header">
              <h2>Forwarding inbox</h2>
              <button
                type="button"
                className="icon-button"
                aria-label="Dismiss"
                onClick={dismissForwarding}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="forwarding-notice-body">
              <p className="muted">
                Domain: <span className="mono">{forwardingConfig.alias_domain}</span>
              </p>
              <p className="muted">
                Pattern: <span className="mono">{forwardingConfig.alias_pattern}</span>
              </p>
              <p className="muted forwarding-notice-hint">
                Your own address appears on your Profile once you sign in.
              </p>
            </div>
            {!forwardingConfig.inbound_configured && (
              <p className="error forwarding-notice-status">
                Inbound forwarding is not connected yet.
              </p>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
