from dataclasses import dataclass

from app.application.ports import SessionTokens, UserDirectory
from app.domain.errors import InvalidCredentials
from app.domain.user import User


@dataclass(frozen=True)
class Session:
    token: str
    user: User


class LogIn:
    def __init__(self, users: UserDirectory, tokens: SessionTokens) -> None:
        self._users = users
        self._tokens = tokens

    def execute(self, username: str, password: str) -> Session:
        user = self._users.authenticate(username, password)
        if user is None:
            raise InvalidCredentials()
        return Session(self._tokens.issue(user), user)
