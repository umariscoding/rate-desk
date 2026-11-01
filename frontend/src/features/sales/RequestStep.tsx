import type { CaseDetail } from "../../api/types";
import { FieldGrid } from "../../components/FieldGrid";
import { Notice } from "../../components/Notice";
import { RateBoard } from "../../components/RateBoard";
import { Step } from "../../components/Step";
import { formatDay } from "../../lib/format";

export function RequestStep({ detail }: { detail: CaseDetail }) {
  const { client } = detail;
  return (
    <Step title="Request" by="Intake agent" state="done">
      <FieldGrid
        fields={[
          ["Contact", client?.name],
          ["Company", client?.company],
          ["Email", client?.email],
          ["Phone", client?.phone],
          ["Event", detail.event_name],
          ["Arrival", detail.arrival ? formatDay(detail.arrival) : null],
          ["Departure", detail.departure ? formatDay(detail.departure) : null],
        ]}
      />
      {detail.nights.length > 0 && (
        <>
          <h4 className="subhead">Rooms needed</h4>
          <RateBoard nights={detail.nights} />
        </>
      )}
      {detail.requirements.length > 0 && (
        <>
          <h4 className="subhead">Other requirements</h4>
          <ul className="bullets">
            {detail.requirements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}
      {detail.notes.map((note) => (
        <p className="note" key={note}>
          {note}
        </p>
      ))}
      {detail.missing.length > 0 && (
        <Notice title="Ask the client before requesting rates">
          <ul className="bullets">
            {detail.missing.map((item) => (
              <li key={item.field}>{item.question}</li>
            ))}
          </ul>
        </Notice>
      )}
    </Step>
  );
}
