import { useRef, useState, useId } from "react";

interface Props {
  label: string;
  hint: string;
  onFile: (file: File) => Promise<void>;
}

const SAMPLE_EMAILS = [
  { name: "PayPal Phishing", file: "phish_paypal_direct.eml", type: "phish" },
  { name: "Invoice Phishing (Inline)", file: "phish_invoice_forwarded_inline.eml", type: "phish" },
  { name: "Bank Security Alert (Legit)", file: "legit_bank_alert.eml", type: "legit" },
  { name: "Weekly Newsletter (Legit)", file: "legit_newsletter.eml", type: "legit" },
];

export default function UploadBox({ label, hint, onFile }: Props) {
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState<string>("Analysing email...");
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleFile(file: File | undefined, labelName?: string) {
    if (!file) return;
    setFileName(labelName ?? file.name);
    setBusy(true);
    setBusyLabel("Extracting 65 features and scoring...");
    setError(null);
    try {
      await onFile(file);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function loadSample(sample: typeof SAMPLE_EMAILS[number]) {
    setBusy(true);
    setBusyLabel(`Loading sample: ${sample.name}...`);
    setError(null);
    try {
      const res = await fetch(`/samples/${sample.file}`);
      if (!res.ok) throw new Error(`Could not load ${sample.file}`);
      const blob = await res.blob();
      const file = new File([blob], sample.file, { type: "message/rfc822" });
      await handleFile(file, sample.name);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  return (
    <div
      className={`upload-container ${dragOver ? "dragover" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          setDragOver(false);
        }
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        void handleFile(e.dataTransfer.files[0]);
      }}
    >
      <div className="upload-icon-wrap" aria-hidden="true">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </div>

      <strong className="upload-title">{label}</strong>
      <p className="muted upload-hint">{hint}</p>

      <div className="upload-formats-strip">
        <span className="upload-format-chip">.EML</span>
        <span className="upload-format-chip">RFC-822</span>
        <span className="upload-format-chip">.TXT</span>
        <span className="upload-format-chip">MAX 10 MB</span>
      </div>

      {fileName && <p className="mono muted upload-selected">Selected: {fileName}</p>}

      <input
        id={inputId}
        ref={fileInputRef}
        type="file"
        className="sr-only"
        accept=".eml,message/rfc822,.txt"
        onChange={(e) => void handleFile(e.target.files?.[0])}
      />

      <label htmlFor={inputId} className="upload-btn-label">
        Choose email file
      </label>

      {busy && (
        <p className="muted" role="status" style={{ marginTop: "12px", fontWeight: 500 }}>
          {busyLabel}
        </p>
      )}

      {error && (
        <p className="error" role="alert" style={{ marginTop: "12px" }}>
          {error}
        </p>
      )}

      {/* Quick Test Samples */}
      <div className="upload-samples-section">
        <span className="upload-samples-label">Or quick-test with demo emails:</span>
        <div className="upload-samples-list">
          {SAMPLE_EMAILS.map((s) => (
            <button
              key={s.file}
              type="button"
              className={`upload-sample-btn ${s.type}`}
              onClick={() => void loadSample(s)}
              disabled={busy}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
