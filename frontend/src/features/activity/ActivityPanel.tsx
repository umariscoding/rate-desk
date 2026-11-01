import type { ActivityEvent, ActivitySource } from "../../api/types";
import { formatAgentCost } from "../../lib/format";

const SOURCE_NAME: Record<ActivitySource, string> = {
  system: "Desk",
  intake: "Intake agent",
  rate_reply: "Rate reading agent",
  rate_guard: "Rate guard agent",
  handoff: "Cover email agent",
};
const NOISE = new Set(["Thinking", "Preparing the agent's workspace"]);

interface Props {
  events: ActivityEvent[];
  agentCost: string | null;
  caseSelected: boolean;
}

export function ActivityPanel({ events, agentCost, caseSelected }: Props) {
  const visible = events.filter((event) => !NOISE.has(event.label));
  const working = currentlyWorking(events);

  return (
    <aside className="card activity" aria-label="Agent activity">
      <header className="card__header card__header--bar">
        <h2 className="card__title">Agent activity</h2>
        {agentCost && <span className="activity__cost" title="What the agents have cost so far on this case">{formatAgentCost(agentCost)}</span>}
      </header>
      <ol className="card__body activity__list" aria-live="polite">
        {visible.length === 0 && <li className="activity__empty">
            {caseSelected
              ? "No agent activity recorded for this case since the server started."
              : "Nothing yet. The agents start when you paste a client email."}
          </li>}
        {visible.map((event) => (
          <li key={event.key} className={`activity__item activity__item--${event.state}`}>
            <span className="activity__icon" aria-hidden="true" />
            <div>
              <span className="activity__label">{event.label}</span>
              <span className="activity__source">{SOURCE_NAME[event.source]}</span>
            </div>
          </li>
        ))}
      </ol>
      {working && <p className="card__body activity__working">{SOURCE_NAME[working.source]} is working…</p>}
    </aside>
  );
}

/** The desk's own step events always close, so they decide whether work is under way; agent events say who. */
function currentlyWorking(events: ActivityEvent[]): ActivityEvent | undefined {
  const lastDeskEvent = events.filter((event) => event.source === "system").at(-1);
  if (lastDeskEvent?.state !== "running") return undefined;
  return events.filter((event) => event.state === "running").at(-1) ?? lastDeskEvent;
}
