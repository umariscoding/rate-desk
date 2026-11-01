"""Business rules that turn the DORM's reply into sellable rate lines, exact totals and open problems.

The agent reads messy text; this module never guesses and never calls a model. Money is computed here.
"""
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

from app.domain.group_request import GroupRequest, RoomNight
from app.domain.hotel_reply import HotelReply, QuotedRate, StatedTotal
from app.domain.rate_rule import RateRule

CENT = Decimal("0.01")
ALL_ROOM_TYPES = "all"


class ProblemKind(StrEnum):
    MISSING_RATE = "missing_rate"
    SHORT_INVENTORY = "short_inventory"
    TOTAL_MISMATCH = "total_mismatch"
    UNCLEAR_IN_REPLY = "unclear_in_reply"
    BELOW_MINIMUM_RATE = "below_minimum_rate"


@dataclass(frozen=True)
class QuoteProblem:
    kind: ProblemKind
    day: date | None = None
    room_type: str | None = None
    rooms_requested: int | None = None
    rooms_offered: int | None = None
    detail: str | None = None
    dorm_total: Decimal | None = None
    computed_total: Decimal | None = None
    rate: Decimal | None = None
    minimum_rate: Decimal | None = None


@dataclass(frozen=True)
class RateLine:
    day: date
    room_type: str
    rooms: int
    rate: Decimal
    amount: Decimal


@dataclass(frozen=True)
class RoomTypeTotal:
    room_type: str
    room_nights: int
    revenue: Decimal


@dataclass(frozen=True)
class Reconciliation:
    lines: tuple[RateLine, ...]
    totals_by_type: tuple[RoomTypeTotal, ...]
    room_nights: int
    revenue: Decimal
    problems: tuple[QuoteProblem, ...]

    @property
    def is_complete(self) -> bool:
        return not self.problems


def money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def reconcile(request: GroupRequest, reply: HotelReply, rules: tuple[RateRule, ...] = ()) -> Reconciliation:
    quotes = {(quote.day, quote.room_type): quote for quote in reply.rates}
    lines: list[RateLine] = []
    problems: list[QuoteProblem] = []
    for need in sorted(request.room_nights, key=lambda item: (item.day, item.room_type)):
        line, found = _price_night(need, quotes.get((need.day, need.room_type)), rules)
        lines.extend([line] if line else [])
        problems.extend(found)
    totals = _totals_by_type(lines)
    problems.extend(_stated_total_mismatches(reply.stated_totals, totals, problems))
    problems.extend(_blocking_reply_issues(reply, problems))
    return Reconciliation(
        lines=tuple(lines),
        totals_by_type=totals,
        room_nights=sum(total.room_nights for total in totals),
        revenue=sum((total.revenue for total in totals), Decimal(0)),
        problems=tuple(problems),
    )


def _price_night(
    need: RoomNight, quote: QuotedRate | None, rules: tuple[RateRule, ...]
) -> tuple[RateLine | None, list[QuoteProblem]]:
    if quote is None or quote.rate is None or quote.rate <= 0:
        return None, [_missing_rate(need, quote)]
    rooms = need.rooms if quote.rooms_offered is None else min(need.rooms, quote.rooms_offered)
    problems = [_short_inventory(need, rooms)] if rooms < need.rooms else []
    if rooms <= 0:
        return None, problems
    rate = money(quote.rate)
    problems += _below_minimum(need, rate, rules)
    return RateLine(need.day, need.room_type, rooms, rate, rate * rooms), problems


def _below_minimum(need: RoomNight, rate: Decimal, rules: tuple[RateRule, ...]) -> list[QuoteProblem]:
    """The strictest rule that applies to this night decides. The rate is still priced: the DORM may confirm it."""
    applicable = [rule for rule in rules if rule.applies_to(need.day, need.room_type)]
    if not applicable:
        return []
    strictest = max(applicable, key=lambda rule: rule.minimum)
    if rate >= strictest.minimum:
        return []
    return [
        QuoteProblem(
            ProblemKind.BELOW_MINIMUM_RATE,
            need.day,
            need.room_type,
            detail=strictest.source,
            rate=rate,
            minimum_rate=money(strictest.minimum),
        )
    ]


def _missing_rate(need: RoomNight, quote: QuotedRate | None) -> QuoteProblem:
    detail = (quote.note if quote else None) or "no usable rate in the reply"
    return QuoteProblem(
        ProblemKind.MISSING_RATE, need.day, need.room_type, rooms_requested=need.rooms, detail=detail
    )


def _short_inventory(need: RoomNight, rooms_offered: int) -> QuoteProblem:
    return QuoteProblem(
        ProblemKind.SHORT_INVENTORY,
        need.day,
        need.room_type,
        rooms_requested=need.rooms,
        rooms_offered=max(rooms_offered, 0),
    )


def _totals_by_type(lines: list[RateLine]) -> tuple[RoomTypeTotal, ...]:
    nights: dict[str, int] = {}
    revenue: dict[str, Decimal] = {}
    for line in lines:
        nights[line.room_type] = nights.get(line.room_type, 0) + line.rooms
        revenue[line.room_type] = revenue.get(line.room_type, Decimal(0)) + line.amount
    return tuple(RoomTypeTotal(kind, nights[kind], revenue[kind]) for kind in nights)


def _stated_total_mismatches(
    stated: tuple[StatedTotal, ...], totals: tuple[RoomTypeTotal, ...], problems: list[QuoteProblem]
) -> list[QuoteProblem]:
    by_type = {total.room_type: total.revenue for total in totals}
    grand = sum(by_type.values(), Decimal(0))
    found = []
    for item in stated:
        computed = grand if item.scope == ALL_ROOM_TYPES else by_type.get(item.scope)
        if computed is None or _scope_has_gaps(item.scope, problems):
            continue  # A total only means something when every requested night in its scope was quoted.
        if abs(computed - money(item.amount)) > CENT:
            found.append(_mismatch(item, computed))
    return found


def _scope_has_gaps(scope: str, problems: list[QuoteProblem]) -> bool:
    return any(scope in (ALL_ROOM_TYPES, problem.room_type) for problem in problems)


def _mismatch(item: StatedTotal, computed: Decimal) -> QuoteProblem:
    return QuoteProblem(
        ProblemKind.TOTAL_MISMATCH,
        room_type=item.scope,
        detail=item.text,
        dorm_total=money(item.amount),
        computed_total=computed,
    )


def _blocking_reply_issues(reply: HotelReply, problems: list[QuoteProblem]) -> list[QuoteProblem]:
    """A model sometimes restates a blank or short cell as 'unclear'. If the issue names a room type we already
    flagged, the follow-up will ask about it anyway, so it is dropped instead of being listed twice."""
    flagged = {p.room_type.lower() for p in problems if p.room_type}
    return [
        QuoteProblem(ProblemKind.UNCLEAR_IN_REPLY, detail=issue.text)
        for issue in reply.issues
        if issue.blocking and not any(room_type in issue.text.lower() for room_type in flagged)
    ]
