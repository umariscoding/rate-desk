"""What a client asked for, extracted from their email."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ClientContact:
    name: str | None
    company: str | None
    email: str | None
    phone: str | None


@dataclass(frozen=True)
class RoomNight:
    """Rooms of one type needed on one night (the night starting on `day`)."""

    day: date
    room_type: str
    rooms: int


@dataclass(frozen=True)
class MissingInformation:
    """A blocker: without it the hotel cannot quote. `question` is what to ask the client."""

    field: str
    question: str


@dataclass(frozen=True)
class GroupRequest:
    client: ClientContact
    event_name: str | None
    arrival: date | None
    departure: date | None
    room_nights: tuple[RoomNight, ...]
    requirements: tuple[str, ...]
    missing: tuple[MissingInformation, ...]
    notes: tuple[str, ...]

    @property
    def is_quotable(self) -> bool:
        return not self.missing and bool(self.room_nights)

    @property
    def nights(self) -> tuple[date, ...]:
        return tuple(sorted({item.day for item in self.room_nights}))
