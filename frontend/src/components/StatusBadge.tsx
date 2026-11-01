import type { CaseStatus } from "../api/types";
import { STATUS_LABEL } from "../lib/format";

export function StatusBadge({ status }: { status: CaseStatus }) {
  const { text, tone } = STATUS_LABEL[status];
  return <span className={`badge badge--${tone}`}>{text}</span>;
}
