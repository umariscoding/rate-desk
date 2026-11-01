"""The Case aggregate: one client request travelling from email to finished proposal."""
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from app.domain.errors import InvalidCaseTransition, NothingToSend
from app.domain.group_request import GroupRequest
from app.domain.hotel_reply import HotelReply
from app.domain.rate_rule import RateRule
from app.domain.reconciliation import Reconciliation


CASE_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{8,64}")  # Also keeps ids safe to use as file names.


class CaseStatus(StrEnum):
    RECEIVED = "received"
    NEEDS_CLIENT_INFO = "needs_client_info"
    RATE_REQUEST_DRAFTED = "rate_request_drafted"
    AWAITING_DORM_REPLY = "awaiting_dorm_reply"
    AWAITING_DORM_CORRECTION = "awaiting_dorm_correction"
    RATES_CONFIRMED = "rates_confirmed"
    PROPOSAL_READY = "proposal_ready"


ALLOWED_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.RECEIVED: frozenset({CaseStatus.NEEDS_CLIENT_INFO, CaseStatus.RATE_REQUEST_DRAFTED}),
    CaseStatus.NEEDS_CLIENT_INFO: frozenset(),
    CaseStatus.RATE_REQUEST_DRAFTED: frozenset({CaseStatus.AWAITING_DORM_REPLY}),
    CaseStatus.AWAITING_DORM_REPLY: frozenset({CaseStatus.RATES_CONFIRMED, CaseStatus.AWAITING_DORM_CORRECTION}),
    CaseStatus.AWAITING_DORM_CORRECTION: frozenset({CaseStatus.RATES_CONFIRMED, CaseStatus.AWAITING_DORM_CORRECTION}),
    CaseStatus.RATES_CONFIRMED: frozenset({CaseStatus.PROPOSAL_READY}),
    CaseStatus.PROPOSAL_READY: frozenset({CaseStatus.PROPOSAL_READY}),
}


AWAITING_THE_DORM = frozenset({CaseStatus.AWAITING_DORM_REPLY, CaseStatus.AWAITING_DORM_CORRECTION})


@dataclass(frozen=True)
class OutboundEmail:
    to_name: str
    to_email: str
    subject: str
    body_html: str


@dataclass(frozen=True)
class ProposalDocument:
    file_name: str
    document_id: str
    verification_problems: tuple[str, ...]


@dataclass(frozen=True)
class Handoff:
    """The last step: a cover email the salesperson sends to the client with the proposal."""

    subject: str
    body_html: str


@dataclass
class Case:
    """Mutable on purpose: a case is the unit of consistency and every change goes through a named method."""

    id: str
    created_at: datetime
    source_email: str
    status: CaseStatus = CaseStatus.RECEIVED
    request: GroupRequest | None = None
    pending_email: OutboundEmail | None = None
    sent_to_dorm: list[OutboundEmail] = field(default_factory=list)
    dorm_reply_texts: list[str] = field(default_factory=list)
    hotel_reply: HotelReply | None = None
    reconciliation: Reconciliation | None = None
    rate_rules: tuple[RateRule, ...] | None = None  # None until the hotel's policy has been read for this case.
    proposal: ProposalDocument | None = None
    handoff: Handoff | None = None
    agent_cost: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        if not CASE_ID_PATTERN.fullmatch(self.id):
            raise ValueError(f"Invalid case id: {self.id!r}")

    def record_extraction(self, request: GroupRequest, rate_request: OutboundEmail | None) -> None:
        if request.is_quotable and rate_request is None:
            raise ValueError("A quotable request needs its rate-request email")
        self._move_to(CaseStatus.RATE_REQUEST_DRAFTED if request.is_quotable else CaseStatus.NEEDS_CLIENT_INFO)
        self.request = request
        self.pending_email = rate_request if request.is_quotable else None

    def send_pending_email(self) -> OutboundEmail:
        if self.pending_email is None:
            raise NothingToSend()
        self._move_to(CaseStatus.AWAITING_DORM_REPLY)
        sent, self.pending_email = self.pending_email, None
        self.sent_to_dorm.append(sent)
        return sent

    def begin_hotel_reply(self) -> GroupRequest:
        """Guard: only a case waiting on the DORM may receive a reply. Fails before any agent cost is spent."""
        if self.status not in AWAITING_THE_DORM or self.request is None:
            raise InvalidCaseTransition(self.status, "receive a hotel reply")
        return self.request

    def record_hotel_reply(
        self, reply_text: str, reply: HotelReply, reconciliation: Reconciliation, followup: OutboundEmail | None
    ) -> None:
        if not reconciliation.is_complete and followup is None:
            raise ValueError("An incomplete quote needs its follow-up email")
        self._move_to(CaseStatus.RATES_CONFIRMED if reconciliation.is_complete else CaseStatus.AWAITING_DORM_CORRECTION)
        self.dorm_reply_texts.append(reply_text)
        self.hotel_reply, self.reconciliation = reply, reconciliation
        if followup is not None:
            self.sent_to_dorm.append(followup)  # A correction request goes straight to the DORM: no approval step.

    def record_rate_rules(self, rules: tuple[RateRule, ...]) -> None:
        self.rate_rules = rules

    def begin_proposal(self) -> tuple[GroupRequest, HotelReply, Reconciliation]:
        """Guard: a proposal needs confirmed rates. Returns what the proposal is built from."""
        confirmed = self.status in (CaseStatus.RATES_CONFIRMED, CaseStatus.PROPOSAL_READY)
        if not confirmed or self.request is None or self.hotel_reply is None or self.reconciliation is None:
            raise InvalidCaseTransition(self.status, "build a proposal")
        return self.request, self.hotel_reply, self.reconciliation

    def record_proposal(self, proposal: ProposalDocument) -> None:
        self._move_to(CaseStatus.PROPOSAL_READY)
        self.proposal = proposal
        self.handoff = None  # A rebuilt proposal gets a fresh cover email.

    def record_handoff(self, handoff: Handoff) -> None:
        if self.proposal is None:
            raise InvalidCaseTransition(self.status, "hand off without a proposal")
        self.handoff = handoff

    @property
    def has_reached_dorm(self) -> bool:
        """The DORM only ever sees a request once the salesperson has sent them something."""
        return bool(self.sent_to_dorm)

    def add_cost(self, amount: Decimal) -> None:
        self.agent_cost += amount

    def _move_to(self, target: CaseStatus) -> None:
        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidCaseTransition(self.status, target)
        self.status = target
