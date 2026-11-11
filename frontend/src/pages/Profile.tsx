import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useSession } from "../auth";
import UploadBox from "../components/UploadBox";

export default function Profile() {
  const { user, signOut } = useSession();
  const nav = useNavigate();
  const [alias, setAlias] = useState<string | null>(null);
  const [aliasError, setAliasError] = useState<string | null>(null);
  const [baselineMsg, setBaselineMsg] = useState<string | null>(null);
  const [baselineError, setBaselineError] = useState<string | null>(null);

  useEffect(() => {
    api.alias()
      .then((a) => setAlias(a.address))
      .catch((e) => setAliasError((e as Error).message));
  }, []);

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
            <dd className="mono">{user?.email ?? "Authentication is disabled on this deployment"}</dd>
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
            onClick={async () => {
              await signOut();
              nav("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </section>

      <section className="card" aria-labelledby="profile-alias-heading">
        <h2 id="profile-alias-heading">Forwarding address</h2>
        {aliasError ? (
          <p className="error" role="alert">Could not load your forwarding address: {aliasError}</p>
        ) : alias ? (
          <>
            <p className="mono big" style={{ margin: "8px 0 0 0" }}>{alias}</p>
            <p className="muted" style={{ margin: "12px 0 0 0", maxWidth: "68ch" }}>
              Forward suspicious emails to this address. Forward them as an attachment so the original
              authentication headers (SPF, DKIM, DMARC) stay intact. Inline forwarding drops them, and
              the system then reports them as missing rather than failed.
            </p>
          </>
        ) : (
          <p className="muted">Loading your forwarding address...</p>
        )}
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
