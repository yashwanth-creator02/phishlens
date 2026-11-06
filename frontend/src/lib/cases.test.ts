import { describe, it, expect } from "vitest";
import { filterCases, paginate } from "./cases";
import type { AnalysisSummary } from "../types";

const mockCases: AnalysisSummary[] = [
  {
    id: "1",
    created_at: "2024-01-01T00:00:00Z",
    sender_address: "attacker@phish.com",
    sender_name: "Attacker",
    subject: "Urgent: Bank Account Update Required",
    scope: "forward_inline",
    risk_score: 85,
    risk_band: "HIGH",
    model_version: "v1",
  },
  {
    id: "2",
    created_at: "2024-01-02T00:00:00Z",
    sender_address: "trusted@company.com",
    sender_name: "Trusted Corp",
    subject: "Weekly Report",
    scope: "direct",
    risk_score: 10,
    risk_band: "LOW",
    model_version: "v1",
  },
  {
    id: "3",
    created_at: "2024-01-03T00:00:00Z",
    sender_address: "scam@fake.net",
    sender_name: "Scammer",
    subject: "Invoice Payment Due",
    scope: "forward_attachment",
    risk_score: 72,
    risk_band: "MEDIUM",
    model_version: "v1",
  },
  {
    id: "4",
    created_at: "2024-01-04T00:00:00Z",
    sender_address: "bank@legit.org",
    sender_name: "Legit Bank",
    subject: "Your Account Statement",
    scope: "direct",
    risk_score: 25,
    risk_band: "LOW",
    model_version: "v1",
  },
  {
    id: "5",
    created_at: "2024-01-05T00:00:00Z",
    sender_address: "noreply@service.io",
    sender_name: "Service Alert",
    subject: "Password Reset Requested",
    scope: "forward_inline",
    risk_score: 60,
    risk_band: "MEDIUM",
    model_version: "v1",
  },
];

describe("filterCases", () => {
  it("filters by sender and band", () => {
    const rows = filterCases(mockCases, { query: "bank", band: "HIGH" });
    expect(rows).toHaveLength(1);
    expect(rows[0].id).toBe("1");
  });

  it("matches query against subject, sender, and name", () => {
    const rows = filterCases(mockCases, { query: "trusted" });
    expect(rows).toHaveLength(1);
    expect(rows[0].id).toBe("2");

    const rows2 = filterCases(mockCases, { query: "invoice" });
    expect(rows2).toHaveLength(1);
    expect(rows2[0].id).toBe("3");

    const rows3 = filterCases(mockCases, { query: "password" });
    expect(rows3).toHaveLength(1);
    expect(rows3[0].id).toBe("5");
  });

  it("returns all when no filters", () => {
    const rows = filterCases(mockCases, {});
    expect(rows).toHaveLength(5);
  });

  it("handles empty query", () => {
    const rows = filterCases(mockCases, { query: "" });
    expect(rows).toHaveLength(5);
  });
});

describe("paginate", () => {
  it("returns correct slice for page 1 size 2", () => {
    const result = paginate(mockCases, 1, 2);
    expect(result.rows).toHaveLength(2);
    expect(result.rows[0].id).toBe("1");
    expect(result.rows[1].id).toBe("2");
    expect(result.page).toBe(1);
    expect(result.pages).toBe(3);
    expect(result.total).toBe(5);
  });

  it("clamps a page past the end to the last page", () => {
    const result = paginate(mockCases, 99, 10);
    expect(result.page).toBe(1);
    expect(result.rows).toHaveLength(5);
  });

  it("handles page 2 with size 2", () => {
    const result = paginate(mockCases, 2, 2);
    expect(result.rows).toHaveLength(2);
    expect(result.rows[0].id).toBe("3");
    expect(result.page).toBe(2);
  });

  it("handles page 3 with size 2", () => {
    const result = paginate(mockCases, 3, 2);
    expect(result.rows).toHaveLength(1);
    expect(result.rows[0].id).toBe("5");
    expect(result.page).toBe(3);
  });

  it("handles size larger than total", () => {
    const result = paginate(mockCases, 1, 100);
    expect(result.rows).toHaveLength(5);
    expect(result.page).toBe(1);
  });

  it("handles zero size", () => {
    const result = paginate(mockCases, 1, 0);
    expect(result.rows).toHaveLength(5);
    expect(result.page).toBe(1);
  });
});