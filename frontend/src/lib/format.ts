import type { CaseStatus } from "../api/types";

export const DORM_LABEL = "the DORM";
const ROOM_ORDER = ["Standard King", "Standard Double", "Deluxe King", "Junior Suite"];

export function formatMoney(amount: string, currency = "EUR"): string {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(Number(amount));
}

export function formatAgentCost(amount: string): string {
  return `€${amount}`;
}

const parseDay = (iso: string) => new Date(`${iso}T12:00:00`);

export function formatDay(iso: string): string {
  return parseDay(iso).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

export function formatStay(arrival: string | null, departure: string | null): string {
  if (!arrival || !departure) return "Dates to be confirmed";
  const short = (iso: string) => parseDay(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  const year = parseDay(departure).getFullYear();
  return `${short(arrival)} to ${short(departure)} ${year}`;
}

export function sortRoomTypes(types: Iterable<string>): string[] {
  const rank = (type: string) => (ROOM_ORDER.includes(type) ? ROOM_ORDER.indexOf(type) : ROOM_ORDER.length);
  return [...new Set(types)].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
}

export type Tone = "neutral" | "info" | "warn" | "ok";

/** What happens next on a case, in the salesperson's words, and whether the move is theirs. */
export const NEXT_STEP: Record<CaseStatus, { text: string; yourMove: boolean }> = {
  received: { text: "The agents are reading the email", yourMove: false },
  needs_client_info: { text: "Ask the client for the missing details", yourMove: true },
  rate_request_drafted: { text: `Review the rate request and send it to ${DORM_LABEL}`, yourMove: true },
  awaiting_dorm_reply: { text: `Waiting for ${DORM_LABEL} to reply`, yourMove: false },
  awaiting_dorm_correction: { text: `Waiting for ${DORM_LABEL} to send what was missing`, yourMove: false },
  rates_confirmed: { text: "Build the proposal", yourMove: true },
  proposal_ready: { text: "Download the proposal and send it to the client", yourMove: true },
};

export const STATUS_LABEL: Record<CaseStatus, { text: string; tone: Tone }> = {
  received: { text: "Reading email", tone: "info" },
  needs_client_info: { text: "Needs client info", tone: "warn" },
  rate_request_drafted: { text: "Approve rate request", tone: "info" },
  awaiting_dorm_reply: { text: `Waiting for ${DORM_LABEL}`, tone: "neutral" },
  awaiting_dorm_correction: { text: "Missing details requested", tone: "warn" },
  rates_confirmed: { text: "Rates confirmed", tone: "ok" },
  proposal_ready: { text: "Proposal ready", tone: "ok" },
};
