import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import BandBar from "../components/BandBar";
import EvidencePanel from "../components/EvidencePanel";
import FeatureTable from "../components/FeatureTable";
import ReasonCard from "../components/ReasonCard";
import RiskBadge from "../components/RiskBadge";
import type { AnalysisDetail, FeatureRow } from "../types";
import "../styles/report.css";

const SCOPE_LABEL: Record<string, string> = {
  direct: "Uploaded directly",
  forward_attachment: "Forwarded as attachment",
  forward_inline: "Forwarded inline",
};

function buildSummary(a: AnalysisDetail) {
  const lines = [
    `PhishLens analysis: ${a.subject || "(no subject)"}`,
    `Risk: ${a.risk_band} (${a.risk_score}/100)`,
    `From: ${a.sender_name ? `${a.sender_name} ` : ""}<${a.sender_address}>`,
    `Model: ${a.model_version}`,
    `Guidance: ${a.guidance}`,
    "",
    "Verified reasons:",
    ...(a.reasons.length === 0
      ? ["- No individual warning signs were triggered by evidence rules."]
      : a.reasons.map((r) => `- ${r.sentence}`)),
    "",
    `Links: ${a.links.length} · Attachments: ${a.attachments.length} · History: ${a.history_message_count} trusted message(s)`,
  ];
  return lines.join("\n");
}

