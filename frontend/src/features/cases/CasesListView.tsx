import type { CaseSummary } from "../../api/types";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDay, NEXT_STEP } from "../../lib/format";

interface Props {
  cases: CaseSummary[];
  onOpen: (caseId: string) => void;
  onNew: () => void;
}

/** The salesperson's inbox: one row per request, with what to do next in plain words. */
export function CasesListView({ cases, onOpen, onNew }: Props) {
  const toDo = cases.filter((item) => NEXT_STEP[item.status].yourMove).length;
  return (
    <section className="card">
      <header className="card__header card__header--bar">
        <div>
          <h2 className="card__title">Inbox</h2>
          <span className="card__meta">{toDo === 0 ? "Nothing needs you right now" : `${toDo} need your action`}</span>
        </div>
        <button className="btn btn--primary" onClick={onNew}>
          New request
        </button>
      </header>
      <table className="list">
        <thead>
          <tr>
            <th scope="col">Company</th>
            <th scope="col">Contact</th>
            <th scope="col">Event</th>
            <th scope="col">Arrival</th>
            <th scope="col">Status</th>
            <th scope="col">Next step</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => {
            const next = NEXT_STEP[item.status];
            return (
              <tr key={item.id} className={next.yourMove ? "list__row--yours" : undefined}>
                <td>
                  <button className="link" onClick={() => onOpen(item.id)}>
                    {item.company ?? item.client_name ?? "Unread request"}
                  </button>
                </td>
                <td>{item.client_name ?? ""}</td>
                <td>{item.event_name ?? ""}</td>
                <td>{item.arrival ? formatDay(item.arrival) : ""}</td>
                <td>
                  <StatusBadge status={item.status} />
                </td>
                <td>{next.yourMove ? <strong>{next.text}</strong> : <span className="muted">{next.text}</span>}</td>
              </tr>
            );
          })}
          {cases.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No requests yet. Choose New request and paste a client's email.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
