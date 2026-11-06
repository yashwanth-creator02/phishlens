import type { AnalysisSummary, Band } from "../types";

export function filterCases(
  items: AnalysisSummary[],
  { query, band }: { query?: string; band?: Band | "ALL" }
): AnalysisSummary[] {
  let result = items;

  if (band && band !== "ALL") {
    result = result.filter((item) => item.risk_band === band);
  }

  if (query?.trim()) {
    const q = query.toLowerCase().trim();
    result = result.filter(
      (item) =>
        (item.subject || "").toLowerCase().includes(q) ||
        (item.sender_address || "").toLowerCase().includes(q) ||
        (item.sender_name || "").toLowerCase().includes(q)
    );
  }

  return result;
}

export function paginate<T>(
  items: T[],
  page: number,
  size: number
): { rows: T[]; page: number; pages: number; total: number } {
  const total = items.length;
  const pages = size > 0 ? Math.max(1, Math.ceil(total / size)) : 1;
  const clampedPage = Math.max(1, Math.min(page, pages));
  const start = size > 0 ? (clampedPage - 1) * size : 0;
  const end = size > 0 ? start + size : total;
  const rows = items.slice(start, end);
  return { rows, page: clampedPage, pages, total };
}