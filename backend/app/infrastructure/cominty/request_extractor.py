from app.application.activity import ActivityHandler, ActivitySource
from app.application.ports import Costed
from app.domain.group_request import GroupRequest
from app.infrastructure.cominty.agent_outputs import IntakeOutput, validated
from app.infrastructure.cominty.agent_runner import AgentRunner
from app.infrastructure.cominty.prompt_library import PromptLibrary, PromptName


class CominyRequestExtractor:
    def __init__(self, runner: AgentRunner, prompts: PromptLibrary) -> None:
        self._runner = runner
        self._prompts = prompts

    async def extract(self, email_text: str, on_activity: ActivityHandler) -> Costed[GroupRequest]:
        answer = await self._runner.run_json(
            ActivitySource.INTAKE, self._prompts.render(PromptName.INTAKE), email_text, on_activity
        )
        output = validated(IntakeOutput, answer.data)
        return Costed(output.to_domain(), answer.cost)
