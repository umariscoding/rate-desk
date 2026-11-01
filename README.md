# Rate Desk

Group sales for a hotel, run by agents. A salesperson pastes a client's email. Cominty agents read it, ask the
hotel's Director of Revenue Management (the DORM) for rates, check the reply, chase what is wrong, and build the proposal.
The salesperson approves the first rate request; corrections go out on their own.

Built for the Cominty Agent-Native Product Challenge. All agent work runs on Cominty (Python SDK, managed agents,
streamed activity, per-message tool scoping, cost tracking). The demo property is fictional.

## The flow

| Step | Who | What happens |
| - | - | - |
| 1 | Salesperson | Pastes the client's email |
| 2 | Intake agent | Extracts client, dates, room types and counts per night. Asks only for real blockers |
| 3 | Code | Fills a fixed rate-request email with the parsed dates, rooms and requirements, and renders the rate grid |
| 4 | DORM | Clicks Reply all on the email. The grid opens editable with the rate cells highlighted; they type their rates and notes and send |
| 5 | Rate Reader and Rate Guard agents + code | The Reader extracts rates and terms. The Guard reads the hotel's rate rules (minimum rates per room type and night) from the Cominty knowledge base. Code does the maths: missing or short cells, wrong totals, and any rate below a hotel minimum. If something is wrong, the DORM is sent **one correction email automatically** (no approval): a checklist of exactly what is wrong, plus the grid with their rates pre-filled and only the open cells highlighted. Their single reply closes it |
| 6 | Code, then Cover Email agent | Code fills the placeholders of the DOCX proposal template from the confirmed quote and checks that every name, date and rate is in the file. The agent then writes the cover email the salesperson sends to the client |

Design rule: agents read and write free text; plain code does everything that must be exact (emails to the DORM,
grids, money, completeness, rate-rule checks, the document). Four agents: Intake reads the client's email, Rate Reader
reads the DORM's reply, Rate Guard reads the hotel's policy from the knowledge base, Cover Email writes the client email. An early test showed a
model adding up a rate grid three different ways and getting it wrong each time.

## Who sees what

Sign in as one of two demo accounts (password `ratedesk`). Each role gets its own inbox, and the server enforces it.

| Account | Role | Sees |
| - | - | - |
| `umar` (Umar Azhar) | Salesperson | Inbox of requests with a plain "next step" for each, new request form, the full case record with agent activity |
| `dorm` (DORM A) | DORM (Director of Revenue Management) | Inbox of rate requests sent to them, each as a conversation with the sales desk, and a reply box. Nothing from inside the desk: no agent costs, no rate checks |

Sign-in here is a demo: fixed accounts, one shared password, signed session tokens. It separates roles; it is not production auth.

## Run it

```bash
# Backend (Python 3.11+)
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env            # add your Cominty API key and user id
.venv/bin/uvicorn app.main:app --port 8000

# Frontend (Node 20+), in a second terminal
cd frontend
npm install && npm run dev      # http://localhost:5173
```

Cost per case: under €0.01 for all four agents together. The emails to the DORM and the proposal cost nothing.

Agents default to Cominty's built-in Chat agent. To use your own, create them on platform.cominty.ai and set
`AGENT_INTAKE`, `AGENT_RATE_REPLY`, `AGENT_RATE_GUARD` and `AGENT_HANDOFF` in `backend/.env`. The Rate Guard needs the
documents capability and a source containing `backend/knowledge/hotel_a_group_sales_policy.pdf`.

## How to test

1. Sign in as `umar`. Open **New request**, click **Complete request**, then **Read email**. Approve and send the rate request.
2. Sign out, sign in as `dorm`. Open the request, click **Reply all**, click **Fill in a messy reply**, then **Send reply**.
   The correction email arrives on its own. It lists what is missing, the short Deluxe King night, and the Standard
   King Friday rate that is below the hotel's weekend minimum.
3. Click **Reply all** again, **Fill in a clean reply**, **Send reply**.
4. Sign in as `umar`. The rates are confirmed. Click **Build the proposal**: download it and read the cover email.

Or run all of it in a real browser with `cd frontend && npm run e2e`.

## Testing without spending credit

`AGENT_MODE=record` saves each real agent answer once and reuses it; `AGENT_MODE=replay` never calls Cominty. The same
input always gets the same recorded answer, so the sample buttons in the app work for free after one recorded run.
Delete `backend/var/agent_fixtures/` to record again (for example after changing a prompt).

```bash
cd backend && AGENT_MODE=replay .venv/bin/uvicorn app.main:app --port 8000
cd frontend && npm run dev          # in another terminal
cd frontend && npm run e2e          # walks all 19 steps in Chrome: both logins, correction email, proposal download
```

## Architecture

Dependencies point inward. The domain imports nothing from the frameworks.

```
backend/app/
  domain/          Case aggregate and its state machine, reconciliation rules, typed errors
  application/     Use cases and the ports (interfaces) they need. Orchestration only
  infrastructure/  Cominty adapters and prompts, email templates, proposal template filler, JSON case store, rate-grid renderer
  interface/api/   FastAPI routers, schemas, presenters, error mapping
  container.py     Composition root: the only place that knows the concrete classes
frontend/src/      Vite + React + TypeScript: api/, hooks/, features/, components/
```

Decisions worth knowing:

- **The browser chooses the case id** and opens the live activity stream (server-sent events) before posting.
  Each request runs to completion and returns the finished case, so there is no job queue.
- **Agent output is validated** with Pydantic before it touches a case. Malformed JSON fails loudly as a 502.
- **Prompts are Markdown files** in `infrastructure/cominty/prompts/`. To use a custom agent created on
  platform.cominty.ai, set `AGENT_INTAKE` or `AGENT_RATE_REPLY` to its id.
- **Persistence** is one JSON file per case under `backend/var/` and the activity feed is in memory. Both sit behind
  ports (`CaseRepository`, `ActivityFeed`), so a database or Cominty memory can replace them without touching use cases.
  Because of this the API needs a long-running host, not a serverless one.
