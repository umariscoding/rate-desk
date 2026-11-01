from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, Query, Request

from app.container import Container
from app.domain.errors import NotAuthenticated, NotPermitted
from app.domain.user import Role, User


def get_container(request: Request) -> Container:
    return request.app.state.container


Services = Annotated[Container, Depends(get_container)]


def _user_for(services: Container, token: str | None) -> User:
    user = services.session_tokens.read(token) if token else None
    if user is None:
        raise NotAuthenticated()
    return user


def current_user(services: Services, authorization: Annotated[str | None, Header()] = None) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    return _user_for(services, token if scheme.lower() == "bearer" else None)


CurrentUser = Annotated[User, Depends(current_user)]


def require_role(role: Role) -> Callable[..., User]:
    def guard(user: CurrentUser) -> User:
        if user.role is not role:
            raise NotPermitted()
        return user

    return guard


require_salesperson = require_role(Role.SALESPERSON)
require_dorm = require_role(Role.DORM)


def activity_viewer(services: Services, token: Annotated[str | None, Query()] = None) -> User:
    """Browsers cannot send headers on an EventSource, so only the activity stream accepts the token in the URL."""
    user = _user_for(services, token)
    if user.role is not Role.SALESPERSON:
        raise NotPermitted()
    return user
