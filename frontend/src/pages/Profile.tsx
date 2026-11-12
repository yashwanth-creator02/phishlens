import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useSession } from "../auth";
import { useForwardingAlias } from "../hooks/useForwardingAlias";
import { supabase } from "../supabase";
import UploadBox from "../components/UploadBox";

export default function Profile() {
  const { user, signOut } = useSession();
  const nav = useNavigate();
  const aliasState = useForwardingAlias();

  const [baselineMsg, setBaselineMsg] = useState<string | null>(null);
  const [baselineError, setBaselineError] = useState<string | null>(null);
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);
  const [resending, setResending] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const handleResend = async () => {
    if (!user?.email || !supabase) return;
    setResending(true);
    setResendError(null);
    setResendStatus(null);
    const { error } = await supabase.auth.resend({
      type: "signup",
      email: user.email,
    });
    setResending(false);
    if (error) {
      setResendError(error.message);
    } else {
      setResendStatus("Verification email sent. Check your inbox.");
    }
  };

  return (
    <>
      <div className="row" style={{ alignItems: "baseline", marginBottom: "16px" }}>
        <div>
          <h1>Profile</h1>
          <p className="muted">Your account, the forwarding address you hand to senders, and your trusted-sender baseline.</p>
        </div>
      </div>

      <section className="card" aria-labelledby="profile-account-heading">
        <h2 id="profile-account-heading" style={{ marginTop: 0 }}>Account</h2>
        <dl className="facts">
          <div>
            <dt>Signed in as</dt>
            <dd className="mono">
              {user?.is_anonymous
                ? "Guest user (anonymous session)"
                : user?.email ?? "Authentication is disabled on this deployment"}
            </dd>
          </div>
          <div>
            <dt>Session</dt>
            <dd>{user ? "Authenticated" : "No authentication configured"}</dd>
          </div>
        </dl>
        <div className="report-actions">
          <button
            className="secondary"
            type="button"
            disabled={signingOut}
            onClick={async () => {
              setSigningOut(true);
              try {
                await signOut();
                nav("/login");
              } finally {
                setSigningOut(false);
              }
            }}
          >
            {signingOut ? "Signing out..." : "Sign out"}
          </button>
        </div>
      </section>

      <section className="card" aria-labelledby="profile-alias-heading">
        <h2 id="profile-alias-heading">Forwarding address</h2>
        {user?.is_anonymous ? (
          <div className="card medium" role="region" aria-labelledby="guest-heading" style={{ marginTop: "12px" }}>
            <h3 id="guest-heading" style={{ marginTop: 0 }}>Guest account</h3>
            <p className="muted" style={{ maxWidth: "68ch" }}>
              Upload an email to try the full flow. A guest has no forwarding address; sign up with an email to get one.
            </p>
          </div>
        ) : aliasState.status === "loading" ? (
          <p className="muted">Loading your forwarding address...</p>
        ) : aliasState.status === "verified" ? (
          <>
            <p className="mono big" style={{ margin: "8px 0 0 0" }}>{aliasState.address}</p>
            <p className="muted" style={{ margin: "12px 0 0 0", maxWidth: "68ch" }}>
              Forward suspicious emails to this address. Forward them as an attachment so the original
              authentication headers (SPF, DKIM, DMARC) stay intact. Inline forwarding drops them, and
              the system then reports them as missing rather than failed.
            </p>
          </>
        ) : aliasState.status === "unverified" ? (
          <div className="card medium" role="region" aria-labelledby="verify-heading" style={{ marginTop: "12px" }}>
            <h3 id="verify-heading" style={{ marginTop: 0 }}>Verify your email address</h3>
            <p className="muted">Account email: <span className="mono">{user?.email ?? "unknown"}</span></p>
            <p className="muted" style={{ maxWidth: "68ch" }}>
              Forwarding alias remains unavailable until your email address is confirmed.
            </p>
            <div className="report-actions">
              <button
                type="button"
                className="secondary"
                onClick={handleResend}
                disabled={resending || !user?.email}
              >
                {resending ? "Sending..." : "Resend verification email"}
              </button>
            </div>
            {resendStatus && <p className="muted" style={{ marginTop: "8px", color: "var(--low)" }}>{resendStatus}</p>}
            {resendError && <p className="error" role="alert" style={{ marginTop: "8px" }}>{resendError}</p>}
          </div>
        ) : aliasState.status === "unconfigured" ? (
          <div className="card medium" role="region" aria-labelledby="unconfigured-heading" style={{ marginTop: "12px" }}>
            <h3 id="unconfigured-heading" style={{ marginTop: 0 }}>Email verification not configured</h3>
            <p className="muted" style={{ maxWidth: "68ch" }}>
              Email verification is not configured on this server yet. Forwarding alias is temporarily unavailable.
            </p>
          </div>
        ) : (
          <p className="error" role="alert">Could not load your forwarding address: {aliasState.message}</p>
        )}
      </section>

      <section className="card" role="region" aria-labelledby="profile-data-heading">
        <h2 id="profile-data-heading" style={{ marginTop: 0 }}>Data handling</h2>
        <p className="muted" style={{ maxWidth: "68ch" }}>
          Forwarding or uploading an email means any personal data contained within it is processed by the system.
        </p>
        <ul className="reasons" style={{ paddingLeft: "20px", margin: "12px 0" }}>
          <li>Raw uploaded emails, headers, extracted links and attachments, 65 feature values, and generated explanations are stored.</li>
          <li>Data is retained for 30 days, after which the automated retention purge deletes it.</li>
          <li>Attachments are recorded as metadata only (name, size, type) and are never opened, executed, or rendered.</li>
          <li>Analyses are isolated per account; only the signed-in account that owns them can access them.</li>
          <li>The active model was trained partly on the owner's mailbox, and the published model artifact was verified by a privacy audit that found no addresses, subjects, or message text.</li>
        </ul>
        <p className="muted" style={{ fontSize: "0.9rem", marginTop: "12px", marginBottom: 0 }}>
          For further technical details, see the security and privacy documentation at <span className="mono">docs/11-security-privacy.md</span>.
        </p>
      </section>

      <section className="card" aria-labelledby="profile-baseline-heading">
        <h2 id="profile-baseline-heading">Trusted sender baseline</h2>
        <p className="muted" style={{ maxWidth: "68ch" }}>
          Upload emails you know are genuine. PhishLens then flags later messages from that sender when
          they deviate from the established pattern. Only LOW-risk results and explicit uploads update the
          profile, so a phishing message never teaches the system to trust its own sender.
        </p>
        <UploadBox
          label="Add known-good email"
          hint="Only upload messages from verified trusted contacts."
          onFile={async (f) => {
            setBaselineError(null);
            try {
              const r = await api.baseline(f);
              setBaselineMsg(`${r.sender}: recorded ${r.message_count} trusted message(s). ${r.note}`);
            } catch (e) {
              setBaselineError((e as Error).message);
            }
          }}
        />
        {baselineMsg && (
          <div className="card low" style={{ padding: "12px 16px", marginTop: "16px" }}>
            <p style={{ margin: 0 }}>{baselineMsg}</p>
          </div>
        )}
        {baselineError && (
          <p className="error" role="alert" style={{ marginTop: "12px" }}>{baselineError}</p>
        )}
      </section>
    </>
  );
}
