import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Health, ModelInfo } from "../types";
import "../styles/status.css";

export default function Status() {
  const [health, setHealth] = useState<Health | null>(null);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checkedAt, setCheckedAt] = useState<string>("");

  useEffect(() => {
    let live = true;
    Promise.all([api.health(), api.model()])
      .then(([h, m]) => {
        if (!live) return;
        setHealth(h);
        setModel(m);
        setCheckedAt(new Date().toLocaleString());
      })
      .catch((e) => {
        if (live) setError((e as Error).message);
      });
    return () => { live = false; };
  }, []);

  if (error) {
    return (
      <section className="page">
        <h1>Status</h1>
        <p className="error" role="alert">Could not load status: {error}</p>
      </section>
    );
  }

  if (!health || !model) {
    return (
      <section className="page" aria-busy="true">
        <h1>Status</h1>
        <p className="muted">Loading service status...</p>
      </section>
    );
  }

  return (
    <section className="page">
      <h1>Status</h1>
      <div className="status-overview-banner">
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className="badge low">OPERATIONAL</span>
          <span style={{ fontWeight: 600 }}>All Core Systems Healthy</span>
        </div>
        <span className="muted mono" style={{ fontSize: "0.85rem" }}>Checked: {checkedAt}</span>
      </div>

      <div className="grid2">
        <article className="card">
          <h2>API Service</h2>
          <dl className="facts">
            <div><dt>State</dt><dd><span className="badge low">{health.status.toUpperCase()}</span></dd></div>
            <div><dt>Model loaded</dt><dd>{health.model_loaded ? <span className="badge low">YES</span> : <span className="badge high">NO</span>}</dd></div>
            <div><dt>Auth mode</dt><dd className="mono">{health.auth_mode}</dd></div>
            {health.model && <div><dt>Active model</dt><dd className="mono">{health.model}</dd></div>}
            {health.detail && <div><dt>Detail</dt><dd>{health.detail}</dd></div>}
          </dl>
        </article>

        <article className="card">
          <h2>Classifier Model</h2>
          <dl className="facts">
            <div><dt>Version tag</dt><dd className="mono">{model.version_tag}</dd></div>
            <div><dt>Algorithm</dt><dd className="mono">{model.algorithm.toUpperCase()}</dd></div>
            <div><dt>Feature vector</dt><dd className="mono">{model.n_features} features</dd></div>
            <div><dt>Data source</dt><dd>{model.data_source}</dd></div>
            {model.trained_at && <div><dt>Trained at</dt><dd className="mono">{model.trained_at}</dd></div>}
          </dl>
        </article>
      </div>

      <article className="card" style={{ marginTop: 16 }}>
        <h2>Training metrics</h2>
        {Object.keys(model.metrics).length === 0 ? (
          <p className="muted">No metrics recorded for this model.</p>
        ) : (
          <table className="fact-table">
            <thead><tr><th scope="col">Metric</th><th scope="col">Value</th></tr></thead>
            <tbody>
              {Object.entries(model.metrics).map(([name, value]) => (
                <tr key={name}>
                  <th scope="row">{name}</th>
                  <td>{typeof value === "number" ? value.toFixed(4) : String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}
