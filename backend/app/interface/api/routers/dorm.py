from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.domain.case import CASE_ID_PATTERN
from app.interface.api import presenters, schemas
from app.interface.api.dependencies import Services, require_dorm

router = APIRouter(prefix="/dorm/requests", tags=["dorm"], dependencies=[Depends(require_dorm)])

CaseIdPath = Annotated[str, Path(pattern=CASE_ID_PATTERN.pattern)]


@router.get("", response_model=list[schemas.DormRequestSummaryView])
def list_requests(services: Services) -> list[schemas.DormRequestSummaryView]:
    return [presenters.dorm_summary(case) for case in services.list_dorm_requests.execute()]


@router.get("/{case_id}", response_model=schemas.DormRequestView)
def get_request(case_id: CaseIdPath, services: Services) -> schemas.DormRequestView:
    return presenters.dorm_request(services.get_dorm_request.execute(case_id), services.hotel)


@router.post("/{case_id}/reply", response_model=schemas.DormRequestView)
async def reply_to_request(case_id: CaseIdPath, body: schemas.SubmitHotelReplyBody, services: Services) -> schemas.DormRequestView:
    services.get_dorm_request.execute(case_id)  # Not a request this DORM can see: answer 404 before spending anything.
    case = await services.submit_hotel_reply.execute(case_id, body.reply_text)
    return presenters.dorm_request(case, services.hotel)
