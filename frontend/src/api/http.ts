import { clearSession, currentToken, SESSION_EXPIRED_EVENT } from "../lib/session";

const API_ROOT = "/api/v1";
const UNAUTHENTICATED = 401;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

/** The backend answers errors as {detail: string} or, for malformed input, {detail: [{msg}]}. */
function describeError(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item?.msg ?? "invalid input").join("; ");
  return `The request failed (${status})`;
}

function authHeaders(): Record<string, string> {
  const token = currentToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** A rejected session means the token expired or was cleared: send the user back to the sign-in page. */
function handleRejectedSession(status: number, path: string) {
  if (status === UNAUTHENTICATED && !path.startsWith("/auth/login")) {
    clearSession();
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    handleRejectedSession(response.status, path);
    throw new ApiError(response.status, describeError(body, response.status));
  }
  return body as T;
}

/** The token travels in the URL only here: browsers cannot set headers on an EventSource. */
export const activityUrl = (caseId: string) => `${API_ROOT}/cases/${caseId}/activity?token=${encodeURIComponent(currentToken() ?? "")}`;

/** Download through fetch so the token stays in a header, then hand the bytes to the browser as a file. */
export async function downloadFile(url: string, fileName: string): Promise<void> {
  const response = await fetch(url, { headers: authHeaders() });
  if (!response.ok) throw new ApiError(response.status, `The download failed (${response.status})`);
  const link = document.createElement("a");
  link.href = URL.createObjectURL(await response.blob());
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(link.href);
}
