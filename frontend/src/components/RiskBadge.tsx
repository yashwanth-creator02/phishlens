import type { Band } from "../types";

export default function RiskBadge({ band, score }: { band: Band; score?: number }) {
  return (
    <span className={`badge ${band.toLowerCase()}`}>
      {band}
      {score !== undefined ? ` · ${score}%` : ""}
    </span>
  );
}
