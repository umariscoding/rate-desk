"""A rule from the hotel's own policy about what a quoted rate may be. The agent reads the policy; code applies it."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class RateRule:
    """No rate below `minimum` for `room_type` (every type when None) on nights that start on one of `weekdays`."""

    room_type: str | None
    weekdays: tuple[int, ...]  # Monday is 0.
    minimum: Decimal
    source: str  # The policy's own words, so a flagged rate can quote the rule behind it.

    def applies_to(self, day: date, room_type: str) -> bool:
        return day.weekday() in self.weekdays and self.room_type in (None, room_type)
