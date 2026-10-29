import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import UploadBox from "../components/UploadBox";
import type { AnalysisSummary } from "../types";

const SCOPE: Record<string, string> = {
  direct: "uploaded directly",
  forward_attachment: "forwarded as attachment",
  forward_inline: "forwarded inline",
};

export default function Dashboard() {
  const nav = useNavigate();
  const [items, setItems] = useState<AnalysisSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api.list().then((r) => { setItems(r.items); setTotal(r.total); setError(null); }).catch((e) => setError((e as Error).message));
  }, []);
  useEffect(load, [load]);

  return (
    <>
      <h1>Analyses</h1>
      <p className="muted">
        Forward a suspicious email to your PhishLens address (see Settings), or upload an .eml file here.
      </p>
      <UploadBox
        label="Analyse an email file"
        hint="Drop an .eml file or choose one. In Gmail: open the message, ⋮ menu, Download message."
        onFile={async (f) => { const a = await api.upload(f); nav(`/analyses/${a.id}`); }}
      />
      {error && <p className="error">{error}</p>}
      <h2>History <span className="muted">({total})</span></h2>
      {items.length === 0 ? (
        <p className="muted">Nothing analysed yet.</p>
      ) : (
        <table className="list">
          <thead><tr><th>Risk</th><th>Subject</th><th>Sender</th><th>How received</th><th>When</th></tr></thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id}>
                <td><RiskBadge band={a.risk_band} score={a.risk_score} /></td>
                <td><Link to={`/analyses/${a.id}`}>{a.subject || "(no subject)"}</Link></td>
                <td>{a.sender_name ? `${a.sender_name} ` : ""}<span className="muted">{a.sender_address}</span></td>
                <td className="muted">{SCOPE[a.scope] ?? a.scope}</td>
                <td className="muted">{new Date(a.created_at + "Z").toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
