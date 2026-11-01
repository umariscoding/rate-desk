import type { CaseDetail } from "../../api/types";
import { FieldGrid } from "../../components/FieldGrid";
import { PathBar } from "../../components/PathBar";
import { StatusBadge } from "../../components/StatusBadge";
import { useGenerateProposal, useSendPendingEmail } from "../../hooks/useCases";
import { formatAgentCost, formatStay, NEXT_STEP } from "../../lib/format";
import { ClientEmailStep } from "./ClientEmailStep";
import { ProposalStep } from "./ProposalStep";
import { RateCheckStep } from "./RateCheckStep";
import { RateRequestStep } from "./RateRequestStep";
import { ReplyStep } from "./ReplyStep";
import { RequestStep } from "./RequestStep";

interface Props {
  detail: CaseDetail;
  onBack: () => void;
}

/** A case record: highlights and status path on top, then one card per stage of the work. */
export function SalesDesk({ detail, onBack }: Props) {
  const send = useSendPendingEmail();
  const build = useGenerateProposal();
  const sendError = send.error?.message ?? null;
  const next = NEXT_STEP[detail.status];

  return (
    <article className="stack">
      <section className="card">
        <div className="card__body">
          <button className="link" onClick={onBack}>
            ← Inbox
          </button>
          <div className="record-title">
            <h2>{detail.client?.company ?? detail.client?.name ?? "New request"}</h2>
            <StatusBadge status={detail.status} />
          </div>
          <FieldGrid
            fields={[
              ["Contact", detail.client?.name],
              ["Event", detail.event_name],
              ["Stay", formatStay(detail.arrival, detail.departure)],
              ["Agent cost", formatAgentCost(detail.agent_cost)],
            ]}
          />
        </div>
        <PathBar status={detail.status} />
        <p className={`next-step ${next.yourMove ? "next-step--yours" : ""}`}>
          {next.yourMove ? "Your next step: " : "Next: "}
          <strong>{next.text}</strong>
        </p>
      </section>
      <ClientEmailStep detail={detail} />
      <RequestStep detail={detail} />
      <RateRequestStep detail={detail} busy={send.isPending} error={sendError} onSend={() => send.mutate(detail.id)} />
      <ReplyStep detail={detail} />
      <RateCheckStep detail={detail} />
      <ProposalStep
        detail={detail}
        busy={build.isPending}
        error={build.error?.message ?? null}
        onBuild={() => build.mutate(detail.id)}
      />
    </article>
  );
}
