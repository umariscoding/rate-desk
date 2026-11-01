from dataclasses import asdict

from app.application.activity import ActivityHandler, ActivitySource
from app.application.ports import Costed
from app.domain.case import Handoff
from app.domain.group_request import GroupRequest
from app.domain.hotel import Property
from app.domain.hotel_reply import HotelReply
from app.domain.reconciliation import Reconciliation
from app.infrastructure.cominty.agent_outputs import HandoffOutput, validated
from app.infrastructure.cominty.agent_runner import AgentRunner
from app.infrastructure.cominty.prompt_library import PromptLibrary, PromptName
from app.infrastructure.cominty.serialization import to_json
from app.infrastructure.documents.proposal_payload import format_day, format_money


class CominyProposalHandoff:
    """One agent run: it writes the client's cover email from the confirmed quote."""

    def __init__(self, runner: AgentRunner, prompts: PromptLibrary, hotel: Property) -> None:
        self._runner = runner
        self._prompts = prompts
        self._hotel = hotel

    async def hand_off(
        self, request: GroupRequest, quote: Reconciliation, reply: HotelReply, on_activity: ActivityHandler
    ) -> Costed[Handoff]:
        answer = await self._runner.run_json(
            ActivitySource.HANDOFF, self._prompts.render(PromptName.HANDOFF), self._facts(request, quote, reply), on_activity
        )
        return Costed(validated(HandoffOutput, answer.data).to_domain(), answer.cost)

    def _facts(self, request: GroupRequest, quote: Reconciliation, reply: HotelReply) -> str:
        """Only what a client email needs. Commission and the DORM's notes stay out."""
        terms = reply.terms
        return to_json(
            {
                "hotel": self._hotel.name,
                "salesperson": asdict(self._hotel.salesperson),
                "client": {"name": request.client.name, "company": request.client.company},
                "event_name": request.event_name,
                "arrival": format_day(request.arrival) if request.arrival else None,
                "departure": format_day(request.departure) if request.departure else None,
                "nights": len(request.nights),
                "room_nights": quote.room_nights,
                "total_room_revenue": format_money(quote.revenue),
                "currency": reply.currency,
                "option_date": format_day(terms.option_date) if terms.option_date else None,
            }
        )
