import type { AnalysisDetail } from "../types";
import "../styles/report.css";

export default function EvidencePanel({ analysis }: { analysis: AnalysisDetail }) {
  return (
    <div className="grid2" aria-label="Evidence panels">
      <section className="card evidence-panel" aria-labelledby="evidence-links-heading">
        <h3 id="evidence-links-heading">Links ({analysis.links.length})</h3>
        {analysis.links.length === 0 ? (
          <p className="muted">No external links found.</p>
        ) : (
          <ul className="plain">
            {analysis.links.map((l, i) => (
              <li key={i} style={{ overflowWrap: "break-word" }}>
                <code className="mono">{l.href}</code>
                {l.text && (
                  <div className="muted" style={{ fontSize: "0.85rem" }}>
                    Shown text: {l.text}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}

        <h3 className="section-gap">Attachments ({analysis.attachments.length})</h3>
        {analysis.attachments.length === 0 ? (
          <p className="muted">No attachments present.</p>
        ) : (
          <ul className="plain">
            {analysis.attachments.map((x, i) => (
              <li key={i}>
                <strong>{x.filename || "(unnamed)"}</strong>{" "}
                <span className="muted mono" style={{ fontSize: "0.85rem" }}>
                  ({x.content_type}, {x.size} bytes)
                </span>
              </li>
            ))}
          </ul>
        )}
        <p className="muted" style={{ fontSize: "0.85rem", marginTop: "16px", marginBottom: 0 }}>
          Attachment contents are never opened or executed. Only metadata is shown.
        </p>
      </section>

      <section className="card evidence-panel" aria-labelledby="evidence-auth-heading">
        <h3 id="evidence-auth-heading">Authentication headers</h3>
        {Object.keys(analysis.auth).length === 0 ? (
          <p className="muted">No authentication headers recorded.</p>
        ) : (
          <ul className="plain">
            {Object.entries(analysis.auth).map(([k, v]) => (
              <li key={k} style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                <span className="muted mono">{k.toUpperCase()}</span>
                <strong className="mono">{v}</strong>
              </li>
            ))}
          </ul>
        )}

        <h3 className="section-gap">Message preview</h3>
        <pre className="preview">{analysis.text_preview || "(no text content)"}</pre>
      </section>
    </div>
  );
}
