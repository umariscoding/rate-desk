"""Record real agent answers once, then replay them for free.

Development aid for testing everything that is not the AI itself. In `record` mode a saved answer is reused when
there is one, and only a missing one is fetched from Cominty and saved. In `replay` mode Cominty is never called.
An answer is found by the agent role and the exact input it was given, so the same input always gets the same
recorded answer. If the input changes, or a prompt does, delete the fixtures and record again.
"""
import hashlib
import json
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from app.application.activity import ActivityEvent, ActivityHandler, ActivitySource, ActivityState
from app.application.errors import AgentFailure
from app.infrastructure.cominty.agent_runner import AgentJson, AgentRunner


class AgentMode(StrEnum):
    LIVE = "live"
    RECORD = "record"
    REPLAY = "replay"


class FixtureAgentRunner:
    def __init__(self, live: AgentRunner, directory: Path, mode: AgentMode) -> None:
        self._live = live
        self._directory = directory
        self._mode = mode
        directory.mkdir(parents=True, exist_ok=True)

    async def run_json(self, role: ActivitySource, instructions: str, payload: str, on_activity: ActivityHandler) -> AgentJson:
        stem = self._stem(role, payload)
        if self._has_answer(stem):
            await self._announce_replay(role, on_activity)
            return AgentJson(self._load(stem)["data"], Decimal(0))
        self._refuse_to_call_live(stem)
        answer = await self._live.run_json(role, instructions, payload, on_activity)
        self._save(stem, {"role": role, "data": answer.data, "cost": str(answer.cost)})
        return answer

    async def _announce_replay(self, role: ActivitySource, on_activity: ActivityHandler) -> None:
        await on_activity(ActivityEvent(role, "Replayed a recorded answer (no Cominty call)", ActivityState.DONE, key=f"replay:{role}"))

    def _stem(self, role: ActivitySource, payload: str) -> str:
        return f"{role}-{hashlib.sha256(payload.encode()).hexdigest()[:16]}"

    def _has_answer(self, stem: str) -> bool:
        return (self._directory / f"{stem}.json").exists()

    def _refuse_to_call_live(self, stem: str) -> None:
        if self._mode is AgentMode.REPLAY:
            raise AgentFailure(f"No recorded answer for {stem}. Record one with AGENT_MODE=record, or use AGENT_MODE=live.")

    def _load(self, stem: str) -> dict:
        return json.loads((self._directory / f"{stem}.json").read_text())

    def _save(self, stem: str, content: dict) -> None:
        (self._directory / f"{stem}.json").write_text(json.dumps(content, indent=2, default=str))
