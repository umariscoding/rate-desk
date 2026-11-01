import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.errors import AgentFailure
from app.domain.errors import (
    CaseAlreadyExists,
    CaseNotFound,
    DomainError,
    InvalidCaseTransition,
    InvalidCredentials,
    NotAuthenticated,
    NotPermitted,
    NothingToSend,
    ProposalNotReady,
)

logger = logging.getLogger(__name__)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    CaseNotFound: 404,
    CaseAlreadyExists: 409,
    InvalidCaseTransition: 409,
    NothingToSend: 409,
    ProposalNotReady: 409,
    InvalidCredentials: 401,
    NotAuthenticated: 401,
    NotPermitted: 403,
}
UNSPECIFIED_DOMAIN_ERROR_STATUS = 400
AGENT_FAILURE_STATUS = 502


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(_: Request, error: DomainError) -> JSONResponse:
        status = STATUS_BY_ERROR.get(type(error), UNSPECIFIED_DOMAIN_ERROR_STATUS)
        return JSONResponse({"detail": str(error)}, status_code=status)

    @app.exception_handler(AgentFailure)
    async def agent_failure(_: Request, error: AgentFailure) -> JSONResponse:
        logger.error("Agent failure: %s", error)
        return JSONResponse({"detail": str(error)}, status_code=AGENT_FAILURE_STATUS)
