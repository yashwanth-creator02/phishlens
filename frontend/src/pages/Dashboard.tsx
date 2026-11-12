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
  const [items, setItems] = useState<AnalysisSummary[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
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
          <button className="secondary" onClick={load} type="button">Refresh</button>
        </div>
      </div>

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
          <button onClick={load} style={{ marginTop: "8px" }} type="button">Retry</button>
        </div>
      ) : (
        <>
          {/* Stat Strip */}
          <div className="stat-strip">
            <div className="stat-card">
              <div className="stat-label">Total analyses</div>
              <div className="stat-value mono">{total}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">High risk</div>
              <div className="stat-value mono" style={{ color: "var(--high)" }}>{highCount}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Medium risk</div>
              <div className="stat-value mono" style={{ color: "var(--medium)" }}>{medCount}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Low risk</div>
              <div className="stat-value mono" style={{ color: "var(--low)" }}>{lowCount}</div>
            </div>
          </div>
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
