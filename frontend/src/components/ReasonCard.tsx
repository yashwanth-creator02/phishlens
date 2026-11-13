import type { Reason } from "../types";
import "../styles/report.css";

const GROUP_LABEL: Record<string, string> = {
  header: "Sender / headers",
  url: "Links",
  text: "Wording",
  action: "Requested action",
  attachment: "Attachments",
  behaviour: "Sender history",
  model: "Overall pattern",
};

export function groupLabel(group: string) {
  return GROUP_LABEL[group] ?? group;
}

export default function ReasonCard({
  reason,
  index,
}: {
  reason: Reason;
  index: number;
}) {
  const rank = reason.rank ?? index + 1;
  return (
    <article className="card reason-card" aria-label={`Verified reason ${rank}`}>
      <div className="reason-row">
        <span className="reason-rank" aria-hidden="true">
          {rank}.
        </span>
        <span className="tag">{groupLabel(reason.group)}</span>
        <span className="reason-verified-chip">Verified</span>
        <span className="reason-sentence">{reason.sentence}</span>
      </div>
      <div className="reason-meta">
        Evidence rule {reason.rule_key} checked against the parsed email
        {reason.contribution !== 0
          ? ` · contribution ${reason.contribution >= 0 ? "+" : ""}${reason.contribution.toFixed(3)}`
          : ""}
      </div>
    </article>
  );
}
