import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ModelInfo } from "../types";
import "../styles/report.css";

export default function ModelPage() {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.model().then(setModel).catch((e) => setError((e as Error).message));
  }, []);

  const metricEntries = model ? Object.entries(model.metrics) : [];

  return (
    <>
      <div className="row" style={{ alignItems: "baseline", marginBottom: "8px" }}>
        <div>
          <h1>Model card</h1>
          <p className="muted">
            Active scoring model from <code className="mono">GET /api/model</code>: training source,
            metrics, band thresholds, and limitations.
          </p>
        </div>
        <button className="secondary" onClick={() => window.location.reload()} type="button">
          Refresh
        </button>
      </div>

      {error && (
        <div className="card high">
          <p className="error" role="alert">
            Failed to load model information: {error}
          </p>
        </div>
      )}

      {!model && !error && (
        <p className="muted pad" role="status">
          Loading model information...
        </p>
      )}

      {model && (
        <>
          <div className="model-grid">
            <section className="card" aria-labelledby="model-identity-heading">
              <h2 id="model-identity-heading" style={{ marginTop: 0 }}>
                Active model
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div>
                  Algorithm: <strong>{model.algorithm}</strong>
                </div>
                <div>
                  Version tag: <code className="mono">{model.version_tag}</code>
                </div>
                <div>
                  Feature count: <span className="mono">{model.n_features}</span>
                </div>
                <div>
                  Trained at:{" "}
                  {model.trained_at ? new Date(model.trained_at).toLocaleString() : "Not recorded"}
                </div>
                <div className={model.data_source.startsWith("synthetic") ? "error" : undefined}>
                  Training data source: <strong>{model.data_source}</strong>
                </div>
              </div>

              <h3 style={{ marginTop: "24px" }}>Risk band thresholds</h3>
              <p className="muted" style={{ fontSize: "0.9rem" }}>
                Score is the calibrated probability scaled to 0-100. Bands are configurable on the
                server and stored with each analysis.
              </p>
              <div className="threshold-row">
                <div className="threshold-card">
                  <div className="stat-label">LOW (0 - 29)</div>
                  <div className="threshold-value" style={{ color: "var(--low)" }}>
                    LOW
                  </div>
                  <div className="muted" style={{ fontSize: "0.9rem" }}>
                    No strong warning signs.
                  </div>
                </div>
                <div className="threshold-card">
                  <div className="stat-label">MEDIUM (30 - 69)</div>
                  <div className="threshold-value" style={{ color: "var(--medium)" }}>
                    MEDIUM
                  </div>
                  <div className="muted" style={{ fontSize: "0.9rem" }}>
                    Some warning signs.
                  </div>
                </div>
                <div className="threshold-card">
                  <div className="stat-label">HIGH (70 - 100)</div>
                  <div className="threshold-value" style={{ color: "var(--high)" }}>
                    HIGH
                  </div>
                  <div className="muted" style={{ fontSize: "0.9rem" }}>
                    Strong warning signs.
                  </div>
                </div>
              </div>

              <h3 style={{ marginTop: "24px" }}>Limitations</h3>
              <ul className="plain" style={{ listStyle: "disc", paddingLeft: "20px" }}>
                <li>
                  {model.data_source.startsWith("synthetic")
                    ? "Bundled model is trained on synthetic data as a pipeline demonstration only. Its metrics are not evidence of real-world phishing detection performance."
                    : "Reported metrics come from the recorded training run. Treat them as test-set figures, not a promise on new mail."}
                </li>
                <li>
                  {model.data_source.startsWith("synthetic")
                    ? "The corpus-trained model measures a 1.8% false-positive rate on 2,865 held-out legitimate messages from a modern inbox, and catches 77% of held-out phishing. One inbox, one provider, one point in time: a floor, not a population estimate."
                    : "This model was fitted on one modern inbox and on a phishing corpus that ends in 2025. It misses some phishing, and its false-positive rate is higher for financial and transactional mail than for ordinary mail."}
                </li>                <li>
                  Sender history updates only from known-good uploads and LOW-risk results. MEDIUM
                  and HIGH messages never train the behavioural profile.
                </li>
                <li>
                  Inline forwarding drops the original SPF, DKIM, and DMARC headers, so those
                  checks are reported as missing, not failed.
                </li>
                <li>
                  Attachments are scored by metadata only and are never opened, executed, or
                  rendered.
                </li>
                <li>
                  Reasons are shown only when an evidence rule verifies the claim against the parsed
                  email. A MEDIUM/HIGH result with no verified reason uses a generic fallback.
                </li>
              </ul>
            </section>

            <section className="card" aria-labelledby="model-metrics-heading">
              <h2 id="model-metrics-heading" style={{ marginTop: 0 }}>
                Training metrics
              </h2>
              {metricEntries.length === 0 ? (
                <p className="muted">No metrics recorded for this model.</p>
              ) : (
                <table className="list small metric-table">
                  <caption>Metrics recorded at training time</caption>
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metricEntries.map(([name, value]) => (
                      <tr key={name}>
                        <td className="mono">{name}</td>
                        <td className="mono">
                          {typeof value === "number"
                            ? value % 1 !== 0
                              ? value.toFixed(4)
                              : String(value)
                            : String(value)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <p className="muted" style={{ fontSize: "0.9rem", marginTop: "16px" }}>
                {model.data_source.startsWith("synthetic")
                  ? "Do not claim model quality from a synthetic demo model. Real-corpus evaluation is reported separately and is not shown as a product guarantee."
                  : "These are the training-run figures on its own test split. The measured behaviour on modern mail, with its false-positive rate and the gates it misses, is in docs/21-modern-corpus-evaluation-plan.md and is not shown here as a product guarantee."}
              </p>
            </section>
          </div>

          <p className="muted" style={{ marginTop: "24px", fontSize: "0.9rem" }}>
            Feature contract: training and serving use the same 65-feature vector in the same order.
            The model registry rejects artifacts whose feature names do not match the serving code.
          </p>
        </>
      )}
    </>
  );
}
