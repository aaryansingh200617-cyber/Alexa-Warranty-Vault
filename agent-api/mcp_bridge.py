"""MCP client adapter. The browser never talks to the MCP server directly: this
service opens MCP sessions over Streamable HTTP and invokes tools on its behalf."""
import json
import os
from pathlib import Path

from fastmcp import Client

CORE_TOOLS = {"log_purchase", "check_warranty", "expiring_soon", "draft_claim"}


def load_env() -> None:
    """Tiny .env loader (no extra dependency). Real environment variables win."""
    for path in (Path(__file__).parent / ".env", Path(__file__).parent.parent / ".env"):
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8765/mcp")
MCP_TOKEN = os.getenv("MCP_AUTH_TOKEN", "").strip() or None


def _client() -> Client:
    return Client(MCP_URL, auth=MCP_TOKEN)


def _unwrap(result) -> dict:
    data = getattr(result, "structured_content", None)
    if isinstance(data, dict):
        return data.get("result", data) if set(data) == {"result"} and isinstance(data["result"], dict) else data
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"ok": False, "error": "bad_response", "message": text}
    return {"ok": False, "error": "empty_response", "message": "The tool returned nothing."}


async def call_tool(name: str, arguments: dict | None = None) -> dict:
    async with _client() as c:
        return _unwrap(await c.call_tool(name, arguments or {}, raise_on_error=False))


async def list_core_tools() -> list[dict]:
    """Discover tools from the server and return them in OpenAI function-calling format."""
    async with _client() as c:
        tools = await c.list_tools()
    return [{"type": "function", "function": {
        "name": t.name, "description": t.description or "", "parameters": getattr(t, "input_schema", None) or t.inputSchema}}
        for t in tools if t.name in CORE_TOOLS]


async def ping() -> bool:
    try:
        async with _client() as c:  # entering the context performs the MCP handshake
            await c.list_tools()
        return True
    except Exception:
        return False
