from app.application.activity import ActivityHandler, ActivitySource
from app.application.ports import Costed
from app.domain.email_content import looks_like_html
from app.domain.group_request import GroupRequest
from app.domain.hotel import Property
from app.domain.hotel_reply import HotelReply
from app.infrastructure.cominty.agent_outputs import HotelReplyOutput, validated
from app.infrastructure.cominty.agent_runner import AgentRunner
from app.infrastructure.cominty.html_text import describe_reply
from app.infrastructure.cominty.prompt_library import PromptLibrary, PromptName
from app.infrastructure.cominty.serialization import request_view, to_json


class CominyRateReplyReader:
    """Reads the DORM's latest reply. It holds the whole grid, so earlier replies are not needed."""

    def __init__(self, runner: AgentRunner, prompts: PromptLibrary, hotel: Property) -> None:
        self._runner = runner
        self._prompts = prompts
        self._hotel = hotel

    async def read(self, request: GroupRequest, reply: str, on_activity: ActivityHandler) -> Costed[HotelReply]:
        text = describe_reply(reply) if looks_like_html(reply) else reply
        payload = f"REQUEST:\n{to_json(request_view(request))}\n\nDORM REPLY:\n{text}"
        answer = await self._runner.run_json(
            ActivitySource.RATE_REPLY, self._prompts.render(PromptName.RATE_REPLY), payload, on_activity
        )
        output = validated(HotelReplyOutput, answer.data)
        return Costed(output.to_domain(self._hotel.currency), answer.cost)
