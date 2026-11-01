"""Turns Cominty's stream events into the activity events our UI shows. Raw model reasoning is never forwarded."""
from cominty_sdk import events

from app.application.activity import ActivityEvent, ActivitySource, ActivityState

MAX_LABEL_LENGTH = 90
HEADLINE_BREAKS = (". ", ": ", "\n")
_STATES = {"running": ActivityState.RUNNING, "success": ActivityState.DONE, "error": ActivityState.FAILED}


def translate(event: events.AnyEvent, source: ActivitySource) -> ActivityEvent | None:
    label = _label(event)
    if label is None:
        return None
    state = _STATES.get(event.status, ActivityState.RUNNING)
    return ActivityEvent(source, label[:MAX_LABEL_LENGTH], state, key=f"{source}:{event.id}")


def _label(event: events.AnyEvent) -> str | None:
    match event:
        case events.LlmStep():
            return "Thinking"
        case events.IntermediaryUpdate():
            return _headline(event.data.message)
        case events.ToolCall():
            return event.data.description or event.data.name
        case _:
            return None


def _headline(note: str) -> str:
    """An agent's progress note can run to a paragraph of working. The first clause says what it is doing."""
    cuts = [note.find(mark) for mark in HEADLINE_BREAKS if note.find(mark) > 0]
    return note[: min(cuts)] if cuts else note
