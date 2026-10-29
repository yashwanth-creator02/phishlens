import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import BandBar from "../components/BandBar";
import RiskBadge from "../components/RiskBadge";
import type { AnalysisDetail, FeatureRow } from "../types";

const GROUP_LABEL: Record<string, string> = {
  header: "Sender / headers", url: "Links", text: "Wording", action: "Requested action",
  attachment: "Attachments", behaviour: "Sender history", model: "Overall pattern",
};

export default function AnalysisDetailPage() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [a, setA] = useState<AnalysisDetail | null>(null);
  const [features, setFeatures] = useState<FeatureRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get(id).then(setA).catch((e) => setError((e as Error).message));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!a) return <p className="muted">Loading…</p>;

  const title = a.risk_band === "LOW" ? "Minor signals noticed" : "Why this message looks suspicious";

  return (
    <>
      <p><Link to="/">← All analyses</Link></p>
      <div className={`card ${a.risk_band.toLowerCase()}`}>
        <div className="row">
          <h1>{a.subject || "(no subject)"}</h1>
          <RiskBadge band={a.risk_band} score={a.risk_score} />
        </div>
        <BandBar score={a.risk_score} band={a.risk_band} />
        <p className="guidance">{a.guidance}</p>
        <p className="muted">
          From {a.sender_name} &lt;{a.sender_address}&gt; · {a.scope.replace("_", " ")}
          {a.forwarded_by ? ` by ${a.forwarded_by}` : ""} · model {a.model_version}
        </p>
      </div>

      <h2>{title}</h2>
      {a.reasons.length === 0 ? (
        <p className="muted">No individual warning signs were found.</p>
      ) : (
        <ol className="reasons">
          {a.reasons.map((r) => (
            <li key={r.rule_key}>
              <span className="tag">{GROUP_LABEL[r.group] ?? r.group}</span> {r.sentence}
            </li>
          ))}
        </ol>
      )}
      {a.scope === "forward_inline" && (
        <p className="note">
          This email was forwarded inline, so the original SPF/DKIM/DMARC results are not available. Forwarding it
          “as attachment” gives a more reliable check.
        </p>
      )}
      <p className="muted">
        Sender history: {a.history_message_count === 0 ? "no earlier trusted messages from this sender" : `${a.history_message_count} earlier trusted message(s)`}.
      </p>

      <h2>Evidence</h2>
      <div className="grid2">
        <div>
          <h3>Links ({a.links.length})</h3>
          {a.links.length === 0 ? <p className="muted">None</p> : (
            <ul className="plain">{a.links.map((l, i) => (
              <li key={i}><code>{l.href}</code>{l.text && <div className="muted">shown as “{l.text}”</div>}</li>
            ))}</ul>
          )}
          <h3>Attachments ({a.attachments.length})</h3>
          {a.attachments.length === 0 ? <p className="muted">None</p> : (
            <ul className="plain">{a.attachments.map((x, i) => (
              <li key={i}>{x.filename || "(unnamed)"} <span className="muted">{x.content_type}, {x.size} bytes</span></li>
            ))}</ul>
          )}
        </div>
        <div>
          <h3>Authentication</h3>
          <ul className="plain">{Object.entries(a.auth).map(([k, v]) => <li key={k}>{k.toUpperCase()}: <strong>{v}</strong></li>)}</ul>
          <h3>Message preview</h3>
          <pre className="preview">{a.text_preview || "(no text)"}</pre>
        </div>
      </div>

      <h2>How the model decided</h2>
      {features === null ? (
        <button onClick={() => api.features(id).then(setFeatures).catch((e) => setError((e as Error).message))}>
          Show feature contributions
        </button>
      ) : (
        <table className="list small">
          <thead><tr><th>Feature</th><th>Group</th><th>Value</th><th>Contribution (SHAP)</th></tr></thead>
          <tbody>
            {features.filter((f) => Math.abs(f.contribution) > 1e-6).slice(0, 20).map((f) => (
              <tr key={f.name}>
                <td><code>{f.name}</code></td><td className="muted">{f.group}</td>
                <td>{f.value.toFixed(2)}</td>
                <td className={f.contribution > 0 ? "pos" : "neg"}>{f.contribution > 0 ? "+" : ""}{f.contribution.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="danger-zone">
        <button className="danger" onClick={async () => { await api.remove(a.id); nav("/"); }}>Delete this analysis</button>
        <span className="muted"> removes the stored email and its results.</span>
      </p>
    </>
  );
}
