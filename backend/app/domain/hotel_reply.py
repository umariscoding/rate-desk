"""What the DORM wrote back, as extracted from their reply. Nothing here is computed or verified."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class QuotedRate:
    day: date
    room_type: str
    rooms_offered: int | None
    rate: Decimal | None
    note: str | None


@dataclass(frozen=True)
class StatedTotal:
    """A total the DORM wrote themselves. `scope` is a room type name or 'all'."""

    scope: str
    amount: Decimal
    text: str


@dataclass(frozen=True)
class TermNote:
    item: str
    detail: str
    source: str | None


@dataclass(frozen=True)
class HotelTerms:
    taxes: str | None
    commission: str | None
    option_date: date | None
    attrition: str | None
    cancellation: str | None
    extras: tuple[TermNote, ...]


@dataclass(frozen=True)
class ReplyIssue:
    """The DORM's own text is contradictory or too unclear to rely on."""

    text: str
    blocking: bool


@dataclass(frozen=True)
class HotelReply:
    currency: str
    rates: tuple[QuotedRate, ...]
    stated_totals: tuple[StatedTotal, ...]
    terms: HotelTerms
    issues: tuple[ReplyIssue, ...]
