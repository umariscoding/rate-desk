"""Everything the Proposal agent may write, with every number already formatted: the agent copies, never computes."""
import hashlib
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal

from app.domain.group_request import GroupRequest
from app.domain.hotel import Property
from app.domain.hotel_reply import HotelReply
from app.domain.reconciliation import Reconciliation

TO_BE_CONFIRMED = "To be confirmed"


@dataclass(frozen=True)
class ProposalLine:
    date: str
    room_type: str
    rooms: int
    rate: str
    amount: str


@dataclass(frozen=True)
class ProposalPayload:
    proposal_ref: str
    proposal_date: str
    currency: str
    property_name: str
    property_address: str
    salesperson: dict
    client: dict
    event_name: str | None
    arrival_date: str
    departure_date: str
    night_count: int
    lines: tuple[ProposalLine, ...]
    total_room_nights: int
    total_revenue: str
    tax_note: str
    option_date: str
    attrition: str
    cancellation: str
    services: tuple[str, ...]
    internal_do_not_print: dict

    def as_dict(self) -> dict:
        return asdict(self)


def format_day(value: date) -> str:
    return f"{value:%a %d %b %Y}"


def format_money(value: Decimal) -> str:
    return f"{value:,.2f}"


def build_proposal_payload(
    hotel: Property, request: GroupRequest, quote: Reconciliation, reply: HotelReply, today: date
) -> ProposalPayload:
    terms = reply.terms
    return ProposalPayload(
        proposal_ref=_reference(request, today),
        proposal_date=f"{today:%d %B %Y}",
        currency=reply.currency,
        property_name=hotel.name,
        property_address=hotel.address,
        salesperson=asdict(hotel.salesperson),
        client=asdict(request.client),
        event_name=request.event_name,
        arrival_date=format_day(request.arrival),
        departure_date=format_day(request.departure),
        night_count=len(request.nights),
        lines=tuple(
            ProposalLine(format_day(l.day), l.room_type, l.rooms, format_money(l.rate), format_money(l.amount))
            for l in quote.lines
        ),
        total_room_nights=quote.room_nights,
        total_revenue=format_money(quote.revenue),
        tax_note=terms.taxes or TO_BE_CONFIRMED,
        option_date=format_day(terms.option_date) if terms.option_date else TO_BE_CONFIRMED,
        attrition=terms.attrition or TO_BE_CONFIRMED,
        cancellation=terms.cancellation or TO_BE_CONFIRMED,
        services=tuple(f"{note.item}: {note.detail}" for note in terms.extras),
        internal_do_not_print={"commission": terms.commission},
    )


def _reference(request: GroupRequest, today: date) -> str:
    seed = f"{request.client.email}{request.arrival}".encode()
    return f"RD-{today:%Y%m%d}-{hashlib.sha1(seed).hexdigest()[:4].upper()}"
