"""Puts the rate table right when the agent's version does not match the confirmed quote."""
from io import BytesIO

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table

from app.infrastructure.documents.proposal_payload import ProposalPayload

RATE_TABLE_HEADER = ["Date", "Room type", "Rooms", "Rate per night", "Amount"]
NUMBER_COLUMNS_START = 2


def rebuild_rate_table(content: bytes, payload: ProposalPayload) -> bytes:
    """Replace every body row of the rate table with the confirmed lines. The header and styling stay as they were."""
    document = Document(BytesIO(content))
    table = _find_rate_table(document)
    if table is None:
        return content
    for row in table.rows[1:]:
        table._tbl.remove(row._tr)
    for line in payload.lines:
        _add_line(table, [line.date, line.room_type, str(line.rooms), line.rate, line.amount])
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _find_rate_table(document: DocxDocument) -> Table | None:
    for table in document.tables:
        if [cell.text.strip() for cell in table.rows[0].cells] == RATE_TABLE_HEADER:
            return table
    return None


def _add_line(table: Table, values: list[str]) -> None:
    cells = table.add_row().cells
    for index, (cell, value) in enumerate(zip(cells, values, strict=True)):
        cell.text = value
        if index >= NUMBER_COLUMNS_START:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
