"""The property we sell for and the people who work on its group desk."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    name: str
    title: str
    email: str


@dataclass(frozen=True)
class Property:
    name: str
    city: str
    address: str
    currency: str
    room_types: tuple[str, ...]
    dorm: Contact
    salesperson: Contact
