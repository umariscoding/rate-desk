import type { Session, User } from "../api/types";

const STORAGE_KEY = "rate-desk-session";
export const SESSION_EXPIRED_EVENT = "rate-desk-session-expired";

export function loadSession(): Session | null {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "null") as Session | null;
  } catch {
    return null;
  }
}

export const saveSession = (session: Session) => window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));

export const clearSession = () => window.localStorage.removeItem(STORAGE_KEY);

export const currentToken = (): string | null => loadSession()?.token ?? null;

export const ROLE_LABEL: Record<User["role"], string> = {
  salesperson: "Salesperson",
  dorm: "DORM (Director of Revenue Management)",
};
