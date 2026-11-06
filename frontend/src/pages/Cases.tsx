import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import { filterCases, paginate } from "../lib/cases";
import type { AnalysisSummary, Band } from "../types";

type SortKey = "date_desc" | "date_asc" | "risk_desc" | "risk_asc" | "subject_asc";

const SCOPE_LABEL: Record<string, string> = {
  direct: "Uploaded directly",
  forward_attachment: "Forwarded as attachment",
  forward_inline: "Forwarded inline",
};

export default function Cases() {
  const [items, setItems] = useState<AnalysisSummary[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [band, setBand] = useState<Band | "ALL">("ALL");
  const [sort, setSort] = useState<SortKey>("date_desc");
  const [pageSize, setPageSize] = useState(20);
  const [page, setPage] = useState(1);

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

  const filtered = useMemo(() => {
    if (!items) return [];
    let out = filterCases(items, { query, band });

    // Sort
    out = [...out].sort((a, b) => {
      switch (sort) {
        case "date_desc":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case "date_asc":
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case "risk_desc":
          return b.risk_score - a.risk_score;
        case "risk_asc":
          return a.risk_score - b.risk_score;
        case "subject_asc":
          return (a.subject || "").localeCompare(b.subject || "");
        default:
          return 0;
      }
    });

    return out;
  }, [items, query, band, sort]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [query, band, sort, pageSize]);

  const { rows, pages, total: filteredTotal } = paginate(filtered, page, pageSize);

  const highCount = items?.filter((i) => i.risk_band === "HIGH").length ?? 0;
  const medCount = items?.filter((i) => i.risk_band === "MEDIUM").length ?? 0;
  const lowCount = items?.filter((i) => i.risk_band === "LOW").length ?? 0;
  const loadedCount = items?.length ?? 0;

  return (
    <>
      <div className="row" style={{ alignItems: "baseline", marginBottom: "16px" }}>
        <div>
          <h1>Cases</h1>
          <p className="muted">Browse all analyses with search, band filter, sort, and pagination.</p>
        </div>
        <div>
          <button className="secondary" onClick={load} type="button">Refresh</button>
        </div>
      </div>

      {error ? (
        <div className="card high" style={{ padding: "16px" }}>
          <p className="error" role="alert">Failed to load cases: {error}</p>
          <button onClick={load} style={{ marginTop: "8px" }} type="button">Retry</button>
        </div>
      ) : (
        <>
          {/* Controls */}
          <div className="controls-grid">
            <input
              type="text"
              className="search-input"
              placeholder="Search subject or sender..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search cases"
            />

            <div className="filters" role="group" aria-label="Filter by risk band">
              <button
                className="filter-btn"
                aria-pressed={band === "ALL"}
                onClick={() => setBand("ALL")}
                type="button"
              >
                All ({loadedCount})
              </button>
              <button
                className="filter-btn"
                aria-pressed={band === "HIGH"}
                onClick={() => setBand("HIGH")}
                type="button"
              >
                High ({highCount})
              </button>
              <button
                className="filter-btn"
                aria-pressed={band === "MEDIUM"}
                onClick={() => setBand("MEDIUM")}
                type="button"
              >
                Medium ({medCount})
              </button>
              <button
                className="filter-btn"
                aria-pressed={band === "LOW"}
                onClick={() => setBand("LOW")}
                type="button"
              >
                Low ({lowCount})
              </button>
            </div>

            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              aria-label="Sort by"
              className="select-input"
            >
              <option value="date_desc">Newest first</option>
              <option value="date_asc">Oldest first</option>
              <option value="risk_desc">Highest risk</option>
              <option value="risk_asc">Lowest risk</option>
              <option value="subject_asc">Subject A-Z</option>
            </select>

            <select
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
              aria-label="Page size"
              className="select-input"
            >
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
          </div>

          {/* Content states */}
          {items === null ? (
            <div role="status" aria-busy="true">
              <span className="sr-only">Loading cases</span>
              <div className="skeleton-row" />
              <div className="skeleton-row" />
              <div className="skeleton-row" />
            </div>
          ) : items.length === 0 ? (
            <div className="empty-state">
              <p className="muted" style={{ fontSize: "1.05rem" }}>No cases yet.</p>
              <p className="muted">Upload an email from the dashboard to get started.</p>
              <Link to="/" className="btn" style={{ marginTop: "16px", textDecoration: "none" }}>
                Go to dashboard
              </Link>
            </div>
          ) : filteredTotal === 0 ? (
            <div className="empty-state">
              <p className="muted" style={{ fontSize: "1.05rem" }}>No cases match the current filters.</p>
              <button
                className="secondary"
                onClick={() => {
                  setQuery("");
                  setBand("ALL");
                }}
                style={{ marginTop: "12px" }}
                type="button"
              >
                Clear filters
              </button>
            </div>
          ) : (
            <>
              <p className="muted" style={{ marginTop: "16px" }}>
                Showing {rows.length} of {filteredTotal} cases
                {total > 100 ? ` • Total records: ${total}` : ""}
              </p>
              <div className="analysis-list">
                {rows.map((a) => (
                  <Link key={a.id} to={`/analyses/${a.id}`} className="analysis-row">
                    <div>
                      <RiskBadge band={a.risk_band} score={a.risk_score} />
                    </div>
                    <div>
                      <div className="analysis-row-subject" title={a.subject || "(no subject)"}>
                        {a.subject || "(no subject)"}
                      </div>
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

              {/* Pagination */}
              <nav className="pagination" aria-label="Pagination">
                <button
                  className="secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  type="button"
                >
                  Previous
                </button>
                <span className="muted">
                  Page {Math.min(page, pages)} of {pages}
                </span>
                <button
                  className="secondary"
                  disabled={page >= pages}
                  onClick={() => setPage((p) => Math.min(pages, p + 1))}
                  type="button"
                >
                  Next
                </button>
              </nav>
            </>
          )}
        </>
      )}
    </>
  );
}