import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator

from app.application.activity import ActivityEvent

MAX_HISTORY_PER_CASE = 500


class InMemoryActivityFeed:
    """Replays a case's history to late subscribers, then streams new events. Single-process by design."""

    def __init__(self) -> None:
        self._history: dict[str, list[ActivityEvent]] = defaultdict(list)
        self._listeners: dict[str, set[asyncio.Queue[ActivityEvent]]] = defaultdict(set)

    async def publish(self, case_id: str, event: ActivityEvent) -> None:
        history = self._history[case_id]
        history.append(event)
        del history[:-MAX_HISTORY_PER_CASE]
        for listener in self._listeners[case_id]:
            listener.put_nowait(event)

    async def subscribe(self, case_id: str) -> AsyncIterator[ActivityEvent]:
        listener: asyncio.Queue[ActivityEvent] = asyncio.Queue()
        backlog = list(self._history[case_id])  # Snapshot and register without awaiting, so no event is missed.
        self._listeners[case_id].add(listener)
        try:
            for event in backlog:
                yield event
            while True:
                yield await listener.get()
        finally:
            self._listeners[case_id].discard(listener)
