import base64
import hashlib
import hmac
import json
from collections.abc import Callable
from datetime import datetime, timedelta

from app.domain.user import Role, User


class SignedSessionTokens:
    """Self-contained tokens: a JSON payload plus an HMAC signature. Nothing is stored on the server."""

    def __init__(self, secret: str, lifetime: timedelta, now: Callable[[], datetime]) -> None:
        self._key = secret.encode()
        self._lifetime = lifetime
        self._now = now

    def issue(self, user: User) -> str:
        expires = (self._now() + self._lifetime).timestamp()
        payload = {"u": user.username, "n": user.display_name, "r": user.role, "exp": expires}
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        return f"{body}.{self._sign(body)}"

    def read(self, token: str) -> User | None:
        body, _, signature = token.partition(".")
        if not hmac.compare_digest(signature, self._sign(body)):
            return None
        try:
            payload = json.loads(base64.urlsafe_b64decode(body.encode()))
            if payload["exp"] < self._now().timestamp():
                return None
            return User(payload["u"], payload["n"], Role(payload["r"]))
        except (ValueError, KeyError):
            return None

    def _sign(self, body: str) -> str:
        return hmac.new(self._key, body.encode(), hashlib.sha256).hexdigest()
