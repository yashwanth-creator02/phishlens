import { useEffect, useState } from "react";
import { api } from "../api/client";
import UploadBox from "../components/UploadBox";
import type { ModelInfo } from "../types";

export default function Settings() {
  const [alias, setAlias] = useState<string | null>(null);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    api.alias().then((a) => setAlias(a.address)).catch(() => setAlias(null));
    api.model().then(setModel).catch(() => setModel(null));
  }, []);

  return (
    <>
      <h1>Settings</h1>
      <h2>Your forwarding address</h2>
      {alias ? <p><code className="big">{alias}</code></p> : <p className="muted">Unavailable.</p>}
      <p className="muted">Forward suspicious emails to this address. Prefer “Forward as attachment” so the original
        headers (SPF, DKIM, DMARC) are preserved.</p>

      <h2>Teach PhishLens what is normal</h2>
      <p className="muted">Upload emails you know are genuine. After a few messages from the same sender, PhishLens can notice
        when a later message does not look like that sender.</p>
      <UploadBox label="Add a known-good email" hint="Only upload messages you trust." onFile={async (f) => {
        const r = await api.baseline(f);
        setMsg(`${r.sender}: ${r.message_count} trusted message(s). ${r.note}`);
      }} />
      {msg && <p>{msg}</p>}

      <h2>Model</h2>
      {model ? (
        <>
          <p>{model.algorithm} · <code>{model.version_tag}</code> · {model.n_features} features</p>
          <p className={model.data_source.startsWith("synthetic") ? "error" : "muted"}>Training data: {model.data_source}</p>
        </>
      ) : <p className="muted">No model loaded.</p>}
    </>
  );
}
