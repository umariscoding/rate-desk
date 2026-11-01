import type { ReactNode } from "react";

export type StepState = "done" | "active" | "waiting" | "waiting-for-dorm";

const STATE_TEXT: Record<StepState, string> = {
  done: "Done",
  active: "Action needed",
  waiting: "Waiting",
  "waiting-for-dorm": "Waiting for the DORM",
};

interface Props {
  title: string;
  by: string;
  state: StepState;
  hint?: string;
  children?: ReactNode;
}

/** One section of a case record: a titled card with who produced it and where it stands. */
export function Step({ title, by, state, hint, children }: Props) {
  return (
    <section className={`card card--${state}`} aria-label={title}>
      <header className="card__header">
        <h3 className="card__title">{title}</h3>
        <span className="card__meta">
          {by} · <span className={`card__state card__state--${state}`}>{STATE_TEXT[state]}</span>
        </span>
      </header>
      <div className="card__body">{state === "waiting" ? <p className="muted">{hint}</p> : children}</div>
    </section>
  );
}
