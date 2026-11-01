"""Who is signed in. The desk has two roles and they see different things."""
from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    SALESPERSON = "salesperson"
    DORM = "dorm"  # Director of Revenue Management


@dataclass(frozen=True)
class User:
    username: str
    display_name: str
    role: Role
