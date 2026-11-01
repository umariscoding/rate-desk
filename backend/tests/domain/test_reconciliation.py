from datetime import date
from decimal import Decimal

from app.domain.group_request import ClientContact, GroupRequest, RoomNight
from app.domain.hotel_reply import HotelReply, HotelTerms, QuotedRate, ReplyIssue, StatedTotal
from app.domain.reconciliation import ProblemKind, reconcile

FRIDAY, SATURDAY, SUNDAY = date(2027, 3, 12), date(2027, 3, 13), date(2027, 3, 14)
NO_TERMS = HotelTerms(None, None, None, None, None, ())


def make_request(*needs: RoomNight) -> GroupRequest:
    return GroupRequest(ClientContact("Client A", "Company A", "p@n.example", None), None, FRIDAY, date(2027, 3, 15), needs, (), (), ())


def make_reply(rates, stated=(), issues=()) -> HotelReply:
    return HotelReply("EUR", tuple(rates), tuple(stated), NO_TERMS, tuple(issues))


def quote(day, room_type, rooms, rate, note=None) -> QuotedRate:
    return QuotedRate(day, room_type, rooms, None if rate is None else Decimal(rate), note)


def test_prices_every_night_with_exact_money():
    request = make_request(*(RoomNight(day, "Standard King", 40) for day in (FRIDAY, SATURDAY, SUNDAY)))
    reply = make_reply(quote(day, "Standard King", 40, rate) for day, rate in zip((FRIDAY, SATURDAY, SUNDAY), ("189", "209", "179")))

    result = reconcile(request, reply)

    assert result.is_complete
    assert result.room_nights == 120
    assert result.revenue == Decimal("23080.00")  # 40 x (189 + 209 + 179), the sum a model got wrong


def test_blank_zero_and_tbc_rates_are_missing():
    request = make_request(RoomNight(FRIDAY, "Deluxe King", 10), RoomNight(SATURDAY, "Junior Suite", 3))
    reply = make_reply([quote(FRIDAY, "Deluxe King", 10, "0"), quote(SATURDAY, "Junior Suite", 3, None, "TBC")])

    result = reconcile(request, reply)

    assert [problem.kind for problem in result.problems] == [ProblemKind.MISSING_RATE] * 2
    assert result.lines == ()


def test_fewer_rooms_than_requested_is_priced_for_what_is_offered_and_flagged():
    request = make_request(RoomNight(SUNDAY, "Deluxe King", 10))

    result = reconcile(request, make_reply([quote(SUNDAY, "Deluxe King", 6, "219")]))

    assert result.lines[0].rooms == 6
    assert result.lines[0].amount == Decimal("1314.00")
    assert result.problems[0].kind is ProblemKind.SHORT_INVENTORY
    assert (result.problems[0].rooms_requested, result.problems[0].rooms_offered) == (10, 6)


def test_a_wrong_total_written_by_the_dorm_is_flagged():
    request = make_request(*(RoomNight(day, "Standard King", 40) for day in (FRIDAY, SATURDAY, SUNDAY)))
    rates = [quote(day, "Standard King", 40, rate) for day, rate in zip((FRIDAY, SATURDAY, SUNDAY), ("189", "209", "179"))]
    stated = [StatedTotal("Standard King", Decimal("23000"), "Total SK revenue 3 nights: EUR 23,000")]

    result = reconcile(request, make_reply(rates, stated))

    mismatch = result.problems[0]
    assert mismatch.kind is ProblemKind.TOTAL_MISMATCH
    assert (mismatch.dorm_total, mismatch.computed_total) == (Decimal("23000.00"), Decimal("23080.00"))


def test_a_total_is_ignored_when_its_scope_has_unquoted_nights():
    request = make_request(RoomNight(FRIDAY, "Standard King", 40), RoomNight(SATURDAY, "Standard King", 40))
    rates = [quote(FRIDAY, "Standard King", 40, "189"), quote(SATURDAY, "Standard King", 40, None)]
    stated = [StatedTotal("Standard King", Decimal("1"), "total")]

    kinds = [problem.kind for problem in reconcile(request, make_reply(rates, stated)).problems]

    assert kinds == [ProblemKind.MISSING_RATE]


def test_only_blocking_reply_issues_become_problems():
    request = make_request(RoomNight(FRIDAY, "Standard King", 1))
    issues = [ReplyIssue("attrition wording contradicts itself", False), ReplyIssue("rate basis unclear", True)]

    result = reconcile(request, make_reply([quote(FRIDAY, "Standard King", 1, "100")], issues=issues))

    assert [problem.kind for problem in result.problems] == [ProblemKind.UNCLEAR_IN_REPLY]
    assert result.problems[0].detail == "rate basis unclear"
