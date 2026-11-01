import { request } from "./http";
import type { DormRequest, DormRequestSummary } from "./types";

export const listDormRequests = () => request<DormRequestSummary[]>("/dorm/requests");

export const getDormRequest = (caseId: string) => request<DormRequest>(`/dorm/requests/${caseId}`);

export const replyToRequest = (caseId: string, replyText: string) =>
  request<DormRequest>(`/dorm/requests/${caseId}/reply`, { method: "POST", body: JSON.stringify({ reply_text: replyText }) });
