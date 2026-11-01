"""The list of exactly what we still need from the DORM, one plain sentence per problem."""
from collections.abc import Sequence
from html import escape

from app.domain.reconciliation import QuoteProblem, ProblemKind

LEGEND = (
    '<p>In the grid below, the <b>yellow cells need your input</b>. Green cells are rates you already gave, '
    "so you can leave them as they are.</p>"
)


DESK_NOTE_CLASS = "desk-note"  # Text from our desk. When the DORM replies, it is quoted back and must be ignored.


def render_checklist(problems: Sequence[QuoteProblem], currency: str) -> str:
    items = "".join(f"<li>{_sentence(problem, currency)}</li>" for problem in problems)
    return f'<div class="{DESK_NOTE_CLASS}"><p><b>What we still need from you</b></p><ul>{items}</ul>{LEGEND}</div>'


def _sentence(problem: QuoteProblem, currency: str) -> str:
    where = f"<b>{problem.day:%a %d %b} · {escape(problem.room_type or '')}</b>: " if problem.day else ""
    match problem.kind:
        case ProblemKind.MISSING_RATE:
            return f"{where}no rate given for {problem.rooms_requested} rooms. Please enter it in the grid."
        case ProblemKind.SHORT_INVENTORY:
            return (
                f"{where}we need {problem.rooms_requested} rooms and you offered {problem.rooms_offered}. "
                f"Please confirm you can release all {problem.rooms_requested}, or tell us how many you can give."
            )
        case ProblemKind.TOTAL_MISMATCH:
            return (
                f"<b>{escape(problem.room_type or 'Total')}</b>: you wrote {currency} {problem.dorm_total:,.2f}, "
                f"but the rates you gave add up to {currency} {problem.computed_total:,.2f}. "
                "Please confirm or correct the rates in the grid."
            )
        case ProblemKind.BELOW_MINIMUM_RATE:
            return (
                f"{where}{currency} {problem.rate:,.2f} is below our minimum rate of {currency} "
                f"{problem.minimum_rate:,.2f} for this night. Please confirm or correct the rate in the grid."
            )
        case ProblemKind.UNCLEAR_IN_REPLY:
            return escape(problem.detail or "Part of your reply was unclear. Please clarify it.")
