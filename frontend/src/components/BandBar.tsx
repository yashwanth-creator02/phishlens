import type { Band } from "../types";

/** Horizontal Low/Medium/High bar with a marker at the score. Threshold positions are display-only. */
export default function BandBar({ score, band }: { score: number; band: Band }) {
  return (
    <div className="bandbar" role="img" aria-label={`Risk score ${score} percent, ${band}`}>
      <div className="seg low">LOW</div>
      <div className="seg medium">MEDIUM</div>
      <div className="seg high">HIGH</div>
      <div className="marker" style={{ left: `${Math.min(99, Math.max(1, score))}%` }} />
    </div>
  );
}
