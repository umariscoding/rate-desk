from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from cominty_sdk import (
    AsyncCominty,
    ComintyError,
    MessageStatus,
    events,
)

from app.application.activity import ActivityHandler, ActivitySource
from app.application.errors import AgentFailure
from app.infrastructure.cominty.json_reply import extract_json_object
from app.infrastructure.cominty.activity_translation import translate

DEFAULT_MAX_STEPS = 10


REPAIR_MESSAGE = (
    "Your reply could not be read as JSON ({problem}). Send the same answer again as one valid JSON object "
    "and nothing else. Escape any double quotes inside strings."
)


@dataclass(frozen=True)
class AgentReply:
    text: str
    cost: Decimal
    thread_id: str = ""


@dataclass(frozen=True)
class AgentJson:
    data: dict
    cost: Decimal


class AgentRunner(Protocol):
    """What the adapters need from an agent runner. The live one talks to Cominty; a fixture one can replay answers."""

    async def run_json(
        self, role: ActivitySource, instructions: str, payload: str, on_activity: ActivityHandler
    ) -> AgentJson: ...


class CominyAgentRunner:
    """Runs one Cominty agent for one message, relays its progress, and turns every failure into AgentFailure."""

    def __init__(self, client: AsyncCominty, agent_ids: Mapping[ActivitySource, str]) -> None:
        self._client = client
        self._agent_ids = agent_ids

    async def run(self, role: ActivitySource, instructions: str, payload: str, on_activity: ActivityHandler) -> AgentReply:
        try:
            return await self._run(role, f"{instructions}\n\n--- INPUT ---\n{payload}", on_activity)
        except ComintyError as error:
            raise AgentFailure(f"Cominty could not complete the {role} step: {error}") from error

    async def run_json(
        self, role: ActivitySource, instructions: str, payload: str, on_activity: ActivityHandler
    ) -> AgentJson:
        """Run an agent that must answer with JSON. If the JSON is malformed, ask once for a corrected answer."""
        reply = await self.run(role, instructions, payload, on_activity)
        try:
            return AgentJson(extract_json_object(reply.text), reply.cost)
        except AgentFailure as problem:
            retry = await self._ask_again(role, reply.thread_id, str(problem), on_activity)
            return AgentJson(extract_json_object(retry.text), reply.cost + retry.cost)

    async def _run(self, role: ActivitySource, message: str, on_activity: ActivityHandler) -> AgentReply:
        run = await self._client.chat.start(
            agent_id=self._agent_ids[role],
            message=message,
            max_steps=DEFAULT_MAX_STEPS,
        )
        return await self._finish(run, role, on_activity, str(run.thread.id))

    async def _ask_again(self, role: ActivitySource, thread_id: str, problem: str, on_activity: ActivityHandler) -> AgentReply:
        try:
            run = await self._client.chat.send(
                thread_id,
                agent_id=self._agent_ids[role],
                message=REPAIR_MESSAGE.format(problem=problem[:200]),
                    max_steps=DEFAULT_MAX_STEPS,
            )
            return await self._finish(run, role, on_activity, thread_id)
        except ComintyError as error:
            raise AgentFailure(f"Cominty could not repair the {role} answer: {error}") from error

    async def _finish(self, run, role: ActivitySource, on_activity: ActivityHandler, thread_id: str) -> AgentReply:
        cost = Decimal(0)
        async for event in run:
            if isinstance(event, events.Result):
                cost = event.data.cost.total
            if (update := translate(event, role)) is not None:
                await on_activity(update)
        reply = await run.result()
        if reply.status is not MessageStatus.success:
            raise AgentFailure(f"The {role} agent ended with status '{reply.status}'")
        return AgentReply(reply.content, cost, thread_id)
