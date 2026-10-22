# Warranty Vault for Alexa +
**Every purchase remembered. Every warranty protected.**
A voice-first AI warranty assistant built on an MCP server (Python · FastMCP · Streamable HTTP · SQLite) with a React + Tailwind web app that simulates an Alexa+ style experience. Amazon-inspired design; not an official Amazon or Alexa product.

```
React UI ──► Agent API (FastAPI: LLM tool-calling + MCP client) ──Streamable HTTP──► FastMCP server ──► SQLite
```

The browser never talks to the MCP server directly. The agent API opens MCP sessions, lets the model choose tools, and returns results to the chat and dashboard. The database is the source of truth: expiry dates and statuses are calculated in code, never by the model.

## Quick start (works with no API key)
Requirements: Python 3.10+, Node 18+.

```bash
./setup.sh      # creates .venv, installs Python + npm deps, copies .env.example to .env
./start.sh      # MCP server :8765, agent API :8000, web app :5173
```
Open http://localhost:5173 and click **Load sample data** (or just talk to it).
Windows: create the venv and install manually (see header of `start.bat`), then run `start.bat`.

Manual start, three terminals:
```bash
cd mcp-server && python server.py        # http://127.0.0.1:8765/mcp
cd agent-api  && python main.py          # http://127.0.0.1:8000
cd web-app    && npm run dev             # http://localhost:5173
```

## Two assistant modes
| Mode | When | Notes |
|---|---|---|
| **AI** | `LLM_BASE_URL`, `LLM_MODEL` (+ `LLM_API_KEY`) set in `.env` | Any OpenAI-compatible API with tool calling. Real intent detection and tool selection. |
| **Offline** | nothing set, or the AI call fails | Built-in keyword + slot-filling assistant. Still calls the real MCP tools. Good for demos without internet or keys. |

The header badge shows which mode is active. See `.env.example` for free provider settings.

## MCP tools
| Tool | Purpose |
|---|---|
| `log_purchase` | Validate and save a purchase; calculates expiry (calendar-safe). Asks for missing date/duration instead of guessing. |
| `check_warranty` | Find a purchase and return active / expiring_soon / expired / unknown. Handles duplicates and not-found. |
| `expiring_soon` | Warranties expiring within `within_days` (default 30). |
| `draft_claim` | Builds a claim email from saved data and the user's issue; stored as a draft, never sent. |

Four more tools (`dashboard_summary`, `save_claim_draft`, `delete_purchase`, `seed_demo_data`) exist for the UI and are **not** exposed to the language model.

## Security notes
- Parameterized SQL everywhere; `PRAGMA foreign_keys = ON`; inputs validated server-side.
- The MCP server binds to `127.0.0.1`. It refuses to bind a public address unless `MCP_AUTH_TOKEN` is set, which enables bearer-token auth. Put HTTPS in front for any remote deployment.
- `warranty.db` and `.env` are git-ignored. Use only synthetic data in public demos.
- Single demo user (`WARRANTY_USER_ID`, default `demo`). Add real authentication before storing real people's data.
- Claim drafts require user review; no email is ever sent.

## Tests
```bash
python tests/test_tools.py
```

## Project layout
```
mcp-server/  server.py (FastMCP) · tools.py · database.py
agent-api/   main.py (FastAPI) · llm_agent.py · rule_agent.py · mcp_bridge.py
web-app/     React + Vite + Tailwind (chat, dashboard, claim panel, voice)
tests/       tool tests
```

## Voice
Uses the browser Web Speech API (best in Chrome/Edge/Safari). If unsupported or the microphone is blocked, the mic button hides or explains, and typing always works. Spoken replies can be muted or stopped.

## Free LLM options
Set one block from `.env.example`. Free tiers and model names change, so confirm current limits and model IDs on each provider's site.
- **Groq**: free tier, OpenAI-compatible, fast.
- **Google Gemini (AI Studio)**: free tier with an OpenAI-compatible endpoint.
- **OpenRouter**: has models ending in `:free`.
- **Ollama**: runs locally, no key, no limits. Pull a tool-capable model (e.g. `ollama pull llama3.1`).
- **No key at all**: leave `LLM_*` empty and use the offline assistant.

## License
This project is open source and available under the [MIT License](LICENSE).
