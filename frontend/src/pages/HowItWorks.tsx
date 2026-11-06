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

      <ol className="how-steps">
        <li>
          <h3>1. Parsing</h3>
          <p>
            The backend parses the email whether it is uploaded directly, forwarded inline, or
            forwarded as a <code className="mono">message/rfc822</code> attachment. Inline
            forwarding loses the original SPF, DKIM, and DMARC headers, so they are stored as
            missing, not failed. Attachments keep metadata only and are never opened or executed.
          </p>
        </li>
        <li>
          <h3>2. Feature extraction</h3>
          <p>
            A single 57-feature vector is computed from six groups. Training and serving share the
            same feature names and order; the model registry rejects mismatched artifacts.
          </p>
        </li>
        <li>
          <h3>3. Prediction</h3>
          <p>
            The active tree or linear model scores the vector, an optional isotonic calibration
            turns the raw output into a probability, and the probability becomes a 0-100 score.
          </p>
        </li>
        <li>
          <h3>4. SHAP contributions</h3>
          <p>
            SHAP assigns each feature a contribution: positive pushes toward phishing, negative
            pushes away. The case report shows the 20 largest absolute contributions.
          </p>
        </li>
        <li>
          <h3>5. Verifying reasons against evidence</h3>
          <p>
            Plain-language reasons are generated from the largest positive contributions, but a
            reason is shown only if its evidence rule verifies against the parsed email. If a
            MEDIUM or HIGH result has no verified reason, the UI shows a generic fallback instead
            of an invented claim.
          </p>
        </li>
        <li>
          <h3>6. Risk bands</h3>
          <p>
            Score 0-100 maps to LOW, MEDIUM, or HIGH using configurable thresholds (provisional:
            LOW up to 29, HIGH from 70). The band and the guidance text are stored with the
            analysis so past results stay explainable after retuning. Sender history is updated
            only when the result is LOW.
          </p>
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
