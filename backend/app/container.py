"""Composition root: the one place that knows every concrete class and wires them to the ports."""
import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from cominty_sdk import AsyncCominty

from app.application.activity import ActivityFeed, ActivitySource
from app.application.use_cases.generate_proposal import GenerateProposal
from app.application.ports import SessionTokens
from app.application.use_cases.log_in import LogIn
from app.application.use_cases.queries import GetCase, GetDormRequest, GetProposalFile, ListCases, ListDormRequests
from app.application.use_cases.send_pending_email import SendPendingEmail
from app.application.use_cases.submit_client_email import SubmitClientEmail
from app.application.use_cases.submit_hotel_reply import SubmitHotelReply
from app.config import Settings
from app.infrastructure.cominty.agent_runner import AgentRunner, CominyAgentRunner
from app.infrastructure.cominty.fixture_agent_runner import AgentMode, FixtureAgentRunner
from app.infrastructure.cominty.handoff_writer import CominyProposalHandoff
from app.infrastructure.cominty.prompt_library import PromptLibrary
from app.infrastructure.cominty.rate_reply_reader import CominyRateReplyReader
from app.infrastructure.cominty.rate_rule_reader import CominyRateRuleReader
from app.infrastructure.cominty.request_extractor import CominyRequestExtractor
from app.domain.hotel import Property
from app.infrastructure.demo_property import DEMO_PROPERTY
from app.infrastructure.demo_users import DEMO_USERS
from app.infrastructure.documents.local_document_store import LocalDocumentStore
from app.infrastructure.documents.template_proposal_composer import TemplateProposalComposer
from app.infrastructure.emails.template_email_writers import TemplateFollowupWriter, TemplateRateRequestWriter
from app.infrastructure.persistence.in_memory_activity_feed import InMemoryActivityFeed
from app.infrastructure.persistence.json_case_repository import JsonCaseRepository
from app.infrastructure.security.demo_user_directory import DemoUserDirectory
from app.infrastructure.security.signed_session_tokens import SignedSessionTokens


@dataclass(frozen=True)
class Container:
    submit_client_email: SubmitClientEmail
    send_pending_email: SendPendingEmail
    submit_hotel_reply: SubmitHotelReply
    generate_proposal: GenerateProposal
    get_case: GetCase
    list_cases: ListCases
    get_proposal_file: GetProposalFile
    list_dorm_requests: ListDormRequests
    get_dorm_request: GetDormRequest
    log_in: LogIn
    session_tokens: SessionTokens
    feed: ActivityFeed
    hotel: Property


def create_cominty_client(settings: Settings) -> AsyncCominty:
    return AsyncCominty(
        api_token=settings.cominty_api_key, user_id=settings.cominty_user_id, base_url=settings.cominty_base_url
    )


def build_container(settings: Settings, client: AsyncCominty) -> Container:
    hotel = DEMO_PROPERTY
    today = date.today
    prompts = PromptLibrary(hotel, today)
    live_runner = CominyAgentRunner(
        client,
        {
            ActivitySource.INTAKE: settings.agent_intake,
            ActivitySource.RATE_REPLY: settings.agent_rate_reply,
            ActivitySource.RATE_GUARD: settings.agent_rate_guard,
            ActivitySource.HANDOFF: settings.agent_handoff,
        },
    )
    runner: AgentRunner = live_runner
    if settings.agent_mode is not AgentMode.LIVE:
        runner = FixtureAgentRunner(live_runner, settings.fixtures_dir, settings.agent_mode)
    cases = JsonCaseRepository(settings.data_dir / "cases")
    documents = LocalDocumentStore(settings.data_dir / "documents")
    feed = InMemoryActivityFeed()
    composer = TemplateProposalComposer(hotel, settings.proposal_template, today)
    secret = settings.session_secret or hashlib.sha256(f"rate-desk:{settings.cominty_api_key}".encode()).hexdigest()
    tokens = SignedSessionTokens(secret, timedelta(hours=settings.session_hours), lambda: datetime.now(UTC))
    return Container(
        submit_client_email=SubmitClientEmail(
            CominyRequestExtractor(runner, prompts),
            TemplateRateRequestWriter(hotel),
            cases,
            feed,
            lambda: datetime.now(UTC),
        ),
        send_pending_email=SendPendingEmail(cases, feed),
        submit_hotel_reply=SubmitHotelReply(
            CominyRateReplyReader(runner, prompts, hotel),
            CominyRateRuleReader(runner, prompts, hotel),
            TemplateFollowupWriter(hotel),
            cases,
            feed,
        ),
        generate_proposal=GenerateProposal(composer, CominyProposalHandoff(runner, prompts, hotel), documents, cases, feed),
        get_case=GetCase(cases),
        list_cases=ListCases(cases),
        get_proposal_file=GetProposalFile(cases, documents),
        list_dorm_requests=ListDormRequests(cases),
        get_dorm_request=GetDormRequest(cases),
        log_in=LogIn(DemoUserDirectory(DEMO_USERS, settings.demo_password), tokens),
        session_tokens=tokens,
        feed=feed,
        hotel=hotel,
    )
