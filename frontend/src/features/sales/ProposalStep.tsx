import { downloadFile } from "../../api/http";
import type { CaseDetail, Handoff } from "../../api/types";
import { EmailPreview } from "../../components/EmailPreview";
import { Notice } from "../../components/Notice";
import { Step } from "../../components/Step";

interface Props {
  detail: CaseDetail;
  busy: boolean;
  error: string | null;
  onBuild: () => void;
}

export function ProposalStep({ detail, busy, error, onBuild }: Props) {
  const by = "Desk and cover email agent";
  const { proposal } = detail;
  if (proposal) {
    return (
      <Step title="Proposal" by={by} state="done">
        <p className="lede">{proposal.file_name} is ready for you to send to the client.</p>
        {proposal.verification_problems.length === 0 ? (
          <Notice tone="ok">Checked against the quote: client name, dates and every rate and total are in the document.</Notice>
        ) : (
          <Notice title="Check these before sending">
            <ul className="plain-list">
              {proposal.verification_problems.map((problem, index) => (
                <li key={`${index}-${problem}`}>{problem}</li>
              ))}
            </ul>
          </Notice>
        )}
        <button className="btn btn--primary" onClick={() => void downloadFile(proposal.download_url, proposal.file_name)}>
          Download proposal
        </button>
        <button className="btn btn--quiet" onClick={onBuild} disabled={busy}>
          {busy ? "Building again…" : "Build again"}
        </button>
        {error && <Notice>{error}</Notice>}
        {detail.handoff && <HandoffCard handoff={detail.handoff} />}
      </Step>
    );
  }
  if (detail.status !== "rates_confirmed") {
    return <Step title="Proposal" by={by} state="waiting" hint="Starts once the rates are confirmed." />;
  }
  return (
    <Step title="Proposal" by={by} state="active">
      <p className="lede">
        Rates are confirmed. The desk fills your proposal template and checks the numbers. Then the cover email agent
        writes the email you send to the client.
      </p>
      {error && <Notice>{error}</Notice>}
      <button className="btn btn--primary" onClick={onBuild} disabled={busy}>
        {busy ? "Building the proposal…" : "Build the proposal"}
      </button>
      {busy && <p className="muted">The cover email agent is working. This takes a few seconds.</p>}
    </Step>
  );
}

/** The cover email the agent wrote, for the salesperson to send with the proposal. */
function HandoffCard({ handoff }: { handoff: Handoff }) {
  return (
    <>
      <h4 className="subhead">Cover email for the client</h4>
      <EmailPreview email={handoff} />
    </>
  );
}
