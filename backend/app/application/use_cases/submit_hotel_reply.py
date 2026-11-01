from app.application.activity import ActivityEvent, ActivityFeed, ActivitySource, ActivityState, reporting
from app.application.ports import CaseRepository, FollowupWriter, RateReplyReader, RateRuleReader
from app.domain.case import Case, CaseStatus, OutboundEmail
from app.domain.reconciliation import reconcile


class SubmitHotelReply:
    """The DORM's reply arrives: read the rates, check them against the hotel's rules with exact arithmetic, and write
    one correction email if anything is missing or wrong."""

    def __init__(
        self,
        reader: RateReplyReader,
        rule_reader: RateRuleReader,
        followup_writer: FollowupWriter,
        cases: CaseRepository,
        feed: ActivityFeed,
    ) -> None:
        self._reader = reader
        self._rule_reader = rule_reader
        self._followup_writer = followup_writer
        self._cases = cases
        self._feed = feed

    async def execute(self, case_id: str, reply_text: str) -> Case:
        case = self._cases.get(case_id)
        request = case.begin_hotel_reply()
        async with reporting(self._feed, case_id, "Reading the DORM's reply") as publish:
            reading = await self._reader.read(request, reply_text, publish)
            case.add_cost(reading.cost)
            await self._ensure_rate_rules(case, request, publish)
            quote = reconcile(request, reading.value, case.rate_rules or ())
            followup = await self._draft_followup(case, request, quote, publish)
            case.record_hotel_reply(reply_text, reading.value, quote, followup)
        self._cases.save(case)
        await self._announce_correction_request(case)
        return case

    async def _ensure_rate_rules(self, case: Case, request, publish) -> None:
        """The policy is read once per case. Later replies reuse the rules, so a correction round costs nothing extra."""
        if case.rate_rules is not None:
            return
        rules = await self._rule_reader.read(request, publish)
        case.add_cost(rules.cost)
        case.record_rate_rules(rules.value)

    async def _draft_followup(self, case: Case, request, quote, publish) -> OutboundEmail | None:
        if quote.is_complete:
            return None
        drafted = await self._followup_writer.write(request, quote, publish)
        case.add_cost(drafted.cost)
        return drafted.value

    async def _announce_correction_request(self, case: Case) -> None:
        if case.status is not CaseStatus.AWAITING_DORM_CORRECTION:
            return
        sent = case.sent_to_dorm[-1]
        label = f"Asked {sent.to_name} for what is missing: {sent.subject}"
        await self._feed.publish(case.id, ActivityEvent(ActivitySource.SYSTEM, label, ActivityState.DONE))
