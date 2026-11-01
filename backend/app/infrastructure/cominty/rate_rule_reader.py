from app.application.activity import ActivityHandler, ActivitySource
from app.application.ports import Costed
from app.domain.group_request import GroupRequest
from app.domain.hotel import Property
from app.domain.rate_rule import RateRule
from app.infrastructure.cominty.agent_outputs import RateRulesOutput, validated
from app.infrastructure.cominty.agent_runner import AgentRunner
from app.infrastructure.cominty.prompt_library import PromptLibrary, PromptName
from app.infrastructure.cominty.serialization import to_json


class CominyRateRuleReader:
    """The Rate Guard agent reads the hotel's policy from the Cominty knowledge base and returns its rate rules."""

    def __init__(self, runner: AgentRunner, prompts: PromptLibrary, hotel: Property) -> None:
        self._runner = runner
        self._prompts = prompts
        self._hotel = hotel

    async def read(self, request: GroupRequest, on_activity: ActivityHandler) -> Costed[tuple[RateRule, ...]]:
        room_types = sorted({need.room_type for need in request.room_nights})
        payload = to_json({"hotel": self._hotel.name, "room_types": room_types})
        answer = await self._runner.run_json(
            ActivitySource.RATE_GUARD, self._prompts.render(PromptName.RATE_GUARD), payload, on_activity
        )
        return Costed(validated(RateRulesOutput, answer.data).to_domain(), answer.cost)
