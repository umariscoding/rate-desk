"""The two emails to the DORM are fixed wording. Only the facts change, and they come from the parsed request."""
from datetime import date, timedelta
from decimal import Decimal
from html import escape

from app.application.activity import ActivityHandler
from app.application.ports import Costed
from app.domain.case import OutboundEmail
from app.domain.group_request import GroupRequest
from app.domain.hotel import Contact, Property
from app.domain.reconciliation import Reconciliation
from app.infrastructure.rendering.correction_checklist import render_checklist
from app.infrastructure.rendering.rate_grid import render_correction_grid, render_rate_grid

FREE_OF_CHARGE = Decimal(0)
ASKS_OF_THE_DORM = ("the currency", "whether the rates include taxes", "commission", "the option (cut-off) date")


def _greeting_name(contact: Contact) -> str:
    return escape(contact.name)


def _sign_off(salesperson: Contact) -> str:
    return f"<p>Kind regards,<br>{escape(salesperson.name)}<br>{escape(salesperson.title)}</p>"


def _stay(request: GroupRequest) -> tuple[date, date]:
    nights = request.nights
    return request.arrival or nights[0], request.departure or nights[-1] + timedelta(days=1)


class TemplateRateRequestWriter:
    def __init__(self, hotel: Property) -> None:
        self._hotel = hotel

    async def write(self, request: GroupRequest, on_activity: ActivityHandler) -> Costed[OutboundEmail]:
        arrival, departure = _stay(request)
        company = escape(request.client.company or request.client.name or "a client")
        subject = f"Group rate request: {request.client.company or 'new group'}, {arrival:%d %b} to {departure:%d %b %Y}"
        intro = (
            f"<p>Dear {_greeting_name(self._hotel.dorm)},</p>"
            f"<p>We have a group request from <b>{company}</b>, arriving {arrival:%A %d %B %Y} and departing "
            f"{departure:%A %d %B %Y}. Please send your rate for each room type and night. Use <b>Reply all</b> "
            "and fill in the yellow cells of the grid below.</p>"
        )
        body = f"{intro}{render_rate_grid(request, self._hotel)}{self._requirements(request)}{self._closing()}"
        return Costed(OutboundEmail(self._hotel.dorm.name, self._hotel.dorm.email, subject, body), FREE_OF_CHARGE)

    @staticmethod
    def _requirements(request: GroupRequest) -> str:
        if not request.requirements:
            return ""
        items = "".join(f"<li>{escape(item)}</li>" for item in request.requirements)
        return f"<p>The client has also asked for the following. Please confirm availability and price:</p><ul>{items}</ul>"

    def _closing(self) -> str:
        asks = ", ".join(ASKS_OF_THE_DORM[:-1]) + f" and {ASKS_OF_THE_DORM[-1]}"
        return f"<p>Please also tell us {asks}.</p><p>Thank you.</p>{_sign_off(self._hotel.salesperson)}"


class TemplateFollowupWriter:
    """One correction email: what is missing, then the grid again with the rates already given filled in."""

    def __init__(self, hotel: Property) -> None:
        self._hotel = hotel

    async def write(
        self, request: GroupRequest, quote: Reconciliation, on_activity: ActivityHandler
    ) -> Costed[OutboundEmail]:
        subject = "Rate request: a few details still needed"
        intro = (
            f"<p>Dear {_greeting_name(self._hotel.dorm)},</p>"
            "<p>Thank you for the rates. A few details are still needed before we can build the proposal. "
            "Please use <b>Reply all</b> and fill in the highlighted cells of the grid below.</p>"
        )
        grid = render_correction_grid(request, self._hotel, quote)
        checklist = render_checklist(quote.problems, self._hotel.currency)
        body = f"{intro}{checklist}{grid}<p>Thank you.</p>{_sign_off(self._hotel.salesperson)}"
        return Costed(OutboundEmail(self._hotel.dorm.name, self._hotel.dorm.email, subject, body), FREE_OF_CHARGE)
