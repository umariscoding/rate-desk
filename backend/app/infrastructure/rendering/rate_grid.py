"""The grids the DORM fills in. Rendered by code: these room counts and rates are what the hotel commits to, so no model touches them."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from html import escape

from app.domain.group_request import GroupRequest
from app.domain.hotel import Property
from app.domain.reconciliation import ALL_ROOM_TYPES, ProblemKind, Reconciliation

TABLE_OPEN = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse">'
RATE_CELL_CLASS = "rate"  # A cell the DORM must fill in or confirm.
FINAL_CELL_CLASS = "ok"  # A rate already given: shown filled and locked.


class CellState(StrEnum):
    OPEN = "open"
    FINAL = "final"
    NOT_NEEDED = "not_needed"


@dataclass(frozen=True)
class GridCell:
    rooms_text: str
    rate_text: str
    state: CellState


CellFor = Callable[[date, str, int], GridCell]


def render_rate_grid(request: GroupRequest, hotel: Property) -> str:
    """The first rate request: every rate cell is empty."""
    return _render_grid(request, hotel, _empty_cell)


def render_correction_grid(request: GroupRequest, hotel: Property, quote: Reconciliation) -> str:
    """The follow-up: rates the DORM already gave are filled in; only what is missing or in doubt is open."""
    return _render_grid(request, hotel, _cell_from_quote(quote))


def _empty_cell(day: date, room_type: str, needed: int) -> GridCell:
    state = CellState.OPEN if needed > 0 else CellState.NOT_NEEDED
    return GridCell(str(needed), "", state)


def _cell_from_quote(quote: Reconciliation) -> CellFor:
    lines = {(line.day, line.room_type): line for line in quote.lines}
    doubted = {p.room_type for p in quote.problems if p.kind is ProblemKind.TOTAL_MISMATCH}
    below_minimum = {(p.day, p.room_type) for p in quote.problems if p.kind is ProblemKind.BELOW_MINIMUM_RATE}

    def cell(day: date, room_type: str, needed: int) -> GridCell:
        line = lines.get((day, room_type))
        if needed == 0:
            return GridCell("0", "", CellState.NOT_NEEDED)
        if line is None:
            return GridCell(str(needed), "", CellState.OPEN)
        rate = f"{line.rate:,.2f}"
        if line.rooms < needed:
            return GridCell(f"{needed} (you offered {line.rooms})", rate, CellState.OPEN)
        in_doubt = room_type in doubted or ALL_ROOM_TYPES in doubted or (day, room_type) in below_minimum
        return GridCell(str(needed), rate, CellState.OPEN if in_doubt else CellState.FINAL)

    return cell


def _render_grid(request: GroupRequest, hotel: Property, cell_for: CellFor) -> str:
    requested = {need.room_type for need in request.room_nights}
    # The hotel's own room order first, so the DORM reads columns the way their rate sheet does.
    room_types = sorted(requested, key=lambda kind: (_rank(kind, hotel), kind))
    rooms = {(need.day, need.room_type): need.rooms for need in request.room_nights}
    rows = [_header(room_types, hotel.currency)]
    rows += [_night_row(day, room_types, rooms, cell_for) for day in request.nights]
    rows.append(_total_row(room_types, rooms))
    return f"{TABLE_OPEN}{''.join(rows)}</table>"


def _rank(room_type: str, hotel: Property) -> int:
    return hotel.room_types.index(room_type) if room_type in hotel.room_types else len(hotel.room_types)


def _header(room_types: list[str], currency: str) -> str:
    cells = ["<th>Date</th>"]
    cells += [f"<th>{escape(kind)}<br>Rooms</th><th>{escape(kind)}<br>Rate ({escape(currency)})</th>" for kind in room_types]
    return f"<tr>{''.join(cells)}</tr>"


def _night_row(day: date, room_types: list[str], rooms: dict, cell_for: CellFor) -> str:
    cells = [f"<td>{day:%a %d %b %Y}</td>"]
    for kind in room_types:
        cell = cell_for(day, kind, rooms.get((day, kind), 0))
        cells.append(f'<td align="right">{escape(cell.rooms_text)}</td>{_rate_cell(cell)}')
    return f"<tr>{''.join(cells)}</tr>"


def _rate_cell(cell: GridCell) -> str:
    match cell.state:
        case CellState.OPEN:
            return f'<td class="{RATE_CELL_CLASS}">{escape(cell.rate_text)}</td>'
        case CellState.FINAL:
            return f'<td class="{FINAL_CELL_CLASS}" contenteditable="false">{escape(cell.rate_text)}</td>'
        case CellState.NOT_NEEDED:
            return "<td></td>"


def _total_row(room_types: list[str], rooms: dict) -> str:
    cells = ["<td><b>Total room nights</b></td>"]
    for kind in room_types:
        total = sum(count for (_, room_type), count in rooms.items() if room_type == kind)
        cells.append(f'<td align="right"><b>{total}</b></td><td></td>')
    return f"<tr>{''.join(cells)}</tr>"
