import { useRef, useState, useId } from "react";

interface Props {
  label: string;
  hint: string;
  onFile: (file: File) => Promise<void>;
}

export default function UploadBox({ label, hint, onFile }: Props) {
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setFileName(file.name);
    setBusy(true);
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
      <strong>{label}</strong>
      <p className="muted" style={{ margin: "6px 0 12px 0" }}>{hint}</p>
      {fileName && <p className="mono muted" style={{ fontSize: "0.9rem" }}>Selected: {fileName}</p>}
      
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
        <p className="muted" role="status" style={{ marginTop: "12px" }}>
          Analysing email...
        </p>
      )}
      {error && (
        <p className="error" role="alert" style={{ marginTop: "12px" }}>
          {error}
        </p>
      )}
    </div>
  );
}
