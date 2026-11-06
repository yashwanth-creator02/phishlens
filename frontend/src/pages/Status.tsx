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
      <p className="muted">Last checked {checkedAt}</p>

      <div className="grid2">
        <article className="card">
          <h2>API</h2>
          <dl className="facts">
            <div><dt>State</dt><dd>{health.status}</dd></div>
            <div><dt>Model loaded</dt><dd>{health.model_loaded ? "Yes" : "No"}</dd></div>
            <div><dt>Auth mode</dt><dd>{health.auth_mode}</dd></div>
            {health.model && <div><dt>Model</dt><dd>{health.model}</dd></div>}
            {health.detail && <div><dt>Detail</dt><dd>{health.detail}</dd></div>}
          </dl>
        </article>

        <article className="card">
          <h2>Model</h2>
          <dl className="facts">
            <div><dt>Version</dt><dd>{model.version_tag}</dd></div>
            <div><dt>Algorithm</dt><dd>{model.algorithm}</dd></div>
            <div><dt>Features</dt><dd>{model.n_features}</dd></div>
            <div><dt>Data source</dt><dd>{model.data_source}</dd></div>
            {model.trained_at && <div><dt>Trained at</dt><dd>{model.trained_at}</dd></div>}
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
