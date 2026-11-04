import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import BandBar from "../components/BandBar";
import RiskBadge from "../components/RiskBadge";
import type { AnalysisDetail, FeatureRow } from "../types";

const SCOPE_LABEL: Record<string, string> = {
  direct: "Uploaded directly",
  forward_attachment: "Forwarded as attachment",
  forward_inline: "Forwarded inline",
};

const GROUP_LABEL: Record<string, string> = {
  header: "Sender / headers",
  url: "Links",
  text: "Wording",
  action: "Requested action",
  attachment: "Attachments",
  behaviour: "Sender history",
  model: "Overall pattern",
};

export default function AnalysisDetailPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [a, setA] = useState<AnalysisDetail | null>(null);
  const [features, setFeatures] = useState<FeatureRow[] | null>(null);
  const [featureError, setFeatureError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get(id).then(setA).catch((e) => setError((e as Error).message));
  }, [id]);

  if (error) {
    return (
      <>
        <p><Link to="/">← Back to dashboard</Link></p>
        <div className="card high">
          <p className="error" role="alert">Failed to load analysis: {error}</p>
          <button className="secondary" onClick={() => window.location.reload()} style={{ marginTop: "12px" }} type="button">
            Retry loading
          </button>
        </div>
      </>
    );
  }

  if (!a) {
    return <p className="muted pad" style={{ textAlign: "center" }}>Loading analysis report...</p>;
  }

  const title = a.risk_band === "LOW" ? "Minor signals noticed" : "Why this message looks suspicious";

  const scopeLabel = SCOPE_LABEL[a.scope] ?? a.scope.replace("_", " ");

  return (
    <>
      <p style={{ marginBottom: "20px" }}>
        <Link to="/">← Back to dashboard</Link>
      </p>

      <div className={`card ${a.risk_band.toLowerCase()}`}>
        <div className="row">
          <h1>{a.subject || "(no subject)"}</h1>
          <RiskBadge band={a.risk_band} score={a.risk_score} />
        </div>
        <BandBar score={a.risk_score} band={a.risk_band} />
        <p className="guidance">{a.guidance}</p>
        <div className="muted" style={{ fontSize: "0.95rem", display: "flex", flexWrap: "wrap", gap: "16px", marginTop: "16px" }}>
          <span>From: <strong>{a.sender_name ? `${a.sender_name} ` : ""}</strong><span className="mono">&lt;{a.sender_address}&gt;</span></span>
          <span>Scope: {scopeLabel}{a.forwarded_by ? ` by ${a.forwarded_by}` : ""}</span>
          <span>Model: <span className="mono">{a.model_version}</span></span>
          <span>Timestamp: {new Date(a.created_at + "Z").toLocaleString()}</span>
        </div>
      </div>

      <h2>{title}</h2>
      {a.reasons.length === 0 ? (
        <p className="muted">No individual warning signs were triggered by evidence rules.</p>
      ) : (
        <ol className="reasons">
          {a.reasons.map((r) => (
            <li key={r.rule_key}>
              <span className="tag">{GROUP_LABEL[r.group] ?? r.group}</span>
              <span>{r.sentence}</span>
            </li>
          ))}
        </ol>
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
      <div className="grid2">
        <div className="card" style={{ margin: 0 }}>
          <h3>Links ({a.links.length})</h3>
          {a.links.length === 0 ? (
            <p className="muted">No external links found.</p>
          ) : (
            <ul className="plain">
              {a.links.map((l, i) => (
                <li key={i} style={{ wordBreak: "break-all" }}>
                  <code className="mono">{l.href}</code>
                  {l.text && <div className="muted" style={{ fontSize: "0.85rem" }}>Shown text: {l.text}</div>}
                </li>
              ))}
            </ul>
          )}

          <h3 style={{ marginTop: "24px" }}>Attachments ({a.attachments.length})</h3>
          {a.attachments.length === 0 ? (
            <p className="muted">No attachments present.</p>
          ) : (
            <ul className="plain">
              {a.attachments.map((x, i) => (
                <li key={i}>
                  <strong>{x.filename || "(unnamed)"}</strong>{" "}
                  <span className="muted mono" style={{ fontSize: "0.85rem" }}>({x.content_type}, {x.size} bytes)</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card" style={{ margin: 0 }}>
          <h3>Authentication headers</h3>
          {Object.keys(a.auth).length === 0 ? (
            <p className="muted">No authentication headers recorded.</p>
          ) : (
            <ul className="plain">
              {Object.entries(a.auth).map(([k, v]) => (
                <li key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span className="muted mono">{k.toUpperCase()}</span>
                  <strong className="mono">{v}</strong>
                </li>
              ))}
            </ul>
          )}

          <h3 style={{ marginTop: "24px" }}>Message preview</h3>
          <pre className="preview">{a.text_preview || "(no text content)"}</pre>
        </div>
      </div>

      <h2>Model decision process</h2>
      {featureError && <p className="error" role="alert">{featureError}</p>}
      {features === null ? (
        <button
          className="secondary"
          onClick={() => {
            setFeatureError(null);
            api.features(id)
              .then(setFeatures)
              .catch((e) => setFeatureError((e as Error).message));
          }}
          type="button"
        >
          Load feature contributions (SHAP)
        </button>
      ) : (
        <>
          <p className="muted" style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
            Positive values push toward phishing, negative values push away. Showing the 20 largest absolute contributions.
          </p>
          <table className="list small">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Group</th>
                <th>Value</th>
                <th>Contribution (SHAP)</th>
              </tr>
            </thead>
            <tbody>
              {features
                .slice()
                .sort((x, y) => Math.abs(y.contribution) - Math.abs(x.contribution))
                .filter((f) => Math.abs(f.contribution) > 1e-6)
                .slice(0, 20)
                .map((f) => (
                  <tr key={f.name}>
                    <td><code className="mono">{f.name}</code></td>
                    <td className="muted">{f.group}</td>
                    <td className="mono">{f.value.toFixed(2)}</td>
                    <td className={f.contribution > 0 ? "pos" : "neg"}>
                      {f.contribution > 0 ? "+" : ""}{f.contribution.toFixed(3)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </>
      )}

      <div className="danger-zone">
        <DeleteSection analysisId={a.id} nav={nav} />
      </div>
    </>
  );
}

function DeleteSection({ analysisId, nav }: { analysisId: string; nav: (to: string) => void }) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <>
      <button
        className="danger"
        disabled={deleting}
        onClick={async () => {
          if (window.confirm("Are you sure you want to delete this analysis?")) {
            setDeleting(true);
            setError(null);
            try {
              await api.remove(analysisId);
              nav("/");
            } catch (e) {
              setError((e as Error).message);
              setDeleting(false);
            }
          }
        }}
        type="button"
      >
        {deleting ? "Deleting..." : "Delete analysis"}
      </button>
      <span className="muted">Permanently removes the stored email record and triage results.</span>
      {error && <p className="error" role="alert" style={{ width: "100%", marginTop: "8px" }}>Failed to delete analysis: {error}</p>}
    </>
  );
}
