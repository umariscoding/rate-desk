/** Mirrors backend/app/interface/api/schemas.py. Money is always a string with two decimals. */

export type CaseStatus =
  | "received"
  | "needs_client_info"
  | "rate_request_drafted"
  | "awaiting_dorm_reply"
  | "awaiting_dorm_correction"
  | "rates_confirmed"
  | "proposal_ready";

export interface Client {
  name: string | null;
  company: string | null;
  email: string | null;
  phone: string | null;
}

export interface Night {
  date: string;
  weekday: string;
  rooms: Record<string, number>;
}

export interface Missing {
  field: string;
  question: string;
}

export interface Email {
  to_name: string;
  to_email: string;
  subject: string;
  body_html: string;
}

export interface RateLine {
  date: string;
  room_type: string;
  rooms: number;
  rate: string;
  amount: string;
}

export interface RoomTypeTotal {
  room_type: string;
  room_nights: number;
  revenue: string;
}

export type ProblemKind = "missing_rate" | "short_inventory" | "total_mismatch" | "unclear_in_reply" | "below_minimum_rate";

export interface Problem {
  kind: ProblemKind;
  date: string | null;
  room_type: string | null;
  rooms_requested: number | null;
  rooms_offered: number | null;
  detail: string | null;
  dorm_total: string | null;
  computed_total: string | null;
  rate: string | null;
  minimum_rate: string | null;
}

export interface Quote {
  currency: string;
  lines: RateLine[];
  totals_by_type: RoomTypeTotal[];
  room_nights: number;
  revenue: string;
  problems: Problem[];
  is_complete: boolean;
  rate_rules_applied: number;
}

export interface Terms {
  taxes: string | null;
  commission: string | null;
  option_date: string | null;
  attrition: string | null;
  cancellation: string | null;
  extras: string[];
}

export interface Proposal {
  file_name: string;
  verification_problems: string[];
  download_url: string;
}

export interface Handoff {
  subject: string;
  body_html: string;
}

export interface CaseDetail {
  id: string;
  status: CaseStatus;
  created_at: string;
  source_email: string;
  agent_cost: string;
  client: Client | null;
  event_name: string | null;
  arrival: string | null;
  departure: string | null;
  nights: Night[];
  requirements: string[];
  missing: Missing[];
  notes: string[];
  pending_email: Email | null;
  sent_to_dorm: Email[];
  dorm_replies: string[];
  dorm_replies_are_html: boolean[];
  quote: Quote | null;
  terms: Terms | null;
  proposal: Proposal | null;
  handoff: Handoff | null;
}

export interface CaseSummary {
  id: string;
  status: CaseStatus;
  created_at: string;
  client_name: string | null;
  company: string | null;
  event_name: string | null;
  arrival: string | null;
}

export type ActivityState = "running" | "done" | "failed";
export type ActivitySource = "system" | "intake" | "rate_reply" | "rate_guard" | "handoff";

export interface ActivityEvent {
  source: ActivitySource;
  label: string;
  state: ActivityState;
  key: string;
  at: string;
}

export type Role = "salesperson" | "dorm";

export interface User {
  username: string;
  display_name: string;
  role: Role;
}

export interface Session {
  token: string;
  user: User;
}

export interface DormRequestSummary {
  id: string;
  subject: string;
  company: string | null;
  arrival: string | null;
  needs_reply: boolean;
  received_at: string;
}

export interface ThreadMessage {
  sender: "salesperson" | "dorm";
  sender_name: string;
  subject: string | null;
  body_html: string | null;
  body_text: string | null;
}

export interface DormRequest {
  id: string;
  company: string | null;
  arrival: string | null;
  departure: string | null;
  can_reply: boolean;
  thread: ThreadMessage[];
}
