import { useEffect, useState } from "react";

import { Notice } from "../../components/Notice";
import { useActivity } from "../../hooks/useActivity";
import { useCase, useCaseList, useSubmitClientEmail } from "../../hooks/useCases";
import { useForgetMissingCase } from "../../hooks/useForgetMissingCase";
import { ActivityPanel } from "../activity/ActivityPanel";
import { CasesListView } from "../cases/CasesListView";
import { NewCase } from "../cases/NewCase";
import { SalesDesk } from "./SalesDesk";

export type SalesView = "inbox" | "new";

interface Props {
  view: SalesView;
  onViewChange: (view: SalesView) => void;
}

const readCaseFromAddress = () => new URLSearchParams(window.location.search).get("case");

/** Everything the salesperson sees: the inbox of requests, a new-request form, and each case record. */
export function SalespersonApp({ view, onViewChange }: Props) {
  const [caseId, setCaseId] = useState<string | null>(readCaseFromAddress);
  // The browser picks the case id, so it can listen to the agents before the first request finishes.
  const [startingId, setStartingId] = useState<string | null>(null);

  const cases = useCaseList();
  const detail = useCase(caseId);
  const submit = useSubmitClientEmail();
  const events = useActivity(startingId ?? caseId);
  useForgetMissingCase(detail.error, () => setCaseId(null));

  useEffect(() => {
    const params = new URLSearchParams();
    if (caseId) params.set("case", caseId);
    window.history.replaceState(null, "", params.size > 0 ? `?${params}` : window.location.pathname);
  }, [caseId]);

  const startCase = (emailText: string) => {
    const newId = crypto.randomUUID();
    setStartingId(newId);
    submit.mutate(
      { caseId: newId, emailText },
      {
        onSuccess: () => {
          setCaseId(newId);
          onViewChange("inbox");
        },
        onSettled: () => setStartingId(null),
      },
    );
  };

  const withActivity = (content: JSX.Element) => (
    <div className="record">
      <div>{content}</div>
      <ActivityPanel events={events} agentCost={detail.data?.agent_cost ?? null} caseSelected={caseId !== null} />
    </div>
  );

  if (startingId) {
    return withActivity(
      <section className="card">
        <header className="card__header">
          <h2 className="card__title">Reading the client's email</h2>
        </header>
        <div className="card__body muted">The agents are extracting the request and drafting the rate request.</div>
      </section>,
    );
  }
  if (view === "new") {
    return <NewCase busy={submit.isPending} error={submit.error?.message ?? null} onSubmit={startCase} onCancel={() => onViewChange("inbox")} />;
  }
  if (caseId === null) {
    return <CasesListView cases={cases.data ?? []} onOpen={setCaseId} onNew={() => onViewChange("new")} />;
  }
  if (detail.isError) return <Notice>{detail.error.message}</Notice>;
  if (!detail.data) return <p className="muted">Loading the case…</p>;
  return withActivity(<SalesDesk detail={detail.data} onBack={() => setCaseId(null)} />);
}
