import { request } from "./http";
import type { CaseDetail, CaseSummary } from "./types";

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const listCases = () => request<CaseSummary[]>("/cases");

export const getCase = (caseId: string) => request<CaseDetail>(`/cases/${caseId}`);

export const submitClientEmail = (caseId: string, emailText: string) =>
  post<CaseDetail>("/cases", { case_id: caseId, email_text: emailText });

export const sendPendingEmail = (caseId: string) => post<CaseDetail>(`/cases/${caseId}/emails/send`);

export const generateProposal = (caseId: string) => post<CaseDetail>(`/cases/${caseId}/proposal`);
