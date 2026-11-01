"""How domain objects are shown to an agent: plain JSON in the same shape the Intake agent produced."""
import json
from dataclasses import asdict
from itertools import groupby
from typing import Any

from app.domain.group_request import GroupRequest


def to_json(value: Any) -> str:
    return json.dumps(value, indent=2, default=str)


def request_view(request: GroupRequest) -> dict:
    ordered = sorted(request.room_nights, key=lambda need: need.day)
    nights = [
        {"date": day, "rooms": {need.room_type: need.rooms for need in group}}
        for day, group in groupby(ordered, key=lambda need: need.day)
    ]
    return {
        "client": asdict(request.client),
        "event_name": request.event_name,
        "arrival_date": request.arrival,
        "departure_date": request.departure,
        "nights": nights,
        "requirements": list(request.requirements),
    }
