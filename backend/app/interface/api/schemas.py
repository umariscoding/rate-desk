"""The HTTP contract. Money is always a string with two decimals; nothing here leaks a domain type."""
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.domain.case import CASE_ID_PATTERN

MAX_EMAIL_LENGTH = 30_000
CaseId = Annotated[str, StringConstraints(pattern=CASE_ID_PATTERN.pattern)]
EmailText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_EMAIL_LENGTH)]


class SubmitClientEmailBody(BaseModel):
    case_id: CaseId
    email_text: EmailText


class SubmitHotelReplyBody(BaseModel):
    reply_text: EmailText  # The reply as HTML (the grid with rates typed in) or plain text.


class ClientView(BaseModel):
    name: str | None
    company: str | None
    email: str | None
    phone: str | None


class NightView(BaseModel):
    date: date
    weekday: str
    rooms: dict[str, int]


class MissingView(BaseModel):
    field: str
    question: str


class EmailView(BaseModel):
    to_name: str
    to_email: str
    subject: str
    body_html: str


class RateLineView(BaseModel):
    date: date
    room_type: str
    rooms: int
    rate: str
    amount: str


class RoomTypeTotalView(BaseModel):
    room_type: str
    room_nights: int
    revenue: str


class ProblemView(BaseModel):
    kind: str
    date: date | None
    room_type: str | None
    rooms_requested: int | None
    rooms_offered: int | None
    detail: str | None
    dorm_total: str | None
    computed_total: str | None
    rate: str | None
    minimum_rate: str | None


class QuoteView(BaseModel):
    currency: str
    lines: list[RateLineView]
    totals_by_type: list[RoomTypeTotalView]
    room_nights: int
    revenue: str
    problems: list[ProblemView]
    is_complete: bool
    rate_rules_applied: int


class TermsView(BaseModel):
    taxes: str | None
    commission: str | None
    option_date: date | None
    attrition: str | None
    cancellation: str | None
    extras: list[str]


class ProposalView(BaseModel):
    file_name: str
    verification_problems: list[str]
    download_url: str


class HandoffView(BaseModel):
    subject: str
    body_html: str


class CaseView(BaseModel):
    id: str
    status: str
    created_at: datetime
    source_email: str
    agent_cost: str
    client: ClientView | None
    event_name: str | None
    arrival: date | None
    departure: date | None
    nights: list[NightView]
    requirements: list[str]
    missing: list[MissingView]
    notes: list[str]
    pending_email: EmailView | None
    sent_to_dorm: list[EmailView]
    dorm_replies: list[str]
    dorm_replies_are_html: list[bool]
    quote: QuoteView | None
    terms: TermsView | None
    proposal: ProposalView | None
    handoff: HandoffView | None


class CaseSummaryView(BaseModel):
    id: str
    status: str
    created_at: datetime
    client_name: str | None
    company: str | None
    event_name: str | None
    arrival: date | None


class ActivityView(BaseModel):
    source: str
    label: str
    state: str
    key: str
    at: datetime


class LoginBody(BaseModel):
    username: str
    password: str


class UserView(BaseModel):
    username: str
    display_name: str
    role: str


class SessionView(BaseModel):
    token: str
    user: UserView


class DormRequestSummaryView(BaseModel):
    id: str
    subject: str
    company: str | None
    arrival: date | None
    needs_reply: bool
    received_at: datetime


class ThreadMessageView(BaseModel):
    sender: str  # "salesperson" or "dorm"
    sender_name: str
    subject: str | None
    body_html: str | None
    body_text: str | None


class DormRequestView(BaseModel):
    id: str
    company: str | None
    arrival: date | None
    departure: date | None
    can_reply: bool
    thread: list[ThreadMessageView]
