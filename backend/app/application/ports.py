"""What the use cases need from the outside world. Infrastructure implements these; nothing here is concrete."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Generic, Protocol, TypeVar

from app.application.activity import ActivityHandler
from app.domain.case import Case, Handoff, OutboundEmail
from app.domain.group_request import GroupRequest
from app.domain.hotel_reply import HotelReply
from app.domain.rate_rule import RateRule
from app.domain.reconciliation import Reconciliation
from app.domain.user import User

T = TypeVar("T")


@dataclass(frozen=True)
class Costed(Generic[T]):
    """An agent's result together with what producing it cost."""

    value: T
    cost: Decimal


@dataclass(frozen=True)
class ComposedProposal:
    file_name: str
    content: bytes
    verification_problems: tuple[str, ...]


class RequestExtractor(Protocol):
    async def extract(self, email_text: str, on_activity: ActivityHandler) -> Costed[GroupRequest]: ...


class RateRequestWriter(Protocol):
    async def write(self, request: GroupRequest, on_activity: ActivityHandler) -> Costed[OutboundEmail]: ...


class RateReplyReader(Protocol):
    async def read(self, request: GroupRequest, reply: str, on_activity: ActivityHandler) -> Costed[HotelReply]:
        """`reply` is the DORM's latest email. It holds the whole grid, so earlier replies are not needed."""
        ...


class FollowupWriter(Protocol):
    async def write(
        self, request: GroupRequest, quote: Reconciliation, on_activity: ActivityHandler
    ) -> Costed[OutboundEmail]:
        """One email that tells the DORM everything missing or wrong, with their rates pre-filled in the grid."""
        ...


class ProposalComposer(Protocol):
    async def compose(
        self, request: GroupRequest, quote: Reconciliation, reply: HotelReply, on_activity: ActivityHandler
    ) -> Costed[ComposedProposal]: ...


class RateRuleReader(Protocol):
    async def read(self, request: GroupRequest, on_activity: ActivityHandler) -> Costed[tuple[RateRule, ...]]:
        """The hotel's rate rules for the room types in this request. Empty when the policy cannot be found."""
        ...


class ProposalHandoff(Protocol):
    async def hand_off(
        self, request: GroupRequest, quote: Reconciliation, reply: HotelReply, on_activity: ActivityHandler
    ) -> Costed[Handoff]:
        """Write the cover email the salesperson sends to the client with the proposal."""
        ...


class CaseRepository(Protocol):
    def exists(self, case_id: str) -> bool: ...

    def get(self, case_id: str) -> Case:
        """Raises CaseNotFound."""
        ...

    def save(self, case: Case) -> None: ...

    def list_recent(self) -> list[Case]: ...


class DocumentStore(Protocol):
    def save(self, case_id: str, file_name: str, content: bytes) -> str:
        """Returns the document id."""
        ...

    def load(self, document_id: str) -> bytes: ...


class UserDirectory(Protocol):
    def authenticate(self, username: str, password: str) -> User | None: ...


class SessionTokens(Protocol):
    def issue(self, user: User) -> str: ...

    def read(self, token: str) -> User | None:
        """None when the token is forged, malformed or expired."""
        ...
