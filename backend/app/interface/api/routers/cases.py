from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from app.domain.case import CASE_ID_PATTERN
from app.interface.api import presenters, schemas
from app.interface.api.dependencies import Services, require_salesperson

router = APIRouter(prefix="/cases", tags=["cases"], dependencies=[Depends(require_salesperson)])

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

CaseIdPath = Annotated[str, Path(pattern=CASE_ID_PATTERN.pattern)]


@router.post("", response_model=schemas.CaseView, status_code=status.HTTP_201_CREATED)
async def submit_client_email(body: schemas.SubmitClientEmailBody, services: Services) -> schemas.CaseView:
    return presenters.case_view(await services.submit_client_email.execute(body.case_id, body.email_text))


@router.get("", response_model=list[schemas.CaseSummaryView])
def list_cases(services: Services) -> list[schemas.CaseSummaryView]:
    return [presenters.case_summary(case) for case in services.list_cases.execute()]


@router.get("/{case_id}", response_model=schemas.CaseView)
def get_case(case_id: CaseIdPath, services: Services) -> schemas.CaseView:
    return presenters.case_view(services.get_case.execute(case_id))


@router.post("/{case_id}/emails/send", response_model=schemas.CaseView)
async def send_pending_email(case_id: CaseIdPath, services: Services) -> schemas.CaseView:
    return presenters.case_view(await services.send_pending_email.execute(case_id))


@router.post("/{case_id}/proposal", response_model=schemas.CaseView)
async def generate_proposal(case_id: CaseIdPath, services: Services) -> schemas.CaseView:
    return presenters.case_view(await services.generate_proposal.execute(case_id))


@router.get("/{case_id}/proposal/file")
def download_proposal(case_id: CaseIdPath, services: Services) -> Response:
    file_name, content = services.get_proposal_file.execute(case_id)
    headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
    return Response(content, media_type=DOCX_MEDIA_TYPE, headers=headers)
