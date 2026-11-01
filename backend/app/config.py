from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infrastructure.cominty.fixture_agent_runner import AgentMode

BACKEND_ROOT = Path(__file__).resolve().parent.parent
CHAT_AGENT = "__cominty_agents::agent.chat"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_ROOT / ".env", extra="ignore")

    cominty_api_key: str
    cominty_user_id: str
    cominty_base_url: str = "https://ds.cominty.com"

    # Two agents read free text (the client's email, the DORM's reply) and a third writes the cover email.
    # Everything else is templates and code.
    # Point either at a custom agent created on platform.cominty.ai without touching code.
    agent_intake: str = CHAT_AGENT
    agent_rate_reply: str = CHAT_AGENT
    # The Rate Guard reads the hotel's rate rules from the knowledge base. It needs the documents capability.
    agent_rate_guard: str = CHAT_AGENT
    # The third agent runs once a proposal is built: it writes the client's cover email.
    agent_handoff: str = CHAT_AGENT

    # Demo sign-in. The secret defaults to a value derived from the Cominty key, so sessions survive a restart.
    demo_password: str = "ratedesk"
    session_secret: str | None = None
    session_hours: int = 12

    # "record" saves each real agent answer, "replay" reuses them without calling Cominty. See fixture_agent_runner.py.
    agent_mode: AgentMode = AgentMode.LIVE
    fixtures_dir: Path = Field(default=BACKEND_ROOT / "var" / "agent_fixtures")

    data_dir: Path = Field(default=BACKEND_ROOT / "var")
    proposal_template: Path = Field(default=BACKEND_ROOT / "templates" / "proposal_template.docx")
    allowed_origins: list[str] = ["http://localhost:5173"]
    # The built frontend, served by this same server when it exists (a deployment). In development Vite serves it.
    frontend_dir: Path | None = Field(default=BACKEND_ROOT.parent / "frontend" / "dist")
