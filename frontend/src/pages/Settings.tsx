import { useEffect, useState } from "react";
import { api } from "../api/client";
import UploadBox from "../components/UploadBox";
import type { ModelInfo } from "../types";

export default function Settings() {
  const [alias, setAlias] = useState<string | null>(null);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.alias().then((a) => setAlias(a.address)).catch(() => setAlias(null));
    api.model().then(setModel).catch((e) => setError((e as Error).message));
  }, []);

  return (
    <>
      <h1>Settings and configuration</h1>
      <p className="muted">Manage your inbound forwarding address, known-good sender baseline profiles, and model registry metadata.</p>

      <h2>Your forwarding address</h2>
      <div className="card">
        {alias ? (
          <p><code className="big">{alias}</code></p>
        ) : (
          <p className="muted">Forwarding address alias is currently unavailable.</p>
        )}
        <p className="muted" style={{ margin: "8px 0 0 0" }}>
          Forward suspicious emails to this address. We recommend forwarding as an attachment so original authentication headers (SPF, DKIM, DMARC) remain intact.
        </p>
      </div>

      <h2>Establish sender baseline</h2>
      <p className="muted">
        Upload emails you know are genuine. After establishing history for a sender, PhishLens flags anomalies when future messages deviate from established patterns.
      </p>
      <UploadBox
        label="Add known-good email"
        hint="Only upload messages from verified trusted contacts."
        onFile={async (f) => {
          const r = await api.baseline(f);
          setMsg(`${r.sender}: recorded ${r.message_count} trusted message(s). ${r.note}`);
        }}
      />
      {msg && <div className="card low" style={{ padding: "12px 16px" }}><p style={{ margin: 0 }}>{msg}</p></div>}

      <h2>Active model card</h2>
      <div className="card">
        {error && <p className="error" role="alert">{error}</p>}
        {model ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div>Algorithm: <strong>{model.algorithm}</strong></div>
            <div>Version tag: <code className="mono">{model.version_tag}</code></div>
            <div>Feature count: <span className="mono">{model.n_features}</span></div>
            <div className={model.data_source.startsWith("synthetic") ? "error" : "muted"}>
              Training data source: {model.data_source}
            </div>
            <p className="muted" style={{ margin: "8px 0 0 0", fontSize: "0.9rem", maxWidth: "68ch" }}>
              Note: The bundled model is trained on synthetic data and serves as a pipeline demonstration only. Its reported evaluation metrics are not evidence of real-world phishing detection performance.
            </p>
          </div>
        ) : (
          <p className="muted">No model registry information loaded.</p>
        )}
      </div>
    </>
  );
}
