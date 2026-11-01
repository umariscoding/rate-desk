import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.responses import StreamingResponse

from app.container import Container
from app.domain.case import CASE_ID_PATTERN
from app.interface.api import presenters
from app.interface.api.dependencies import Services, activity_viewer

router = APIRouter(tags=["activity"], dependencies=[Depends(activity_viewer)])

KEEPALIVE_SECONDS = 15
CaseIdPath = Annotated[str, Path(pattern=CASE_ID_PATTERN.pattern)]


@router.get("/cases/{case_id}/activity")
async def stream_activity(case_id: CaseIdPath, services: Services) -> StreamingResponse:
    """Server-sent events: what the agents are doing for this case, replayed from the start for late listeners."""
    return StreamingResponse(_server_sent_events(services, case_id), media_type="text/event-stream")


async def _server_sent_events(services: Container, case_id: str) -> AsyncIterator[str]:
    events = services.feed.subscribe(case_id)
    pending = asyncio.ensure_future(anext(events))
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=KEEPALIVE_SECONDS)
            if not done:
                yield ": keepalive\n\n"  # Keeps proxies from closing an idle stream.
                continue
            yield f"data: {presenters.activity_view(pending.result()).model_dump_json()}\n\n"
            pending = asyncio.ensure_future(anext(events))
    finally:
        pending.cancel()  # The feed's own cleanup runs when the cancelled read unwinds.
