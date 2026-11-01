import { useEffect, useState } from "react";

import { Notice } from "../../components/Notice";
import { useDormRequest, useDormRequestList } from "../../hooks/useDormRequests";
import { useForgetMissingCase } from "../../hooks/useForgetMissingCase";
import { DormInboxPage } from "./DormInboxPage";
import { DormRequestPage } from "./DormRequestPage";

/** Everything the DORM sees: an inbox of rate requests and the conversation for each. */
export function DormApp() {
  const [caseId, setCaseId] = useState<string | null>(() => new URLSearchParams(window.location.search).get("case"));
  const requests = useDormRequestList();
  const detail = useDormRequest(caseId);
  useForgetMissingCase(detail.error, () => setCaseId(null));

  useEffect(() => {
    const params = new URLSearchParams();
    if (caseId) params.set("case", caseId);
    window.history.replaceState(null, "", params.size > 0 ? `?${params}` : window.location.pathname);
  }, [caseId]);

  if (caseId === null) return <DormInboxPage requests={requests.data ?? []} onOpen={setCaseId} />;
  if (detail.isError) return <Notice>{detail.error.message}</Notice>;
  if (!detail.data) return <p className="muted">Loading the request…</p>;
  return <DormRequestPage request={detail.data} onBack={() => setCaseId(null)} />;
}
