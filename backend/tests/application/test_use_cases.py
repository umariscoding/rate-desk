from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.application.activity import ActivityState
from app.application.use_cases.generate_proposal import GenerateProposal
from app.application.use_cases.send_pending_email import SendPendingEmail
from app.application.use_cases.submit_client_email import SubmitClientEmail
from app.application.use_cases.submit_hotel_reply import SubmitHotelReply
from app.domain.case import CaseStatus
from app.domain.errors import CaseAlreadyExists, CaseNotFound, InvalidCaseTransition
from tests.application import fakes

NOW = datetime(2026, 10, 25, tzinfo=UTC)


@pytest.fixture
def cases() -> fakes.InMemoryCases:
    return fakes.InMemoryCases()


@pytest.fixture
def feed() -> fakes.RecordingFeed:
    return fakes.RecordingFeed()


def submit_email(cases, feed, request, writer=None) -> SubmitClientEmail:
    return SubmitClientEmail(fakes.ScriptedExtractor(request), writer or fakes.ScriptedRateRequestWriter(), cases, feed, lambda: NOW)


async def case_awaiting_dorm(cases, feed) -> str:
    await submit_email(cases, feed, fakes.quotable_request()).execute("case-0001", "email")
    await SendPendingEmail(cases, feed).execute("case-0001")
    return "case-0001"


async def test_quotable_email_becomes_a_drafted_rate_request(cases, feed):
    case = await submit_email(cases, feed, fakes.quotable_request()).execute("case-0001", "email")

    assert case.status is CaseStatus.RATE_REQUEST_DRAFTED
    assert case.pending_email == fakes.EMAIL
    assert case.agent_cost == Decimal("0.002")
    assert cases.get("case-0001") is case


async def test_email_missing_dates_asks_the_salesperson_and_never_drafts_a_rate_request(cases, feed):
    writer = fakes.ScriptedRateRequestWriter()

    case = await submit_email(cases, feed, fakes.request_missing_dates(), writer).execute("case-0001", "email")

    assert case.status is CaseStatus.NEEDS_CLIENT_INFO
    assert writer.calls == 0


async def test_the_same_case_id_cannot_be_submitted_twice(cases, feed):
    await submit_email(cases, feed, fakes.quotable_request()).execute("case-0001", "email")
    with pytest.raises(CaseAlreadyExists):
        await submit_email(cases, feed, fakes.quotable_request()).execute("case-0001", "email")


async def test_progress_is_reported_and_closed_with_done(cases, feed):
    await submit_email(cases, feed, fakes.quotable_request()).execute("case-0001", "email")
    states = [event.state for _, event in feed.events]
    assert states == [ActivityState.RUNNING, ActivityState.DONE]


async def test_a_failing_step_is_reported_as_failed_and_the_case_is_not_saved(cases, feed):
    class Exploding:
        async def extract(self, email_text, on_activity):
            raise RuntimeError("agent down")

    use_case = SubmitClientEmail(Exploding(), fakes.ScriptedRateRequestWriter(), cases, feed, lambda: NOW)
    with pytest.raises(RuntimeError):
        await use_case.execute("case-0001", "email")

    assert feed.events[-1][1].state is ActivityState.FAILED
    assert not cases.exists("case-0001")


async def test_complete_reply_confirms_rates_without_a_followup(cases, feed):
    case_id = await case_awaiting_dorm(cases, feed)
    use_case = SubmitHotelReply(fakes.ScriptedReader(fakes.hotel_reply("189")), fakes.ScriptedRateRules(), fakes.ScriptedFollowupWriter(), cases, feed)

    case = await use_case.execute(case_id, "rates attached")

    assert case.status is CaseStatus.RATES_CONFIRMED
    assert case.pending_email is None
    assert case.reconciliation.revenue == Decimal("378.00")


async def test_incomplete_reply_sends_one_correction_email_without_approval(cases, feed):
    case_id = await case_awaiting_dorm(cases, feed)
    use_case = SubmitHotelReply(fakes.ScriptedReader(fakes.hotel_reply(None)), fakes.ScriptedRateRules(), fakes.ScriptedFollowupWriter(), cases, feed)

    case = await use_case.execute(case_id, "TBC")

    assert case.status is CaseStatus.AWAITING_DORM_CORRECTION
    assert case.pending_email is None
    assert case.sent_to_dorm[-1].subject == "Follow-up"


async def test_the_reader_gets_only_the_latest_reply_each_time(cases, feed):
    case_id = await case_awaiting_dorm(cases, feed)
    reader = fakes.ScriptedReader(fakes.hotel_reply(None))
    use_case = SubmitHotelReply(reader, fakes.ScriptedRateRules(), fakes.ScriptedFollowupWriter(), cases, feed)
    await use_case.execute(case_id, "first reply")

    await use_case.execute(case_id, "second reply")

    assert reader.replies == ["first reply", "second reply"]


async def test_a_reply_before_the_rate_request_is_sent_is_refused_before_any_agent_runs(cases, feed):
    await submit_email(cases, feed, fakes.quotable_request()).execute("case-0001", "email")
    reader = fakes.ScriptedReader(fakes.hotel_reply("189"))

    with pytest.raises(InvalidCaseTransition):
        await SubmitHotelReply(reader, fakes.ScriptedRateRules(), fakes.ScriptedFollowupWriter(), cases, feed).execute("case-0001", "reply")

    assert reader.replies == []


async def test_proposal_is_stored_and_flags_verification_problems(cases, feed):
    case_id = await case_awaiting_dorm(cases, feed)
    await SubmitHotelReply(fakes.ScriptedReader(fakes.hotel_reply("189")), fakes.ScriptedRateRules(), fakes.ScriptedFollowupWriter(), cases, feed).execute(case_id, "rates")
    documents = fakes.MemoryDocuments()

    case = await GenerateProposal(fakes.ScriptedComposer(("missing: 189.00",)), fakes.ScriptedHandoff(), documents, cases, feed).execute(case_id)

    assert case.status is CaseStatus.PROPOSAL_READY
    assert documents.load(case.proposal.document_id) == b"docx-bytes"
    assert case.proposal.verification_problems == ("missing: 189.00",)


async def test_proposal_requires_confirmed_rates(cases, feed):
    case_id = await case_awaiting_dorm(cases, feed)
    with pytest.raises(InvalidCaseTransition):
        await GenerateProposal(fakes.ScriptedComposer(), fakes.ScriptedHandoff(), fakes.MemoryDocuments(), cases, feed).execute(case_id)


async def test_unknown_case_is_a_typed_error(cases, feed):
    with pytest.raises(CaseNotFound):
        await SendPendingEmail(cases, feed).execute("missing")
