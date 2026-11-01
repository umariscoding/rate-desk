"""Live progress of a case: what the agents are doing right now. Feeds the UI's activity stream."""
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from functools import partial
from typing import Protocol


class ActivitySource(StrEnum):
    SYSTEM = "system"
    INTAKE = "intake"
    RATE_REPLY = "rate_reply"
    RATE_GUARD = "rate_guard"
    HANDOFF = "handoff"


class ActivityState(StrEnum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True)
class ActivityEvent:
    source: ActivitySource
    label: str
    state: ActivityState
    key: str = ""  # Events sharing a key describe the same step, so a consumer can update it in place.
    at: datetime = field(default_factory=lambda: datetime.now(UTC))


ActivityHandler = Callable[[ActivityEvent], Awaitable[None]]


class ActivityFeed(Protocol):
    async def publish(self, case_id: str, event: ActivityEvent) -> None: ...

    def subscribe(self, case_id: str) -> AsyncIterator[ActivityEvent]:
        """Replays everything published so far, then follows new events until the consumer stops."""
        ...


@asynccontextmanager
async def reporting(feed: ActivityFeed, case_id: str, label: str) -> AsyncIterator[ActivityHandler]:
    """Announce a step, hand its progress handler to the caller, and always report how it ended."""
    publish = partial(feed.publish, case_id)
    await publish(ActivityEvent(ActivitySource.SYSTEM, label, ActivityState.RUNNING, label))
    try:
        yield publish
    except Exception:
        await publish(ActivityEvent(ActivitySource.SYSTEM, label, ActivityState.FAILED, label))
        raise
    await publish(ActivityEvent(ActivitySource.SYSTEM, label, ActivityState.DONE, label))
