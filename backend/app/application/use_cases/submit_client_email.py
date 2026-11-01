from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from app.application.activity import ActivityFeed, reporting
from app.application.ports import CaseRepository, RateRequestWriter, RequestExtractor
from app.domain.case import Case
from app.domain.errors import CaseAlreadyExists


class SubmitClientEmail:
    """A salesperson pastes a client's email: extract the request, and if it can be quoted, draft the rate request."""

    def __init__(
        self,
        extractor: RequestExtractor,
        rate_request_writer: RateRequestWriter,
        cases: CaseRepository,
        feed: ActivityFeed,
        now: Callable[[], datetime],
    ) -> None:
        self._extractor = extractor
        self._rate_request_writer = rate_request_writer
        self._cases = cases
        self._feed = feed
        self._now = now

    async def execute(self, case_id: str, email_text: str) -> Case:
        if self._cases.exists(case_id):
            raise CaseAlreadyExists(case_id)
        case = Case(case_id, self._now(), email_text)
        async with reporting(self._feed, case_id, "Reading the client's email") as publish:
            extraction = await self._extractor.extract(email_text, publish)
            case.add_cost(extraction.cost)
            request = extraction.value
            draft = await self._rate_request_writer.write(request, publish) if request.is_quotable else None
            case.record_extraction(request, draft.value if draft else None)
            case.add_cost(draft.cost if draft else Decimal(0))
        self._cases.save(case)
        return case
