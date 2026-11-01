import hmac
from collections.abc import Sequence

from app.domain.user import User


class DemoUserDirectory:
    """A fixed list of users sharing one demo password. Enough to separate roles in a proof of concept, not for production."""

    def __init__(self, users: Sequence[User], password: str) -> None:
        self._users = {user.username: user for user in users}
        self._password = password

    def authenticate(self, username: str, password: str) -> User | None:
        user = self._users.get(username.strip().lower())
        password_matches = hmac.compare_digest(password.encode(), self._password.encode())
        return user if user is not None and password_matches else None
