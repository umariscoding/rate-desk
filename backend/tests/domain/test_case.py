from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.domain.case import Case, CaseStatus, OutboundEmail, ProposalDocument
from app.domain.errors import NothingToSend
from app.domain.group_request import ClientContact, GroupRequest, MissingInformation, RoomNight
from app.domain.hotel_reply import HotelReply, HotelTerms, QuotedRate
from app.domain.reconciliation import reconcile

DAY = date(2027, 3, 12)
EMAIL = OutboundEmail("DORM A", "dorm@h.example", "Rate request", "<p>hi</p>")


def make_case() -> Case:
    return Case("case-0001", datetime(2026, 10, 25, tzinfo=UTC), "email text")


def quotable_request() -> GroupRequest:
    return GroupRequest(ClientContact("P", None, None, None), None, DAY, date(2027, 3, 13), (RoomNight(DAY, "Standard King", 2),), (), (), ())


def incomplete_request() -> GroupRequest:
    return GroupRequest(ClientContact("T", None, None, None), None, None, None, (), (), (MissingInformation("stay_dates", "When?"),), ())


def hotel_reply(rate: str | None) -> HotelReply:
    terms = HotelTerms(None, None, None, None, None, ())
    return HotelReply("EUR", (QuotedRate(DAY, "Standard King", 2, None if rate is None else Decimal(rate), None),), (), terms, ())


def test_quotable_request_drafts_a_rate_request():
    case = make_case()
    case.record_extraction(quotable_request(), EMAIL)
    assert case.status is CaseStatus.RATE_REQUEST_DRAFTED
    assert case.pending_email == EMAIL


def test_request_with_missing_information_stops_for_the_salesperson():
    case = make_case()
    case.record_extraction(incomplete_request(), None)
    assert case.status is CaseStatus.NEEDS_CLIENT_INFO
    assert case.pending_email is None


def test_sending_moves_the_draft_to_the_dorm():
    case = make_case()
    case.record_extraction(quotable_request(), EMAIL)
    case.send_pending_email()
    assert case.status is CaseStatus.AWAITING_DORM_REPLY
    assert case.sent_to_dorm == [EMAIL] and case.pending_email is None


def test_nothing_to_send_is_a_typed_error():
    with pytest.raises(NothingToSend):
        make_case().send_pending_email()


def test_complete_quote_confirms_rates_and_allows_a_proposal():
    case = make_case()
    case.record_extraction(quotable_request(), EMAIL)
    case.send_pending_email()
    reply = hotel_reply("189")
    case.record_hotel_reply("reply", reply, reconcile(case.request, reply), None)
    assert case.status is CaseStatus.RATES_CONFIRMED
    case.record_proposal(ProposalDocument("proposal.docx", "doc1", ()))
    assert case.status is CaseStatus.PROPOSAL_READY


def test_incomplete_quote_sends_the_correction_straight_to_the_dorm():
    case = make_case()
    case.record_extraction(quotable_request(), EMAIL)
    case.send_pending_email()
    reply = hotel_reply(None)
    case.record_hotel_reply("reply", reply, reconcile(case.request, reply), EMAIL)
    assert case.status is CaseStatus.AWAITING_DORM_CORRECTION
    assert case.pending_email is None  # No approval step: the DORM already has it.
    assert case.sent_to_dorm == [EMAIL, EMAIL]
