import type { FeatureRow } from "../types";
import "../styles/report.css";

export function sortContributions<T extends { contribution: number }>(rows: T[]): T[] {
  return [...rows].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
}

export default function FeatureTable({
  rows,
  caption = "Top feature contributions by absolute SHAP value",
}: {
  rows: FeatureRow[];
  caption?: string;
}) {
  const visible = sortContributions(rows)
    .filter((f) => Math.abs(f.contribution) > 1e-6)
    .slice(0, 20);

  if (visible.length === 0) {
    return <p className="muted">No feature contributions above the display threshold.</p>;
  }

  return (
    <table className="list small feature-table">
      <caption>{caption}</caption>
      <thead>
        <tr>
          <th>Feature</th>
          <th>Group</th>
          <th>Value</th>
          <th>Contribution (SHAP)</th>
        </tr>
      </thead>
      <tbody>
        {visible.map((f) => (
          <tr key={f.name}>
            <td>
              <code className="mono">{f.name}</code>
            </td>
            <td className="muted">{f.group}</td>
            <td className="mono">{f.value.toFixed(2)}</td>
            <td className={f.contribution > 0 ? "pos" : "neg"}>
              {f.contribution > 0 ? "+" : ""}
              {f.contribution.toFixed(3)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
