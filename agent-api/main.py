"""Warranty Vault agent API.

React UI  →  this service (AI agent + MCP client)  →  FastMCP server (Streamable HTTP)  →  SQLite
"""
import os
import time
import uuid

import mcp_bridge  # loads .env first
import llm_agent
import rule_agent
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Warranty Vault Agent API")

cors_origins_env = os.getenv("CORS_ORIGINS", "*").strip()
cors_origins = ["*"] if cors_origins_env == "*" else [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, dict] = {}
MAX_SESSIONS, MAX_HISTORY = 200, 12


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str | None = None
    # 'online'  -> always try LLM (returns error if not configured)
    # 'offline' -> always use rule agent
    # None      -> auto-fallback (current default behaviour)
    force_mode: str | None = None


class DraftIn(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=5000)


class ClaimCreateIn(BaseModel):
    purchase_id: int | None = None
    product_name: str | None = None
    issue_description: str | None = None


def _session(sid: str | None) -> tuple[str, dict]:
    sid = sid or uuid.uuid4().hex
    if sid not in SESSIONS:
        if len(SESSIONS) >= MAX_SESSIONS:
            SESSIONS.pop(next(iter(SESSIONS)))
        SESSIONS[sid] = {"history": [], "pending": None, "ts": time.time()}
    return sid, SESSIONS[sid]


@app.get("/api/health")
async def health():
    return {"mcp_connected": await mcp_bridge.ping(),
            "mode": "ai" if llm_agent.configured() else "offline",
            "model": llm_agent.LLM_MODEL if llm_agent.configured() else None}


@app.post("/api/chat")
async def chat(body: ChatIn):
    sid, session = _session(body.session_id)
    mode, note = "offline", None
    if not await mcp_bridge.ping():
        return {"session_id": sid, "mode": mode, "events": [], "error": True,
                "reply": "I can't reach the Warranty Vault MCP server, so I can't save or look up anything yet."}

    reply, events = None, []
    fm = (body.force_mode or "").lower()

    # ── ONLINE mode (force LLM) ──────────────────────────────────────────────
    if fm == "online":
        if not llm_agent.configured():
            return {
                "session_id": sid, "mode": "offline", "events": [], "error": True,
                "reply": (
                    "Online mode requires an LLM API key. "
                    "Please set LLM_BASE_URL, LLM_MODEL, and LLM_API_KEY in the .env file and restart the server. "
                    "See .env.example for free provider options (Groq, Gemini, OpenRouter)."
                ),
            }
        try:
            reply, events = await llm_agent.run(session["history"], body.message)
            mode = "ai"
        except llm_agent.LLMError as e:
            # Surface the LLM error clearly — do NOT silently fall back in forced-online mode
            return {
                "session_id": sid, "mode": "offline", "events": [], "error": True,
                "reply": f"Online AI error: {e}. Switch to Offline mode or check your API key.",
            }

    # ── OFFLINE mode (force rule agent) ─────────────────────────────────────
    elif fm == "offline":
        reply, events = await rule_agent.handle(session, body.message)
        mode = "offline"

    # ── AUTO mode (original fallback behaviour) ──────────────────────────────
    else:
        if llm_agent.configured():
            try:
                reply, events = await llm_agent.run(session["history"], body.message)
                mode = "ai"
            except llm_agent.LLMError as e:
                note = str(e)  # fall back so the demo keeps working
        if reply is None:
            reply, events = await rule_agent.handle(session, body.message)
            if note:
                reply = "(AI model unavailable, using offline mode.) " + reply

    session["history"] += [{"role": "user", "content": body.message},
                           {"role": "assistant", "content": reply}]
    session["history"] = session["history"][-MAX_HISTORY:]
    return {"session_id": sid, "reply": reply, "events": events, "mode": mode, "warning": note}


async def _tool(name: str, args: dict | None = None) -> dict:
    try:
        return await mcp_bridge.call_tool(name, args)
    except Exception as e:
        raise HTTPException(502, f"MCP server unavailable: {e}")


@app.get("/api/dashboard")
async def dashboard():
    return await _tool("dashboard_summary")


@app.put("/api/claims/{claim_id}")
async def save_claim(claim_id: int, body: DraftIn):
    result = await _tool("save_claim_draft", {"claim_id": claim_id, "subject": body.subject, "body": body.body})
    if not result.get("ok"):
        raise HTTPException(400, result.get("message", "Could not save draft"))
    return result


@app.post("/api/claims/draft")
async def create_claim_draft(body: ClaimCreateIn):
    args = {}
    if body.purchase_id is not None:
        args["purchase_id"] = body.purchase_id
    if body.product_name:
        args["product_name"] = body.product_name
    args["issue_description"] = body.issue_description or "Device stopped working properly; requesting warranty repair or replacement under warranty terms."
    result = await _tool("draft_claim", args)
    if not result.get("ok"):
        raise HTTPException(400, result.get("message", "Could not draft claim"))
    return result


@app.delete("/api/purchases/{purchase_id}")
async def remove_purchase(purchase_id: int):
    return await _tool("delete_purchase", {"purchase_id": purchase_id})


@app.post("/api/demo/seed")
async def seed():
    return await _tool("seed_demo_data")


@app.get("/api/products")
async def products():
    """Return a lightweight list of all saved products with name, purchase date and expiry.
    Used by the offline assistant to answer expiry questions when the MCP tool call alone
    would not return useful results (e.g. fuzzy product-name matching).
    """
    summary = await _tool("dashboard_summary")
    items = [
        {
            "id": p["id"],
            "product_name": p["product_name"],
            "brand": p.get("brand"),
            "purchase_date": p.get("purchase_date"),
            "warranty_expiry_date": p.get("warranty_expiry_date"),
            "status": p.get("status"),
            "days_remaining": p.get("days_remaining"),
        }
        for p in summary.get("purchases", [])
    ]
    return {"ok": True, "products": items}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
