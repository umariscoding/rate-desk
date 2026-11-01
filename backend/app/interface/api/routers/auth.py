from fastapi import APIRouter

from app.interface.api import presenters, schemas
from app.interface.api.dependencies import CurrentUser, Services

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.SessionView)
def log_in(body: schemas.LoginBody, services: Services) -> schemas.SessionView:
    session = services.log_in.execute(body.username, body.password)
    return schemas.SessionView(token=session.token, user=presenters.user_view(session.user))


@router.get("/me", response_model=schemas.UserView)
def who_am_i(user: CurrentUser) -> schemas.UserView:
    return presenters.user_view(user)
