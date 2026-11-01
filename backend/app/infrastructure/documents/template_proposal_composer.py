"""Builds the proposal by filling the placeholders of a Word template. No agent: every value is already known."""
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.text.paragraph import Paragraph

from app.application.activity import ActivityHandler
from app.application.ports import ComposedProposal, Costed
from app.domain.group_request import GroupRequest
from app.domain.hotel import Property
from app.domain.hotel_reply import HotelReply
from app.domain.reconciliation import Reconciliation
from app.infrastructure.documents import docx_checker
from app.infrastructure.documents.docx_repair import rebuild_rate_table
from app.infrastructure.documents.proposal_payload import ProposalPayload, build_proposal_payload

FREE_OF_CHARGE = Decimal(0)
NO_SERVICES = "No additional services requested."
UNKNOWN_EVENT = "Group stay"


class TemplateProposalComposer:
    def __init__(self, hotel: Property, template: Path, today: Callable[[], date]) -> None:
        self._hotel = hotel
        self._template = template
        self._today = today

    async def compose(
        self, request: GroupRequest, quote: Reconciliation, reply: HotelReply, on_activity: ActivityHandler
    ) -> Costed[ComposedProposal]:
        payload = build_proposal_payload(self._hotel, request, quote, reply, self._today())
        content = rebuild_rate_table(self._template.read_bytes(), payload)
        content = _fill_placeholders(content, _values(payload))
        problems = docx_checker.find_problems(content, payload)
        return Costed(ComposedProposal(f"Proposal {payload.proposal_ref}.docx", content, problems), FREE_OF_CHARGE)


def _values(payload: ProposalPayload) -> dict[str, str]:
    client, salesperson = payload.client, payload.salesperson
    return {
        "PROPERTY_NAME": payload.property_name,
        "PROPERTY_ADDRESS": payload.property_address,
        "PROPOSAL_REF": payload.proposal_ref,
        "PROPOSAL_DATE": payload.proposal_date,
        "CLIENT_NAME": client["name"] or "",
        "CLIENT_COMPANY": client["company"] or "",
        "CLIENT_EMAIL": client["email"] or "",
        "EVENT_NAME": payload.event_name or UNKNOWN_EVENT,
        "ARRIVAL_DATE": payload.arrival_date,
        "DEPARTURE_DATE": payload.departure_date,
        "NIGHT_COUNT": str(payload.night_count),
        "CURRENCY": payload.currency,
        "TAX_NOTE": f"Taxes: {payload.tax_note}.",
        "TOTAL_ROOM_NIGHTS": str(payload.total_room_nights),
        "TOTAL_REVENUE": payload.total_revenue,
        "ADDITIONAL_SERVICES": "\n".join(payload.services) or NO_SERVICES,
        "OPTION_DATE": payload.option_date,
        "ATTRITION": payload.attrition,
        "CANCELLATION": payload.cancellation,
        "SALESPERSON_NAME": salesperson["name"],
        "SALESPERSON_TITLE": salesperson["title"],
        "SALESPERSON_EMAIL": salesperson["email"],
    }


def _fill_placeholders(content: bytes, values: dict[str, str]) -> bytes:
    document = Document(BytesIO(content))
    for paragraph in _paragraphs(document):
        for run in paragraph.runs:
            for name, value in values.items():
                run.text = run.text.replace(f"{{{{{name}}}}}", value)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _paragraphs(document: DocxDocument) -> Iterator[Paragraph]:
    yield from document.paragraphs
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs
