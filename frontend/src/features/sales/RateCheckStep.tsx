import type { CaseDetail } from "../../api/types";
import { EmailPreview } from "../../components/EmailPreview";
import { Notice } from "../../components/Notice";
import { RateBoard } from "../../components/RateBoard";
import { Step } from "../../components/Step";
import { formatDay, formatMoney } from "../../lib/format";
import { describeProblem } from "./describeProblem";

export function RateCheckStep({ detail }: { detail: CaseDetail }) {
  const { quote } = detail;
  const by = "Rate reading agent";
  if (!quote) {
    return <Step title="Rate check" by={by} state="waiting" hint="Runs as soon as the reply arrives." />;
  }
  const waitingForCorrection = detail.status === "awaiting_dorm_correction";
  return (
    <Step title="Rate check" by={by} state={quote.is_complete ? "done" : "waiting-for-dorm"}>
      <RateBoard nights={detail.nights} quote={quote} />
      <p className="summary">
        <strong>{quote.room_nights}</strong> room nights quoted · <strong>{formatMoney(quote.revenue, quote.currency)}</strong>{" "}
        room revenue
        {quote.rate_rules_applied > 0 && (
          <>
            {" "}
            · checked against <strong>{quote.rate_rules_applied}</strong> hotel rate rules
          </>
        )}
      </p>
      {quote.problems.length > 0 && (
        <Notice title={`${quote.problems.length} to fix before this can become a proposal`}>
          <ul className="bullets">
            {quote.problems.map((problem, index) => (
              <li key={index}>{describeProblem(problem, quote.currency)}</li>
            ))}
          </ul>
        </Notice>
      )}
      {waitingForCorrection && <CorrectionSent detail={detail} />}
      {quote.is_complete && <Terms detail={detail} />}
    </Step>
  );
}

/** The correction request goes to the DORM on its own. Here is what they were sent. */
function CorrectionSent({ detail }: { detail: CaseDetail }) {
  const sent = detail.sent_to_dorm.at(-1);
  return (
    <>
      <Notice tone="info">
        The DORM was sent one email with everything that is missing and their rates pre-filled. Nothing for you to do until they reply.
      </Notice>
      {sent && (
        <details className="original">
          <summary>Show what was sent: {sent.subject}</summary>
          <EmailPreview email={sent} />
        </details>
      )}
    </>
  );
}

function Terms({ detail }: { detail: CaseDetail }) {
  const terms = detail.terms;
  if (!terms) return null;
  const rows: [string, string | null][] = [
    ["Taxes", terms.taxes],
    ["Option until", terms.option_date ? formatDay(terms.option_date) : null],
    ["Attrition", terms.attrition],
    ["Cancellation", terms.cancellation],
    ...terms.extras.map((extra): [string, string] => ["Also quoted", extra]),
  ];
  return (
    <dl className="terms">
      {rows.map(([label, value], index) => (
        <div key={index}>
          <dt>{label}</dt>
          <dd className={value ? undefined : "muted"}>{value ?? "Not stated"}</dd>
        </div>
      ))}
    </dl>
  );
}
