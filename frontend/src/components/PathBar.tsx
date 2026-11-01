import type { CaseStatus } from "../api/types";

const STAGES = ["Request read", "Rate request sent", "Rates confirmed", "Proposal ready"];

/** How many stages are finished, and whether the next one is blocked on a human fix. */
const PROGRESS: Record<CaseStatus, { completed: number; blocked: boolean }> = {
  received: { completed: 0, blocked: false },
  needs_client_info: { completed: 1, blocked: true },
  rate_request_drafted: { completed: 1, blocked: false },
  awaiting_dorm_reply: { completed: 2, blocked: false },
  awaiting_dorm_correction: { completed: 2, blocked: true },
  rates_confirmed: { completed: 3, blocked: false },
  proposal_ready: { completed: 4, blocked: false },
};

export function PathBar({ status }: { status: CaseStatus }) {
  const { completed, blocked } = PROGRESS[status];
  return (
    <ol className="path" aria-label="Case progress">
      {STAGES.map((stage, index) => {
        const state = index < completed ? "done" : index === completed ? (blocked ? "blocked" : "current") : "todo";
        return (
          <li key={stage} className={`path__stage path__stage--${state}`} aria-current={state === "current" ? "step" : undefined}>
            {state === "done" ? `✓ ${stage}` : stage}
          </li>
        );
      })}
    </ol>
  );
}
