"""Independent check of the generated proposal: the agent wrote it, this proves the numbers made it in intact."""
from io import BytesIO

from docx import Document

from app.infrastructure.documents.proposal_payload import ProposalPayload


def read_text(content: bytes) -> str:
    document = Document(BytesIO(content))
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        parts.extend(cell.text for row in table.rows for cell in row.cells)
    return "\n".join(parts)


def find_problems(content: bytes, payload: ProposalPayload) -> tuple[str, ...]:
    text = read_text(content)
    problems = []
    if "{{" in text or "}}" in text:
        problems.append("The document still contains an unfilled placeholder")
    problems += [f"Missing from the document: {item}" for item in _expected(payload) if item not in text]
    commission = payload.internal_do_not_print.get("commission")
    if commission and commission.lower() in text.lower():
        problems.append("Internal commission text appears in the document")
    return tuple(problems)


def _expected(payload: ProposalPayload) -> list[str]:
    fixed = [payload.client["name"], payload.property_name, payload.arrival_date, payload.departure_date, payload.total_revenue]
    per_line = [item for line in payload.lines for item in (line.date, line.rate, line.amount)]
    return [item for item in (*fixed, *per_line) if item]
