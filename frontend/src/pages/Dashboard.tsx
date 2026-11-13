import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useForwardingAlias } from "../hooks/useForwardingAlias";
import RiskBadge from "../components/RiskBadge";
import UploadBox from "../components/UploadBox";
import type { AnalysisSummary } from "../types";

const SCOPE_LABEL: Record<string, string> = {
  direct: "Uploaded directly",
  forward_attachment: "Forwarded as attachment",
  forward_inline: "Forwarded inline",
};

const RECENT_COUNT = 5;

export default function Dashboard() {
  const nav = useNavigate();
  const aliasState = useForwardingAlias();
  const [copiedAddress, setCopiedAddress] = useState(false);
  const [items, setItems] = useState<AnalysisSummary[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const copyAddress = () => {
    if (aliasState.status === "verified") {
      navigator.clipboard.writeText(aliasState.address);
      setCopiedAddress(true);
      setTimeout(() => setCopiedAddress(false), 2000);
    }
  };

  const load = useCallback(() => {
    setRefreshing(true);
    setItems(null);
    setError(null);
    api.list(100, 0)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setError(null);
      })
      .catch((e) => {
        setError((e as Error).message);
        setItems([]);
      })
      .finally(() => {
        setRefreshing(false);
      });
  }, []);

  useEffect(load, [load]);

  const lowCount = items?.filter((i) => i.risk_band === "LOW").length ?? 0;
  const medCount = items?.filter((i) => i.risk_band === "MEDIUM").length ?? 0;
  const highCount = items?.filter((i) => i.risk_band === "HIGH").length ?? 0;
  const isCapped = total > 100;

  const recent = items?.slice(0, RECENT_COUNT) ?? [];

  return (
    <>
      <div className="row" style={{ alignItems: "baseline", marginBottom: "16px" }}>
        <div>
          <h1>Triage dashboard</h1>
          <p className="muted">
            Analyse an email, check the current risk mix, and open any past result from the history.
          </p>
        </div>
        <div>
          <button className="secondary" onClick={load} disabled={refreshing} type="button">
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* Forwarding & Mail App Bar */}
      <section className="dashboard-forwarding-card" aria-label="Forwarding and mail app triage">
        <div className="forwarding-card-content">
          <div className="forwarding-card-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <div className="forwarding-card-text">
            <div className="forwarding-card-header">
              <strong className="forwarding-card-title">Inbound Email Forwarding</strong>
              <span className="upload-format-chip">RFC-822 PRESERVED</span>
            </div>
            {aliasState.status === "verified" ? (
              <>
                <p className="muted" style={{ margin: "4px 0 8px", fontSize: "0.9rem" }}>
                  Forward suspicious emails as an attachment to your dedicated triage address:
                </p>
                <div className="forwarding-address-row">
                  <span className="mono forwarding-address-pill">{aliasState.address}</span>
                  <button
                    type="button"
                    className="copy-btn secondary"
                    onClick={copyAddress}
                    aria-label="Copy forwarding email address"
                  >
                    {copiedAddress ? (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                        </svg>
                        <span>Copy address</span>
                      </>
                    )}
                  </button>
                  <a
                    href={`mailto:${aliasState.address}?subject=Suspicious%20Email%20for%20Triage&body=Attach%20the%20suspicious%20email%20here%20as%20an%20attachment%20(.eml)%20and%20send%20to%20trigger%20automated%20PhishLens%20triage.`}
                    className="mail-app-link btn"
                    title="Launch your default email app"
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <line x1="22" y1="2" x2="11" y2="13"/>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                    <span>Open in Mail App</span>
                  </a>
                </div>
              </>
            ) : aliasState.status === "unverified" ? (
              <div style={{ marginTop: "4px" }}>
                <p className="muted" style={{ margin: "4px 0 8px", fontSize: "0.9rem" }}>
                  Forwarding alias is gated on email confirmation to protect inbox history.
                </p>
                <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
                  <Link to="/profile" className="secondary" style={{ padding: "4px 10px", fontSize: "0.85rem", textDecoration: "none" }}>
                    Verify email in Profile →
                  </Link>
                  <a href="mailto:?subject=PhishLens%20Triage" className="secondary" style={{ padding: "4px 10px", fontSize: "0.85rem", textDecoration: "none" }}>
                    Open Mail App
                  </a>
                </div>
              </div>
            ) : (
              <div style={{ marginTop: "4px" }}>
                <p className="muted" style={{ margin: "4px 0", fontSize: "0.9rem" }}>
                  Sign in with an email account to receive a personal forwarding address.
                </p>
                <a href="mailto:?subject=PhishLens%20Triage" className="secondary" style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 10px", fontSize: "0.85rem", textDecoration: "none", marginTop: "6px" }}>
                  Open Mail App
                </a>
              </div>
            )}
          </div>
        </div>
      </section>

      <UploadBox
        label="Analyse new email"
        hint="Drop an .eml, message/rfc822, or .txt file here. In mail clients, choose download message."
        onFile={async (f) => {
          const a = await api.upload(f);
          nav(`/analyses/${a.id}`);
        }}
      />

      {error ? (
        <div className="card high" style={{ padding: "16px" }}>
          <p className="error" role="alert">Failed to load analyses: {error}</p>
          <button onClick={load} disabled={refreshing} style={{ marginTop: "8px" }} type="button">
            {refreshing ? "Retrying..." : "Retry"}
          </button>
        </div>
      ) : (
        <>
          {/* Stat Strip */}
          <div className="stat-strip">
            <div className="stat-card stat-total">
              <div className="stat-label">Total analyses</div>
              <div className="stat-value mono">{total}</div>
            </div>
            <div className="stat-card stat-high">
              <div className="stat-label">High risk</div>
              <div className="stat-value mono" style={{ color: "var(--high)" }}>{highCount}</div>
            </div>
            <div className="stat-card stat-medium">
              <div className="stat-label">Medium risk</div>
              <div className="stat-value mono" style={{ color: "var(--medium)" }}>{medCount}</div>
            </div>
            <div className="stat-card stat-low">
              <div className="stat-label">Low risk</div>
              <div className="stat-value mono" style={{ color: "var(--low)" }}>{lowCount}</div>
            </div>
          </div>

          {/* Risk Distribution Bar */}
          {items && items.length > 0 && (
            <div className="risk-distribution-wrap">
              <div className="risk-distribution-header">
                <span className="risk-distribution-title">Triage Risk Distribution</span>
                <span className="risk-distribution-meta mono">
                  {highCount} High ({total > 0 ? Math.round((highCount / total) * 100) : 0}%) · {medCount} Medium ({total > 0 ? Math.round((medCount / total) * 100) : 0}%) · {lowCount} Low ({total > 0 ? Math.round((lowCount / total) * 100) : 0}%)
                </span>
              </div>
              <div className="risk-distribution-bar" role="meter" aria-label="Risk distribution">
                {highCount > 0 && (
                  <div
                    className="risk-bar-seg high"
                    style={{ width: `${(highCount / total) * 100}%` }}
                    title={`High Risk: ${highCount}`}
                  />
                )}
                {medCount > 0 && (
                  <div
                    className="risk-bar-seg medium"
                    style={{ width: `${(medCount / total) * 100}%` }}
                    title={`Medium Risk: ${medCount}`}
                  />
                )}
                {lowCount > 0 && (
                  <div
                    className="risk-bar-seg low"
                    style={{ width: `${(lowCount / total) * 100}%` }}
                    title={`Low Risk: ${lowCount}`}
                  />
                )}
              </div>
            </div>
          )}

          <p className="muted" style={{ fontSize: "0.85rem", marginTop: "-12px", marginBottom: "16px" }}>
            {isCapped ? `Band counts reflect the latest 100 analyses. Total records: ${total}.` : `Band counts cover all ${total} analyses.`}
          </p>

          <div className="toolbar">
            <div>
              <h2 style={{ margin: 0 }}>Recent activity</h2>
            </div>
            <div>
              <Link to="/history" className="secondary" style={{ textDecoration: "none" }}>Open history</Link>
            </div>
          </div>

          {items === null ? (
            <div role="status" aria-busy="true">
              <span className="sr-only">Loading recent analyses</span>
              <div className="skeleton-row" />
              <div className="skeleton-row" />
              <div className="skeleton-row" />
            </div>
          ) : recent.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "40px" }}>
              <p className="muted" style={{ fontSize: "1.05rem" }}>No analyses yet.</p>
              <p className="muted">
                {aliasState.status === "verified"
                  ? "Use the upload area above or forward an email to your alias to begin triage."
                  : aliasState.status === "unverified" || aliasState.status === "unconfigured"
                  ? "Confirm your email address to get a forwarding address."
                  : "Use the upload area above to begin triage."}
              </p>
            </div>
          ) : (
            <div className="analysis-list">
              {recent.map((a) => (
                <Link key={a.id} to={`/analyses/${a.id}`} className="analysis-row">
                  <div>
                    <RiskBadge band={a.risk_band} score={a.risk_score} />
                  </div>
                  <div>
                    <div className="analysis-row-subject" title={a.subject || "(no subject)"}>{a.subject || "(no subject)"}</div>
                    <div className="analysis-row-sender" title={`${a.sender_name ? `${a.sender_name} ` : ""}<${a.sender_address}>`}>
                      {a.sender_name ? `${a.sender_name} ` : ""}
                      <span className="mono">&lt;{a.sender_address}&gt;</span>
                    </div>
                  </div>
                  <div className="muted" style={{ fontSize: "0.85rem" }}>
                    {SCOPE_LABEL[a.scope] ?? a.scope}
                  </div>
                  <div className="analysis-row-meta">
                    {new Date(a.created_at + "Z").toLocaleString()}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </>
  );
}