export default function AnalysisDetailPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [a, setA] = useState<AnalysisDetail | null>(null);
  const [features, setFeatures] = useState<FeatureRow[] | null>(null);
  const [featureError, setFeatureError] = useState<string | null>(null);
  const [loadingFeatures, setLoadingFeatures] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    api.get(id).then(setA).catch((e) => setError((e as Error).message));
  }, [id]);

  useEffect(() => {
    if (!confirmDelete) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setConfirmDelete(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [confirmDelete]);

  if (error) {
    return (
      <>
        <p>
          <Link to="/">Back to dashboard</Link>
        </p>
        <div className="card high">
          <p className="error" role="alert">
            Failed to load analysis: {error}
          </p>
          <button
            className="secondary"
            onClick={() => window.location.reload()}
            style={{ marginTop: "12px" }}
            type="button"
          >
            Retry loading
          </button>
        </div>
      </>
    );
  }

  if (!a) return <p className="muted pad" role="status">Loading analysis report...</p>;

  const title = a.risk_band === "LOW" ? "Minor signals noticed" : "Why this message looks suspicious";
  const scopeLabel = SCOPE_LABEL[a.scope] ?? a.scope.replace("_", " ");
  const headerEntries = Object.entries(a.headers);

  const copySummary = async () => {
    await navigator.clipboard.writeText(buildSummary(a));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <p style={{ marginBottom: "20px" }}>
        <Link to="/">Back to dashboard</Link>
      </p>

      <div className={`card report-verdict ${a.risk_band.toLowerCase()}`}>
        <div className="row">
          <h1>{a.subject || "(no subject)"}</h1>
          <RiskBadge band={a.risk_band} score={a.risk_score} />
        </div>
        <BandBar score={a.risk_score} band={a.risk_band} />
        <p className="guidance">{a.guidance}</p>
        <div className="report-verdict-meta">
          <span>
            From: <strong>{a.sender_name ? `${a.sender_name} ` : ""}</strong>
            <span className="mono">&lt;{a.sender_address}&gt;</span>
          </span>
          <span>Scope: {scopeLabel}{a.forwarded_by ? ` by ${a.forwarded_by}` : ""}</span>
          <span>Model: <span className="mono">{a.model_version}</span></span>
          <span>Timestamp: {new Date(a.created_at + "Z").toLocaleString()}</span>
        </div>
        <div className="report-actions">
          <button className="secondary" onClick={() => void copySummary()} type="button">
            {copied ? "Summary copied" : "Copy summary"}
          </button>
          <span className="muted" role="status">{copied ? "Copied to clipboard." : ""}</span>
        </div>
      </div>

      <h2>{title}</h2>
      <p className="muted" style={{ fontSize: "0.95rem" }}>
        Each reason below was checked against evidence in this email. Only verified reasons are shown.
      </p>
      {a.reasons.length === 0 ? (
        <p className="muted">No individual warning signs were triggered by evidence rules.</p>
      ) : (
        <div>
          <ol className="plain" style={{ listStyle: "none", padding: 0, margin: "12px 0 0" }}>
            {a.reasons.map((r, i) => (
              <li key={r.rule_key}>
                <ReasonCard reason={r} index={i} />
              </li>
            ))}
          </ol>
        </div>
      )}

      {a.scope === "forward_inline" && (
        <div className="note">
          This email was forwarded inline, so original SPF, DKIM, and DMARC authentication headers are not available.
          Forwarding as an attachment provides a more reliable verification result.
        </div>
      )}

      <p className="muted" style={{ marginTop: "16px" }}>
        Sender history: {a.history_message_count === 0 ? "no earlier trusted messages recorded from this sender." : `${a.history_message_count} earlier trusted message(s) on file.`}
      </p>

      <h2>Evidence summary</h2>
      <EvidencePanel analysis={a} />

      <h2>Model decision process</h2>
      {featureError && <p className="error" role="alert">{featureError}</p>}
      {features === null ? (
        <button
          className="secondary"
          disabled={loadingFeatures}
          onClick={() => {
            setFeatureError(null);
            setLoadingFeatures(true);
            api.features(id)
              .then(setFeatures)
              .catch((e) => setFeatureError((e as Error).message))
              .finally(() => setLoadingFeatures(false));
          }}
          type="button"
        >
          {loadingFeatures ? "Loading features..." : "Load feature contributions (SHAP)"}
        </button>
      ) : (
        <>
          <p className="muted" style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
            Positive values push toward phishing, negative values push away. Showing the 20 largest absolute contributions.
          </p>
          <FeatureTable rows={features} />
        </>
      )}

      <h2>Raw headers</h2>
      {headerEntries.length === 0 ? (
        <p className="muted">No raw headers recorded.</p>
      ) : (
        <table className="list small raw-headers">
          <caption>Headers stored from the parsed email, exactly as received</caption>
          <thead>
            <tr>
              <th>Header</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {headerEntries.map(([k, v]) => (
              <tr key={k}>
                <td className="muted mono">{k}</td>
                <td className="mono" style={{ overflowWrap: "break-word" }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="danger-zone">
        <DeleteSection
          analysisId={a.id}
          nav={nav}
          confirmOpen={confirmDelete}
          onConfirmChange={setConfirmDelete}
        />
      </div>
    </>
  );
}

function DeleteSection({
  analysisId,
  nav,
  confirmOpen,
  onConfirmChange,
}: {
  analysisId: string;
  nav: (to: string) => void;
  confirmOpen: boolean;
  onConfirmChange: (open: boolean) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await api.remove(analysisId);
      nav("/");
    } catch (e) {
      setError((e as Error).message);
      setDeleting(false);
    }
  };

  return (
    <>
      <button className="danger" disabled={deleting} onClick={() => onConfirmChange(true)} type="button">
        Delete analysis
      </button>
      <span className="muted">Permanently removes the stored email record and triage results.</span>
      {error && <p className="error" role="alert" style={{ width: "100%", marginTop: "8px" }}>Failed to delete analysis: {error}</p>}

      {confirmOpen && (
        <div className="dialog-overlay" role="presentation" onClick={() => !deleting && onConfirmChange(false)}>
          <div
            className="dialog-panel"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-title"
            aria-describedby="delete-desc"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="delete-title">Delete this analysis?</h2>
            <p id="delete-desc" className="muted" style={{ margin: 0 }}>
              This permanently removes the stored email record and triage results for this case.
              This cannot be undone.
            </p>
            <div className="dialog-actions">
              <button className="secondary" disabled={deleting} onClick={() => onConfirmChange(false)} type="button">
                Cancel
              </button>
              <button className="danger" disabled={deleting} onClick={() => void doDelete()} type="button">
                {deleting ? "Deleting..." : "Delete permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
