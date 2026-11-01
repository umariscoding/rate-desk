import asyncio
from datetime import UTC, datetime

import pytest

from app.application.activity import ActivityEvent, ActivitySource, ActivityState
from app.domain.case import Case, ProposalDocument
from app.domain.errors import CaseNotFound
from app.domain.reconciliation import reconcile
from app.infrastructure.persistence.in_memory_activity_feed import InMemoryActivityFeed
from app.infrastructure.persistence.json_case_repository import JsonCaseRepository
from tests.application import fakes


def finished_case(case_id: str = "case-0001") -> Case:
    case = Case(case_id, datetime(2026, 10, 25, 9, 30, tzinfo=UTC), "client email")
    request = fakes.quotable_request()
    case.record_extraction(request, fakes.EMAIL)
    case.send_pending_email()
    reply = fakes.hotel_reply("189")
    case.record_hotel_reply("dorm reply", reply, reconcile(request, reply), None)
    case.record_proposal(ProposalDocument("proposal.docx", "case-0001-ab12cd34.docx", ("a problem",)))
    case.add_cost(fakes.COST)
    return case


def test_a_whole_case_survives_a_save_and_load(tmp_path):
    repository = JsonCaseRepository(tmp_path)
    case = finished_case()

    repository.save(case)

    assert repository.get("case-0001") == case


def test_unknown_and_unsafe_ids_are_not_found(tmp_path):
    repository = JsonCaseRepository(tmp_path)
    for case_id in ("case-9999", "../secrets", ""):
        assert not repository.exists(case_id)
        with pytest.raises(CaseNotFound):
            repository.get(case_id)


def test_cases_are_listed_newest_first(tmp_path):
    repository = JsonCaseRepository(tmp_path)
    repository.save(finished_case("case-0001"))
    repository.save(finished_case("case-0002"))

    assert [case.id for case in repository.list_recent()] == ["case-0002", "case-0001"]


async def test_a_late_subscriber_gets_the_history_then_live_events():
    feed = InMemoryActivityFeed()

    def event(label: str) -> ActivityEvent:
        return ActivityEvent(ActivitySource.SYSTEM, label, ActivityState.DONE, label)

    await feed.publish("case-0001", event("early"))
    received: list[str] = []

    async def listen():
        async for item in feed.subscribe("case-0001"):
            received.append(item.label)

    task = asyncio.create_task(listen())
    await asyncio.sleep(0.01)
    await feed.publish("case-0001", event("live"))
    await asyncio.sleep(0.01)
    task.cancel()

    assert received == ["early", "live"]
