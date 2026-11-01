import type { DormRequestSummary } from "../../api/types";
import { formatDay } from "../../lib/format";

interface Props {
  requests: DormRequestSummary[];
  onOpen: (caseId: string) => void;
}

/** The DORM's inbox: rate requests from the sales desk. */
export function DormInboxPage({ requests, onOpen }: Props) {
  const waiting = requests.filter((request) => request.needs_reply).length;
  return (
    <section className="card">
      <header className="card__header">
        <h2 className="card__title">Inbox</h2>
        <span className="card__meta">{waiting === 0 ? "No replies needed" : `${waiting} waiting for your reply`}</span>
      </header>
      <table className="list">
        <thead>
          <tr>
            <th scope="col">Subject</th>
            <th scope="col">Group</th>
            <th scope="col">Arrival</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((request) => (
            <tr key={request.id} className={request.needs_reply ? "list__row--yours" : undefined}>
              <td>
                <button className="link" onClick={() => onOpen(request.id)}>
                  {request.subject}
                </button>
              </td>
              <td>{request.company ?? ""}</td>
              <td>{request.arrival ? formatDay(request.arrival) : ""}</td>
              <td>
                {request.needs_reply ? <span className="badge badge--info">Reply needed</span> : <span className="badge badge--neutral">Replied</span>}
              </td>
            </tr>
          ))}
          {requests.length === 0 && (
            <tr>
              <td colSpan={4} className="muted">
                Nothing here yet. Rate requests appear when the sales desk sends them.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
