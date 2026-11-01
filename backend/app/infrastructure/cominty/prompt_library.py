from collections.abc import Callable
from datetime import date
from enum import StrEnum
from pathlib import Path
from string import Template

from app.domain.hotel import Property

PROMPT_DIR = Path(__file__).parent / "prompts"


class PromptName(StrEnum):
    INTAKE = "intake"
    RATE_REPLY = "rate_reply"
    RATE_GUARD = "rate_guard"
    HANDOFF = "handoff"


class PromptLibrary:
    """Loads the agents' instructions from Markdown files, so they can be edited or pasted into the Cominty console."""

    def __init__(self, hotel: Property, today: Callable[[], date]) -> None:
        self._hotel = hotel
        self._today = today

    def render(self, name: PromptName) -> str:
        variables = {
            "property_name": self._hotel.name,
            "city": self._hotel.city,
            "room_types": ", ".join(self._hotel.room_types),
            "today": self._today().isoformat(),
            "json_only": (PROMPT_DIR / "_json_only.md").read_text().strip(),
        }
        return Template((PROMPT_DIR / f"{name}.md").read_text()).substitute(variables)
