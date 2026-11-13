import "../styles/report.css";

export default function HowItWorksPage() {
  return (
    <>
      <div className="row" style={{ alignItems: "baseline", marginBottom: "8px" }}>
        <div>
          <h1>How it works</h1>
          <p className="muted">
            From a forwarded email to an evidence-verified risk band, in six steps.
          </p>
        </div>
      </div>

      <ol className="how-steps-grid">
        <li className="how-step-card">
          <div className="how-step-num" aria-hidden="true">01</div>
          <div className="how-step-content">
            <h3>Parsing & Ingestion</h3>
            <p>
              The backend parses the email whether it is uploaded directly, forwarded inline, or
              forwarded as a <code className="mono">message/rfc822</code> attachment. Inline
              forwarding loses the original SPF, DKIM, and DMARC headers, so they are stored as
              missing, not failed. Attachments keep metadata only and are never opened or executed.
            </p>
          </div>
        </li>
        <li className="how-step-card">
          <div className="how-step-num" aria-hidden="true">02</div>
          <div className="how-step-content">
            <h3>65-Feature Vector Extraction</h3>
            <p>
              A single 65-feature vector is computed across six core groups. Training and serving share the
              identical feature names and order; the model registry strictly rejects mismatched artifacts.
            </p>
          </div>
        </li>
        <li className="how-step-card">
          <div className="how-step-num" aria-hidden="true">03</div>
          <div className="how-step-content">
            <h3>Tree-Ensemble Prediction & Calibration</h3>
            <p>
              The active XGBoost tree ensemble scores the feature vector. Isotonic regression calibration
              maps raw outputs into a calibrated probability, scaled to a continuous 0–100 risk score.
            </p>
          </div>
        </li>
        <li className="how-step-card">
          <div className="how-step-num" aria-hidden="true">04</div>
          <div className="how-step-content">
            <h3>SHAP Attribution Engine</h3>
            <p>
              TreeExplainer computes Shapley Additive Explanations: positive contributions push toward phishing,
              negative push toward legitimate. The incident report ranks top contributions by absolute magnitude.
            </p>
          </div>
        </li>
        <li className="how-step-card">
          <div className="how-step-num" aria-hidden="true">05</div>
          <div className="how-step-content">
            <h3>Ground-Truth Evidence Verification</h3>
            <p>
              Plain-language reasons are generated from the largest positive contributions, but a
              reason is shown only if its evidence rule verifies against the parsed email. If a
              MEDIUM or HIGH result has no verified reason, the UI shows a generic fallback instead
              of an invented claim.
            </p>
          </div>
        </li>
        <li className="how-step-card">
          <div className="how-step-num" aria-hidden="true">06</div>
          <div className="how-step-content">
            <h3>Calibrated Three-Tier Triage Bands</h3>
            <p>
              Score 0–100 maps to LOW, MEDIUM, or HIGH using calibrated operating thresholds (LOW up to 29,
              HIGH from 70). The band and guidance text are stored with the analysis for auditability.
              Sender history baseline updates only when the result is LOW.
            </p>
          </div>
        </li>
      </ol>

      <h2>Six feature groups</h2>
      <div className="feature-groups">
        <section className="group-card">
          <h3>1. Header</h3>
          <p>Sender, reply-to, and authentication results (SPF, DKIM, DMARC).</p>
        </section>
        <section className="group-card">
          <h3>2. URL</h3>
          <p>Link counts, display-text mismatches, and host patterns.</p>
        </section>
        <section className="group-card">
          <h3>3. Text</h3>
          <p>Word counts, urgency language, and credential-request wording.</p>
        </section>
        <section className="group-card">
          <h3>4. Action</h3>
          <p>Requested actions: click, reply, call, open, or pay.</p>
        </section>
        <section className="group-card">
          <h3>5. Attachment</h3>
          <p>Attachment count, types, and metadata only. Never opened or rendered.</p>
        </section>
        <section className="group-card">
          <h3>6. Behavioral</h3>
          <p>Sender history: how often this sender was seen before and how the message deviates.</p>
        </section>
      </div>

      <div className="note" style={{ marginTop: "24px" }}>
        <strong>Why evidence verification?</strong> A large SHAP value says the model used a
        feature; it does not prove the claim is true of this email. Every specific reason must pass
        a check against the parsed headers, links, text, or attachments before it is shown.
      </div>

      <p className="muted" style={{ marginTop: "16px", fontSize: "0.95rem" }}>
        The bundled demo model is trained on synthetic data as a pipeline demonstration only. Its
        metrics are not evidence of real-world phishing detection performance.
      </p>
    </>
  );
}
