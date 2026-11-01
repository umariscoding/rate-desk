import type { CaseDetail } from "../../api/types";
import { EmailPreview } from "../../components/EmailPreview";
import { Notice } from "../../components/Notice";
import { Step } from "../../components/Step";
import { DORM_LABEL } from "../../lib/format";

interface Props {
  detail: CaseDetail;
  busy: boolean;
  error: string | null;
  onSend: () => void;
}

export function RateRequestStep({ detail, busy, error, onSend }: Props) {
  const by = "Desk";
  const title = `Rate request to ${DORM_LABEL}`;
  if (detail.status === "needs_client_info") {
    return <Step title={title} by={by} state="waiting" hint="Needs the stay dates and room counts first." />;
  }
  if (detail.status === "rate_request_drafted" && detail.pending_email) {
    return (
      <Step title={title} by={by} state="active">
        <EmailPreview email={detail.pending_email} />
        {error && <Notice>{error}</Notice>}
        <button className="btn btn--primary" onClick={onSend} disabled={busy}>
          Approve and send to {DORM_LABEL}
        </button>
      </Step>
    );
  }
  const sent = detail.sent_to_dorm[0];
  return (
    <Step title={title} by={by} state="done">
      {sent && (
        <details className="original">
          <summary>Sent: {sent.subject}</summary>
          <EmailPreview email={sent} />
        </details>
      )}
    </Step>
  );
}
