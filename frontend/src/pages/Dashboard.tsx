import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import UploadBox from "../components/UploadBox";
import type { AnalysisSummary, Band } from "../types";

const SCOPE_LABEL: Record<string, string> = {
  direct: "Uploaded directly",
  forward_attachment: "Forwarded as attachment",
  forward_inline: "Forwarded inline",
};

export default function Dashboard() {
  const nav = useNavigate();
  const [items, setItems] = useState<AnalysisSummary[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Band | "ALL">("ALL");
  const [search, setSearch] = useState("");

  const load = useCallback(() => {
    setItems(null);
    setError(null);
    api.list(100, 0)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
        setError(null);
      })
      .catch((e) => {
        setError((e as Error).message);
        setItems([]);
      });
  }, []);

  useEffect(load, [load]);

  const loadedCount = items?.length ?? 0;
  const lowCount = items?.filter((i) => i.risk_band === "LOW").length ?? 0;
  const medCount = items?.filter((i) => i.risk_band === "MEDIUM").length ?? 0;
  const highCount = items?.filter((i) => i.risk_band === "HIGH").length ?? 0;
  const isCapped = total > 100;

  const filteredItems = items?.filter((item) => {
    if (filter !== "ALL" && item.risk_band !== filter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const subj = (item.subject || "").toLowerCase();
      const sender = (item.sender_address || "").toLowerCase();
      const name = (item.sender_name || "").toLowerCase();
      if (!subj.includes(q) && !sender.includes(q) && !name.includes(q)) return false;
    }
    return true;
  });

  return (
    <>
      <div className="row" style={{ alignItems: "baseline", marginBottom: "16px" }}>
        <div>
          <h1>Phishing triage console</h1>
          <p className="muted">
            Inspect suspicious communications, verify evidence rules against parsed headers, and review risk bands.
          </p>
        </div>
        <div>
          <button className="secondary" onClick={load} type="button">Refresh list</button>
        </div>
      </div>

      <UploadBox
        label="Analyze new email"
        hint="Drop an .eml, message/rfc822, or .txt file here. In mail clients, choose download message."
        onFile={async (f) => {
          const a = await api.upload(f);
          nav(`/analyses/${a.id}`);
        }}
      />

      {error ? (
        <div className="card high" style={{ padding: "16px" }}>
          <p className="error" role="alert">Failed to load analyses: {error}</p>
          <button onClick={load} style={{ marginTop: "8px" }} type="button">Retry</button>
        </div>
      ) : (
        <>
          {/* Stat Strip */}
          <div className="stat-strip">
            <div className="stat-card">
              <div className="stat-label">Total analyses</div>
              <div className="stat-value mono">{total}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">High risk</div>
              <div className="stat-value mono" style={{ color: "var(--high)" }}>{highCount}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Medium risk</div>
              <div className="stat-value mono" style={{ color: "var(--medium)" }}>{medCount}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Low risk</div>
              <div className="stat-value mono" style={{ color: "var(--low)" }}>{lowCount}</div>
            </div>
          </div>
          <p className="muted" style={{ fontSize: "0.85rem", marginTop: "-12px", marginBottom: "16px" }}>
            {isCapped ? `Band counts reflect the latest 100 analyses. Total records: ${total}.` : `Band counts cover all ${total} analyses.`}
          </p>

          <div className="toolbar">
            <div>
              <h2 style={{ margin: 0 }}>Analysis queue <span className="muted" style={{ fontWeight: 400, fontSize: "0.9rem" }}>({isCapped ? `Latest 100 of ${total} records` : `${total} records`})</span></h2>
            </div>
            <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
              <div className="filters" role="group" aria-label="Filter by risk band">
                <button
                  className="filter-btn"
                  aria-pressed={filter === "ALL"}
                  onClick={() => setFilter("ALL")}
                  type="button"
                >
                  All ({loadedCount})
                </button>
                <button
                  className="filter-btn"
                  aria-pressed={filter === "HIGH"}
                  onClick={() => setFilter("HIGH")}
                  type="button"
                >
                  High ({highCount})
                </button>
                <button
                  className="filter-btn"
                  aria-pressed={filter === "MEDIUM"}
                  onClick={() => setFilter("MEDIUM")}
                  type="button"
                >
                  Medium ({medCount})
                </button>
                <button
                  className="filter-btn"
                  aria-pressed={filter === "LOW"}
                  onClick={() => setFilter("LOW")}
                  type="button"
                >
                  Low ({lowCount})
                </button>
              </div>
              <input
                type="text"
                className="search-input"
                placeholder="Search subject or sender..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="Search analyses"
              />
            </div>
          </div>

          {items === null ? (
            <div role="status" aria-busy="true">
              <span className="sr-only">Loading analyses</span>
              <div className="skeleton-row" />
              <div className="skeleton-row" />
              <div className="skeleton-row" />
            </div>
          ) : items.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "40px" }}>
              <p className="muted" style={{ fontSize: "1.05rem" }}>No analyses yet.</p>
              <p className="muted">Use the upload area above or forward an email to your alias to begin triage.</p>
            </div>
          ) : filteredItems?.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "40px" }}>
              <p className="muted" style={{ fontSize: "1.05rem" }}>No analyses match the current filter or search criteria.</p>
              <button
                className="secondary"
                onClick={() => { setFilter("ALL"); setSearch(""); }}
                style={{ marginTop: "12px" }}
                type="button"
              >
                Clear filters
              </button>
            </div>
          ) : (
            <div className="analysis-list">
              {filteredItems?.map((a) => (
                <Link key={a.id} to={`/analyses/${a.id}`} className="analysis-row">
                  <div>
                    <RiskBadge band={a.risk_band} score={a.risk_score} />
                  </div>
                  <div>
                    <div className="analysis-row-subject" title={a.subject || "(no subject)"}>{a.subject || "(no subject)"}</div>
                    <div className="analysis-row-sender" title={`${a.sender_name ? `${a.sender_name} ` : ""}<${a.sender_address}>`}>
                      {a.sender_name ? `${a.sender_name} ` : ""}
                      <span className="mono">&lt;{a.sender_address}&gt;</span>
                    </div>
                  </div>
                  <div className="muted" style={{ fontSize: "0.85rem" }}>
                    {SCOPE_LABEL[a.scope] ?? a.scope}
                  </div>
                  <div className="analysis-row-meta">
                    {new Date(a.created_at + "Z").toLocaleString()}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </>
  );
}
