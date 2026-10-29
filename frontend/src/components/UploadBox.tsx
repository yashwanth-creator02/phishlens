import { useRef, useState } from "react";

interface Props {
  label: string;
  hint: string;
  onFile: (file: File) => Promise<void>;
}

export default function UploadBox({ label, hint, onFile }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handle(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await onFile(file);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div
      className="upload"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        void handle(e.dataTransfer.files[0]);
      }}
    >
      <strong>{label}</strong>
      <p className="muted">{hint}</p>
      <input ref={input} type="file" accept=".eml,message/rfc822,.txt" onChange={(e) => void handle(e.target.files?.[0])} />
      {busy && <p className="muted">Analysing…</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
