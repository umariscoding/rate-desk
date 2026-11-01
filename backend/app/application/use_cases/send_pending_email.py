from app.application.activity import ActivityEvent, ActivityFeed, ActivitySource, ActivityState
from app.application.ports import CaseRepository
from app.domain.case import Case


class SendPendingEmail:
    """The salesperson approves the drafted email (rate request or follow-up) and it goes to the DORM."""

    def __init__(self, cases: CaseRepository, feed: ActivityFeed) -> None:
        self._cases = cases
        self._feed = feed

    async def execute(self, case_id: str) -> Case:
        case = self._cases.get(case_id)
        sent = case.send_pending_email()
        self._cases.save(case)
        label = f"Email sent to {sent.to_name}: {sent.subject}"
        await self._feed.publish(case_id, ActivityEvent(ActivitySource.SYSTEM, label, ActivityState.DONE))
        return case
