"""Warranty Vault MCP server (FastMCP, Streamable HTTP, SQLite).

Run:  python server.py
Endpoint: http://127.0.0.1:8765/mcp
"""
import json
import os
from typing import Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

import tools
from database import init_db

mcp = FastMCP(
    name="warranty-vault",
    instructions=(
        "Warranty management tools. The database is the source of truth: never invent purchases "
        "or expiry dates. Dates use YYYY-MM-DD. If a tool returns `needs`, ask the user for those fields."
    ),
)

USER_ID = os.getenv("WARRANTY_USER_ID", "demo")  # single-user demo; swap for real auth later


# ----------------------------- Core tools (offered to the AI) ----------------------------- #
@mcp.tool
def log_purchase(
    product_name: Annotated[str, Field(description="Product name, e.g. 'Dishwasher'")],
    purchase_date: Annotated[Optional[str], Field(description="Purchase date, YYYY-MM-DD. Ask the user if unknown.")] = None,
    warranty_duration_months: Annotated[Optional[int], Field(description="Warranty length in months (2 years = 24). Ask if unknown.")] = None,
    purchase_price: Annotated[Optional[float], Field(description="Price paid, non-negative")] = None,
    currency: Annotated[str, Field(description="ISO 4217 currency code, e.g. USD, INR, EUR")] = "USD",
    brand: Optional[str] = None,
    category: Optional[str] = None,
    receipt_path: Annotated[Optional[str], Field(description="Optional receipt reference")] = None,
    notes: Optional[str] = None,
) -> dict:
    """Save a new purchase and its warranty terms. Returns the saved record with a calculated expiry date."""
    return tools.log_purchase(product_name, purchase_date, warranty_duration_months, purchase_price,
                              currency, brand, category, receipt_path, notes, user_id=USER_ID)


@mcp.tool
def check_warranty(
    product_name: Annotated[str, Field(description="Product to look up, e.g. 'fridge' or 'Dishwasher'")],
) -> dict:
    """Look up a saved purchase and calculate whether its warranty is active, expiring soon, expired or unknown."""
    return tools.check_warranty(product_name, user_id=USER_ID)


@mcp.tool
def expiring_soon(
    within_days: Annotated[int, Field(description="Look-ahead window in days", ge=1, le=3650)] = 30,
) -> dict:
    """List saved warranties that expire within the next N days (default 30)."""
    return tools.expiring_soon(within_days, user_id=USER_ID)


@mcp.tool
def draft_claim(
    product_name: Annotated[str, Field(description="Product the claim is for")],
    issue_description: Annotated[Optional[str], Field(description="What is wrong with the product. Ask if unknown.")] = None,
    customer_name: Optional[str] = None,
    purchase_id: Annotated[Optional[int], Field(description="Use to disambiguate when several items match")] = None,
) -> dict:
    """Prepare a warranty-claim email draft from the saved purchase and the user's problem description. Never sends anything."""
    return tools.draft_claim(product_name, issue_description, customer_name, purchase_id, user_id=USER_ID)


# ----------------------------- UI-support tools (not offered to the AI) ----------------------------- #
@mcp.tool(tags={"ui"})
def dashboard_summary() -> dict:
    """UI only: counts, purchases, expiring items and claim drafts for the dashboard."""
    return tools.dashboard_summary(user_id=USER_ID)


@mcp.tool(tags={"ui"})
def save_claim_draft(claim_id: int, subject: str, body: str) -> dict:
    """UI only: persist edits the user made to a claim draft."""
    return tools.save_claim_draft(claim_id, subject, body, user_id=USER_ID)


@mcp.tool(tags={"ui"})
def delete_purchase(purchase_id: int) -> dict:
    """UI only: remove a saved purchase (and its drafts)."""
    return tools.delete_purchase(purchase_id, user_id=USER_ID)


@mcp.tool(tags={"ui"})
def seed_demo_data() -> dict:
    """UI only: load synthetic sample purchases for demos."""
    return tools.seed_demo_data(user_id=USER_ID)


# ----------------------------- Auth + entrypoint ----------------------------- #
class BearerAuth:
    """Minimal ASGI middleware: require `Authorization: Bearer <MCP_AUTH_TOKEN>` when a token is set."""

    def __init__(self, app, token: str):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            if headers.get(b"authorization", b"").decode() != f"Bearer {self.token}":
                body = json.dumps({"error": "unauthorized"}).encode()
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json"),
                                        (b"content-length", str(len(body)).encode())]})
                await send({"type": "http.response.body", "body": body})
                return
        await self.app(scope, receive, send)


def build_app():
    app = mcp.http_app(path="/mcp")
    token = os.getenv("MCP_AUTH_TOKEN", "").strip()
    return BearerAuth(app, token) if token else app


if __name__ == "__main__":
    import uvicorn

    init_db()
    host = os.getenv("MCP_HOST", "127.0.0.1")  # keep local unless you add HTTPS + a token
    port = int(os.getenv("MCP_PORT", "8765"))
    if host not in ("127.0.0.1", "localhost") and not os.getenv("MCP_AUTH_TOKEN"):
        raise SystemExit("Refusing to bind a public address without MCP_AUTH_TOKEN set.")
    print(f"Warranty Vault MCP server -> http://{host}:{port}/mcp")
    uvicorn.run(build_app(), host=host, port=port, log_level="warning")
