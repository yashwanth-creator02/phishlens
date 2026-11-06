import type { Band } from "../types";

export default function BandBar({ score, band }: { score: number; band: Band }) {
  return (
    <div className="bandbar" role="img" aria-label={`Risk score ${score} percent, band ${band}`}>
      <div className="seg low">LOW</div>
      <div className="seg medium">MEDIUM</div>
      <div className="seg high">HIGH</div>
      <div className="marker" style={{ left: `${Math.min(99, Math.max(1, score))}%` }} />
    </div>
  );
}
