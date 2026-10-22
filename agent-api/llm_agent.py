"""LLM tool-calling loop over any OpenAI-compatible chat API.

Works with Groq, Google Gemini (OpenAI-compat endpoint), OpenRouter, Ollama, etc.
Configure with LLM_BASE_URL / LLM_API_KEY / LLM_MODEL.
"""
import json
import os
from datetime import date

import httpx

import mcp_bridge

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
MAX_STEPS = 5

TOOL_LABELS = {
    "log_purchase": "Saving your purchase…",
    "check_warranty": "Checking warranty dates…",
    "expiring_soon": "Looking for expiring warranties…",
    "draft_claim": "Preparing your claim…",
}


class LLMError(Exception):
    pass


def configured() -> bool:
    if not (LLM_BASE_URL and LLM_MODEL):
        return False
    local = "localhost" in LLM_BASE_URL or "127.0.0.1" in LLM_BASE_URL
    return bool(LLM_API_KEY) or local


def system_prompt() -> str:
    return (
        "You are Warranty Vault, a concise, friendly voice-first warranty assistant. "
        f"Today's date is {date.today().isoformat()}. Use tools for every warranty action.\n"
        "Rules:\n"
        "- Use log_purchase when the user bought something, check_warranty to answer coverage questions, "
        "expiring_soon for upcoming expiries, draft_claim to prepare a claim email.\n"
        "- NEVER invent a purchase, price, date, warranty length or expiry date. If a required detail is "
        "missing, ask ONE short follow-up question instead of calling the tool.\n"
        "- Convert relative dates ('yesterday') to YYYY-MM-DD using today's date. Convert '2 years' to 24 months.\n"
        "- Only report what tool results say. Expiry dates and statuses come from the tool, not from you.\n"
        "- Status is calculated from saved dates; it is not a guarantee the manufacturer will approve a claim.\n"
        "- Never claim an email was sent; claims are drafts for the user to review.\n"
        "- Keep replies to 1–3 short sentences. They may be read aloud, so avoid markdown and long lists."
    )


async def _chat(messages: list[dict], tools: list[dict]) -> dict:
    headers = {"Content-Type": "application/json", "User-Agent": "WarrantyVault/1.0"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    payload = {"model": LLM_MODEL, "messages": messages, "tools": tools,
               "tool_choice": "auto", "temperature": 0.2}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{LLM_BASE_URL}/chat/completions", headers=headers, json=payload)
    except httpx.HTTPError as e:
        raise LLMError(f"Could not reach the language model: {e}") from e
    if r.status_code != 200:
        if r.status_code == 401:
            raise LLMError("API key authentication failed (401). Please check your LLM_API_KEY environment variable or switch to Offline mode.")
        raise LLMError(f"Language model error {r.status_code}: {r.text[:200]}")
    try:
        return r.json()["choices"][0]["message"]
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError("Unexpected response from the language model.") from e


async def run(history: list[dict], user_text: str) -> tuple[str, list[dict]]:
    """Returns (assistant_reply, tool_events)."""
    tools = await mcp_bridge.list_core_tools()
    messages = [{"role": "system", "content": system_prompt()}, *history,
                {"role": "user", "content": user_text}]
    events: list[dict] = []

    for _ in range(MAX_STEPS):
        msg = await _chat(messages, tools)
        calls = msg.get("tool_calls") or []
        if not calls:
            return (msg.get("content") or "").strip() or "Sorry, I didn't catch that.", events
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if name not in mcp_bridge.CORE_TOOLS:
                result = {"ok": False, "error": "unknown_tool", "message": f"No tool named {name}."}
            else:
                try:
                    result = await mcp_bridge.call_tool(name, args)
                except Exception as e:  # MCP/transport failure: surface it, never fake success
                    result = {"ok": False, "error": "tool_failed", "message": f"Tool failed: {e}"}
            events.append({"name": name, "label": TOOL_LABELS.get(name, name), "arguments": args,
                           "ok": bool(result.get("ok")), "result": result})
            messages.append({"role": "tool", "tool_call_id": call.get("id", name),
                             "content": json.dumps(result)[:6000]})
    return "I'm having trouble finishing that. Could you rephrase?", events
