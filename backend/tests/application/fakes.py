"""In-memory stand-ins for every port, so use cases are tested without Cominty, files or HTTP."""
from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal

from app.application.activity import ActivityEvent
from app.application.ports import ComposedProposal, Costed
from app.domain.case import Case, Handoff, OutboundEmail
from app.domain.errors import CaseNotFound
from app.domain.group_request import ClientContact, GroupRequest, MissingInformation, RoomNight
from app.domain.hotel_reply import HotelReply, HotelTerms, QuotedRate

DAY = date(2027, 3, 12)
COST = Decimal("0.001")
EMAIL = OutboundEmail("DORM A", "dorm@h.example", "Rate request", "<p>grid</p>")
NO_TERMS = HotelTerms(None, None, None, None, None, ())


def quotable_request() -> GroupRequest:
    return GroupRequest(ClientContact("Client A", "Company A", "p@n.example", None), None, DAY, date(2027, 3, 13), (RoomNight(DAY, "Standard King", 2),), (), (), ())


def request_missing_dates() -> GroupRequest:
    return GroupRequest(ClientContact("Tom", None, None, None), None, None, None, (), (), (MissingInformation("stay_dates", "When?"),), ())


def hotel_reply(rate: str | None) -> HotelReply:
    return HotelReply("EUR", (QuotedRate(DAY, "Standard King", 2, None if rate is None else Decimal(rate), None),), (), NO_TERMS, ())


class InMemoryCases:
    def __init__(self) -> None:
        self.items: dict[str, Case] = {}

    def exists(self, case_id: str) -> bool:
        return case_id in self.items

    def get(self, case_id: str) -> Case:
        if case_id not in self.items:
            raise CaseNotFound(case_id)
        return self.items[case_id]

    def save(self, case: Case) -> None:
        self.items[case.id] = case

    def list_recent(self) -> list[Case]:
        return list(self.items.values())


class RecordingFeed:
    def __init__(self) -> None:
        self.events: list[tuple[str, ActivityEvent]] = []

    async def publish(self, case_id: str, event: ActivityEvent) -> None:
        self.events.append((case_id, event))

    async def subscribe(self, case_id: str) -> AsyncIterator[ActivityEvent]:
        for owner, event in self.events:
            if owner == case_id:
                yield event


class MemoryDocuments:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, case_id: str, file_name: str, content: bytes) -> str:
        document_id = f"{case_id}/{file_name}"
        self.files[document_id] = content
        return document_id

    def load(self, document_id: str) -> bytes:
        return self.files[document_id]


class ScriptedExtractor:
    def __init__(self, request: GroupRequest) -> None:
        self._request = request

    async def extract(self, email_text, on_activity) -> Costed[GroupRequest]:
        return Costed(self._request, COST)


class ScriptedRateRequestWriter:
    def __init__(self) -> None:
        self.calls = 0

    async def write(self, request, on_activity) -> Costed[OutboundEmail]:
        self.calls += 1
        return Costed(EMAIL, COST)


class ScriptedReader:
    def __init__(self, reply: HotelReply) -> None:
        self._reply = reply
        self.replies: list[str] = []

    async def read(self, request, reply, on_activity) -> Costed[HotelReply]:
        self.replies.append(reply)
        return Costed(self._reply, COST)


class ScriptedFollowupWriter:
    async def write(self, request, quote, on_activity) -> Costed[OutboundEmail]:
        return Costed(OutboundEmail("DORM A", "dorm@h.example", "Follow-up", f"{len(quote.problems)} problems"), COST)


class ScriptedRateRules:
    def __init__(self, rules=()) -> None:
        self._rules = tuple(rules)

    async def read(self, request, on_activity) -> Costed:
        return Costed(self._rules, COST)


class ScriptedHandoff:
    async def hand_off(self, request, quote, reply, on_activity) -> Costed[Handoff]:
        return Costed(Handoff("Your proposal", "<p>Dear Client A</p>"), COST)


class ScriptedComposer:
    def __init__(self, problems: tuple[str, ...] = ()) -> None:
        self._problems = problems

    async def compose(self, request, quote, reply, on_activity) -> Costed[ComposedProposal]:
        return Costed(ComposedProposal("proposal.docx", b"docx-bytes", self._problems), COST)
