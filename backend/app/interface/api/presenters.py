"""Domain objects to HTTP views. The only place that knows both shapes."""
from decimal import Decimal
from itertools import zip_longest

from app.application.activity import ActivityEvent
from app.domain.case import AWAITING_THE_DORM, Case, OutboundEmail
from app.domain.email_content import looks_like_html
from app.domain.hotel import Property
from app.domain.user import User
from app.domain.group_request import GroupRequest
from app.domain.hotel_reply import HotelReply
from app.domain.reconciliation import QuoteProblem, Reconciliation
from app.interface.api import schemas


def _money(value: Decimal | None) -> str | None:
    return None if value is None else f"{value:.2f}"


def _email(email: OutboundEmail) -> schemas.EmailView:
    return schemas.EmailView(**vars(email))


def _nights(request: GroupRequest) -> list[schemas.NightView]:
    return [
        schemas.NightView(
            date=day,
            weekday=f"{day:%A}",
            rooms={need.room_type: need.rooms for need in request.room_nights if need.day == day},
        )
        for day in request.nights
    ]


def _problem(problem: QuoteProblem) -> schemas.ProblemView:
    return schemas.ProblemView(
        kind=problem.kind,
        date=problem.day,
        room_type=problem.room_type,
        rooms_requested=problem.rooms_requested,
        rooms_offered=problem.rooms_offered,
        detail=problem.detail,
        dorm_total=_money(problem.dorm_total),
        computed_total=_money(problem.computed_total),
        rate=_money(problem.rate),
        minimum_rate=_money(problem.minimum_rate),
    )


def _quote(quote: Reconciliation, reply: HotelReply, rate_rules_applied: int) -> schemas.QuoteView:
    return schemas.QuoteView(
        currency=reply.currency,
        lines=[
            schemas.RateLineView(date=l.day, room_type=l.room_type, rooms=l.rooms, rate=_money(l.rate), amount=_money(l.amount))
            for l in quote.lines
        ],
        totals_by_type=[
            schemas.RoomTypeTotalView(room_type=t.room_type, room_nights=t.room_nights, revenue=_money(t.revenue))
            for t in quote.totals_by_type
        ],
        room_nights=quote.room_nights,
        revenue=_money(quote.revenue),
        problems=[_problem(p) for p in quote.problems],
        is_complete=quote.is_complete,
        rate_rules_applied=rate_rules_applied,
    )


def _terms(reply: HotelReply) -> schemas.TermsView:
    terms = reply.terms
    return schemas.TermsView(
        taxes=terms.taxes,
        commission=terms.commission,
        option_date=terms.option_date,
        attrition=terms.attrition,
        cancellation=terms.cancellation,
        extras=[f"{note.item}: {note.detail}" for note in terms.extras],
    )


def case_view(case: Case) -> schemas.CaseView:
    request, proposal = case.request, case.proposal
    return schemas.CaseView(
        id=case.id,
        status=case.status,
        created_at=case.created_at,
        source_email=case.source_email,
        agent_cost=f"{case.agent_cost:.4f}",  # Agent calls cost fractions of a cent.
        client=schemas.ClientView(**vars(request.client)) if request else None,
        event_name=request.event_name if request else None,
        arrival=request.arrival if request else None,
        departure=request.departure if request else None,
        nights=_nights(request) if request else [],
        requirements=list(request.requirements) if request else [],
        missing=[schemas.MissingView(**vars(item)) for item in request.missing] if request else [],
        notes=list(request.notes) if request else [],
        pending_email=_email(case.pending_email) if case.pending_email else None,
        sent_to_dorm=[_email(email) for email in case.sent_to_dorm],
        dorm_replies=list(case.dorm_reply_texts),
        dorm_replies_are_html=[looks_like_html(reply) for reply in case.dorm_reply_texts],
        quote=_quote(case.reconciliation, case.hotel_reply, len(case.rate_rules or ())) if case.reconciliation and case.hotel_reply else None,
        terms=_terms(case.hotel_reply) if case.hotel_reply else None,
        proposal=schemas.ProposalView(
            file_name=proposal.file_name,
            verification_problems=list(proposal.verification_problems),
            download_url=f"/api/v1/cases/{case.id}/proposal/file",
        )
        if proposal
        else None,
        handoff=schemas.HandoffView(**vars(case.handoff)) if case.handoff else None,
    )


def case_summary(case: Case) -> schemas.CaseSummaryView:
    client = case.request.client if case.request else None
    return schemas.CaseSummaryView(
        id=case.id,
        status=case.status,
        created_at=case.created_at,
        client_name=client.name if client else None,
        company=client.company if client else None,
        event_name=case.request.event_name if case.request else None,
        arrival=case.request.arrival if case.request else None,
    )


def activity_view(event: ActivityEvent) -> schemas.ActivityView:
    return schemas.ActivityView(
        source=event.source, label=event.label, state=event.state, key=event.key or event.label, at=event.at
    )


def user_view(user: User) -> schemas.UserView:
    return schemas.UserView(username=user.username, display_name=user.display_name, role=user.role)


def dorm_summary(case: Case) -> schemas.DormRequestSummaryView:
    request = case.request
    return schemas.DormRequestSummaryView(
        id=case.id,
        subject=case.sent_to_dorm[-1].subject,
        company=request.client.company if request else None,
        arrival=request.arrival if request else None,
        needs_reply=case.status in AWAITING_THE_DORM,
        received_at=case.created_at,
    )


def dorm_request(case: Case, hotel: Property) -> schemas.DormRequestView:
    """What the DORM may see: the conversation with the salesperson, and nothing from inside the desk."""
    request = case.request
    return schemas.DormRequestView(
        id=case.id,
        company=request.client.company if request else None,
        arrival=request.arrival if request else None,
        departure=request.departure if request else None,
        can_reply=case.status in AWAITING_THE_DORM,
        thread=_thread(case, hotel),
    )


def _thread(case: Case, hotel: Property) -> list[schemas.ThreadMessageView]:
    """Each email we sent is followed by the DORM's answer to it."""
    messages = []
    for sent, reply in zip_longest(case.sent_to_dorm, case.dorm_reply_texts):
        if sent:
            messages.append(
                schemas.ThreadMessageView(
                    sender="salesperson", sender_name=hotel.salesperson.name, subject=sent.subject, body_html=sent.body_html, body_text=None
                )
            )
        if reply:
            is_html = looks_like_html(reply)
            messages.append(
                schemas.ThreadMessageView(
                    sender="dorm",
                    sender_name=hotel.dorm.name,
                    subject=None,
                    body_html=reply if is_html else None,
                    body_text=None if is_html else reply,
                )
            )
    return messages
