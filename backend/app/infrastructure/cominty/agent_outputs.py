"""The JSON each agent must return, validated here so malformed output fails loudly instead of corrupting a case."""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.application.errors import AgentFailure
from app.domain.case import Handoff
from app.domain.group_request import ClientContact, GroupRequest, MissingInformation, RoomNight
from app.domain.hotel_reply import HotelReply, HotelTerms, QuotedRate, ReplyIssue, StatedTotal, TermNote
from app.domain.rate_rule import RateRule

T = TypeVar("T", bound=BaseModel)
ROOM_COUNTS_QUESTION = MissingInformation("room_counts", "How many rooms of each type are needed per night?")


class AgentOutput(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def drop_nulls(cls, data: Any) -> Any:
        """Models often write null for 'nothing'. Dropping it lets each field fall back to its own default."""
        return {key: value for key, value in data.items() if value is not None} if isinstance(data, dict) else data


def validated(model: type[T], payload: dict) -> T:
    try:
        return model.model_validate(payload)
    except ValidationError as error:
        raise AgentFailure(f"The agent's JSON does not match what we asked for: {error.errors()[:3]}") from error


class ClientOutput(AgentOutput):
    name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None


class NightOutput(AgentOutput):
    day: date = Field(alias="date")
    rooms: dict[str, int] = {}


class MissingOutput(AgentOutput):
    field: str
    question: str


class IntakeOutput(AgentOutput):
    client: ClientOutput = ClientOutput()
    event_name: str | None = None
    arrival_date: date | None = None
    departure_date: date | None = None
    nights: list[NightOutput] = []
    requirements: list[str] = []
    missing: list[MissingOutput] = []
    notes: list[str] = []

    def to_domain(self) -> GroupRequest:
        room_nights = tuple(
            RoomNight(night.day, room_type, rooms)
            for night in self.nights
            for room_type, rooms in night.rooms.items()
            if rooms > 0
        )
        missing = tuple(MissingInformation(item.field, item.question) for item in self.missing)
        return GroupRequest(
            client=ClientContact(**self.client.model_dump()),
            event_name=self.event_name,
            arrival=self.arrival_date,
            departure=self.departure_date,
            room_nights=room_nights,
            requirements=tuple(self.requirements),
            missing=missing or (() if room_nights else (ROOM_COUNTS_QUESTION,)),
            notes=tuple(self.notes),
        )





class QuotedRateOutput(AgentOutput):
    day: date = Field(alias="date")
    room_type: str
    rooms: int | None = None
    rate: Decimal | None = None
    note: str | None = None

    @field_validator("rate", mode="before")
    @classmethod
    def words_are_not_rates(cls, value: Any) -> Any:
        """'TBC' or 'n/a' in a rate cell means the DORM gave no rate."""
        try:
            Decimal(str(value))
        except InvalidOperation:
            return None
        return value


class StatedTotalOutput(AgentOutput):
    scope: str
    amount: Decimal
    text: str = ""


class TermNoteOutput(AgentOutput):
    item: str
    detail: str
    source: str | None = None


class TermsOutput(AgentOutput):
    taxes: str | None = None
    commission: str | None = None
    option_date: date | None = None
    attrition: str | None = None
    cancellation: str | None = None
    other: list[TermNoteOutput] = []


class IssueOutput(AgentOutput):
    text: str
    blocking: bool = False


class HotelReplyOutput(AgentOutput):
    currency: str | None = None  # Only present when the DORM names one.
    rates: list[QuotedRateOutput] = []
    dorm_stated_totals: list[StatedTotalOutput] = []
    terms: TermsOutput = TermsOutput()
    issues: list[IssueOutput] = []

    def to_domain(self, default_currency: str) -> HotelReply:
        return HotelReply(
            currency=self.currency or default_currency,
            rates=tuple(QuotedRate(r.day, r.room_type, r.rooms, r.rate, r.note) for r in self.rates),
            stated_totals=tuple(StatedTotal(t.scope, t.amount, t.text) for t in self.dorm_stated_totals),
            terms=self._terms(),
            issues=tuple(ReplyIssue(issue.text, issue.blocking) for issue in self.issues),
        )

    def _terms(self) -> HotelTerms:
        terms = self.terms
        extras = tuple(TermNote(note.item, note.detail, note.source) for note in terms.other)
        return HotelTerms(terms.taxes, terms.commission, terms.option_date, terms.attrition, terms.cancellation, extras)


class HandoffOutput(AgentOutput):
    subject: str
    body_html: str

    def to_domain(self) -> Handoff:
        return Handoff(self.subject, self.body_html)


CITATION_TAG = re.compile(r"<cite\b[^>]*/?>(?:</cite>)?")
WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


class RateRuleOutput(AgentOutput):
    room_type: str | None = None  # None, or "all", means every room type.
    weekdays: list[str]
    minimum_rate: Decimal
    source: str = ""

    @field_validator("source")
    @classmethod
    def without_citation_markup(cls, text: str) -> str:
        """Cominty adds <cite .../> tags when an answer comes from a document. They are not part of the policy's words."""
        return CITATION_TAG.sub("", text).strip()

    @field_validator("weekdays")
    @classmethod
    def known_weekdays(cls, names: list[str]) -> list[str]:
        unknown = [name for name in names if name[:3].lower() not in WEEKDAYS]
        if unknown:
            raise ValueError(f"unknown weekday names: {unknown}")
        return names

    def to_domain(self) -> RateRule:
        room_type = None if (self.room_type or "all").lower() == "all" else self.room_type
        days = tuple(sorted({WEEKDAYS[name[:3].lower()] for name in self.weekdays}))
        return RateRule(room_type, days, self.minimum_rate, self.source)


class RateRulesOutput(AgentOutput):
    found_policy: bool = False
    rules: list[RateRuleOutput] = []

    def to_domain(self) -> tuple[RateRule, ...]:
        return tuple(rule.to_domain() for rule in self.rules) if self.found_policy else ()
