"""Offline fallback agent: keyword intents + slot filling. Needs no API key.

It still calls the real MCP tools, so persistence, validation and expiry
calculation behave exactly as with an LLM. It is just less flexible at language.
"""
import calendar
import os
import re
from datetime import date, datetime, timedelta

from dateutil import parser as dateparser

import mcp_bridge
from llm_agent import TOOL_LABELS

DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD").upper()
NUM_WORDS = {"one": 1, "a": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "eighteen": 18}
MONTHS = r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
LEADING = r"^(?:a|an|the|my|our|new|brand new|some)\s+"
ISSUE_WORDS = r"(?:has|have|had|is|isn't|is not|stopped|won't|will not|doesn't|does not|keeps|broke|broken|makes|not|started|began|no longer|can't|cannot|flicker|flickering|leaking|leaks|damaged|cracked|dead|defect|defective|faulty)"

HELP = ("Hi! I can save a purchase, check a warranty, list warranties that expire soon, or prepare a claim. "
        "Try: “I bought a dishwasher for $600 with a two-year warranty.”")


def _num(token: str):
    token = token.lower()
    return NUM_WORDS.get(token) if token in NUM_WORDS else float(token)


def extract_months(text: str):
    m = re.search(r"(\d+(?:\.\d+)?|" + "|".join(NUM_WORDS) + r")[\s-]*(year|yr|month|mo)s?\b", text, re.I)
    if not m:
        return None
    n = _num(m.group(1))
    return int(round(n * 12)) if m.group(2).lower() in ("year", "yr") else int(n)


def extract_price(text: str):
    m = re.search(r"(?:(\$|€|£|₹|rs\.?|inr|usd|eur|gbp)\s?(\d[\d,]*(?:\.\d+)?))", text, re.I)
    if m:
        sym = m.group(1).lower().rstrip(".")
        cur = {"$": "USD", "usd": "USD", "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP",
               "₹": "INR", "rs": "INR", "inr": "INR"}[sym]
        return float(m.group(2).replace(",", "")), cur
    m = re.search(r"\bfor\s+(\d[\d,]*(?:\.\d+)?)\b(?!\s*[- ]?(?:year|yr|month|day|week))", text, re.I)
    if m:
        return float(m.group(1).replace(",", "")), DEFAULT_CURRENCY
    return None, None


def extract_date(text: str):
    t, today = text.lower(), date.today()
    if re.search(r"\btoday\b", t):
        return today.isoformat()
    if re.search(r"\byesterday\b", t):
        return (today - timedelta(days=1)).isoformat()
    m = re.search(r"(\d+|a|one|two|three|four)\s+(day|week|month|year)s?\s+ago", t)
    if m:
        n, unit = _num(m.group(1)), m.group(2)
        if unit == "month":
            idx = today.year * 12 + today.month - 1 - int(n)
            y, mo = divmod(idx, 12)
            return date(y, mo + 1, min(today.day, calendar.monthrange(y, mo + 1)[1])).isoformat()
        return (today - timedelta(days={"day": 1, "week": 7, "year": 365}[unit] * int(n))).isoformat()
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        return m.group(0)
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b", t)  # day-first
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            return None
    m = re.search(rf"\b(?:\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?)?(?:{MONTHS})\.?(?:\s+\d{{1,2}}(?:st|nd|rd|th)?)?(?:,?\s+\d{{4}})?\b", t)
    if m and re.search(MONTHS, m.group(0)):
        try:
            d = dateparser.parse(re.sub(r"(st|nd|rd|th)\b", "", m.group(0)), default=datetime(today.year, today.month, 1)).date()
            if not re.search(r"\d{4}", m.group(0)) and d > today:
                d = d.replace(year=d.year - 1)
            return d.isoformat()
        except (ValueError, OverflowError):
            return None
    return None


def _trim(name: str) -> str:
    name = re.sub(LEADING, "", name.strip(" .,!?"), flags=re.I)
    name = re.sub(r"^(?:new)\s+", "", name, flags=re.I)
    return name.strip(" .,!?")[:100]


def detect_intent(t: str):
    t = t.lower()
    # Claim / issue / repair intents for any product
    if re.search(r"\b(claim|claims|broke|broken|stopped|not working|isn't working|doesn't work|faulty|defective|repair|replacement|issue|issues|problem|problems|trouble|damage|damaged|cracked|leak|leaking|won't turn on|won't start|flicker|flickering|dead)\b", t):
        return "draft_claim"
    # "which warranties expire soon" / "list expiring" → expiring_soon (no product named)
    if re.search(r"\bexpir", t) and not re.search(r"\b(is|does|when does|when will|how long)\b.*\bmy\b", t) \
            and not re.search(r"\bmy .{1,40} expir", t):
        return "expiring_soon"
    if re.search(r"\b(bought|purchased|ordered|picked up)\b|\bi got (?:a|an|the|my|new)\b", t):
        return "log_purchase"
    # Check warranty / expiry for a specific product
    if re.search(r"\b(warranty|covered|coverage|guarantee|expir|expire|expiry|valid|still under|how long|when does|when will|days left|days remain)\b", t):
        return "check_warranty"
    return None


def parse_product(intent: str, text: str):
    if intent == "log_purchase":
        m = re.search(r"(?:bought|purchased|ordered|picked up|got)\s+(.+?)(?:\s+(?:for|on|with|at|from|yesterday|today|last|about|\d+\s+\w+\s+ago)\b|[,.;]|\s+[$€£₹]|$)", text, re.I)
    elif intent == "draft_claim":
        m = (
            re.search(r"\b(?:claim|warranty claim)\s+(?:for|about|on|regarding)\s+(?:my|the)?\s*(.+?)(?:[.,?!]|\s+(?:because|as|since|is|has|having|stopped|broke)\b|$)", text, re.I) or
            re.search(r"\b(?:issue|problem|trouble|damage|fault)\s+(?:with|in|on|regarding)\s+(?:my|the)?\s*(.+?)(?:[.,?!]|\s+(?:help|please|draft|prepare|can you)\b|$)", text, re.I) or
            re.search(r"\b(?:prepare|file|make|submit|draft)\s+(?:a\s+)?claim\s+(?:for|on|regarding)?\s*(?:my|the)?\s*(.+?)(?:[.,?!]|$)", text, re.I) or
            re.search(rf"\b(?:my|the)?\s*(.+?)\s+{ISSUE_WORDS}\b", text, re.I) or
            re.search(r"\b(?:my|the)?\s*(.+?)\s+(?:has|have|having|got)\s+(?:an?\s+)?(?:issue|problem|trouble|fault)", text, re.I) or
            re.search(r"\b(?:for|about|on)\s+(?:my|the)?\s*(.+?)(?:[.,?!]|\s+(?:is|has|broke|stopped)\b|$)", text, re.I)
        )
    else:
        m = re.search(r"\b(?:is|are|does|do|when does|check)\s+(?:my|the)\s+(.+?)\s+(?:still|under|covered|in|have|expire|warranty)", text, re.I) or \
            re.search(r"\b(?:my|the)\s+(.+?)\s+(?:warranty|still|covered)", text, re.I) or \
            re.search(r"\bwarranty\s+(?:for|on|of)\s+(?:my|the)?\s*(.+?)(?:[.,?!]|$)", text, re.I)
    return _trim(m.group(1)) if m else None


def parse_issue(text: str):
    m = re.search(rf"(?:my|the)?\s*.+?\s+({ISSUE_WORDS}\b.*?)(?:[.!?]|\s+(?:help|prepare|please|can you|draft|file)\b|$)", text, re.I)
    if m:
        desc = m.group(1).strip()
        if len(desc) >= 3 and not re.fullmatch(r"claim|file claim|draft claim", desc, re.I):
            return f"The product {desc}." if not desc.lower().startswith("the") else desc
    m = re.search(r"\b(?:because|since|as)\s+(.+?)(?:[.!?]|\s+(?:help|please)\b|$)", text, re.I)
    if m:
        return m.group(1).strip().capitalize() + "."
    m = re.search(r"\b(?:issue|problem)\s+(?:is|with)?\s+(.+?)(?:[.!?]|$)", text, re.I)
    if m:
        cand = m.group(1).strip()
        if re.search(ISSUE_WORDS, cand, re.I) or len(cand.split()) > 2:
            return cand.capitalize() + "."
    return None


def parse_window(text: str) -> int:
    t = text.lower()
    m = re.search(r"(\d+)\s*(day|week|month)s?", t)
    if m:
        return int(m.group(1)) * {"day": 1, "week": 7, "month": 30}[m.group(2)]
    if "week" in t:
        return 7
    if "month" in t:
        return 30
    if "year" in t:
        return 365
    return 30


def _format(intent: str, result: dict) -> str:
    msg = result.get("message", "Done.")
    if intent == "check_warranty" and result.get("multiple"):
        rows = [f"{m['product_name']} ({m['purchase_date']}): {m['status'].replace('_', ' ')}, "
                f"expires {m['warranty_expiry_date'] or 'unknown'}" for m in result["matches"]]
        return msg + " " + "; ".join(rows) + "."
    return msg


async def handle(session: dict, text: str) -> tuple[str, list[dict]]:
    events: list[dict] = []
    text = text.strip()
    pending = session.get("pending")

    if re.fullmatch(r"(cancel|never ?mind|stop|forget it)[.!]?", text, re.I):
        session["pending"] = None
        return "Okay, cancelled. What else can I help with?", events

    intent = detect_intent(text)
    if pending and (not intent or intent == pending["tool"]):
        tool, args, awaiting = pending["tool"], dict(pending["args"]), pending["awaiting"]
        if awaiting == "purchase_date":
            val = extract_date(text)
            if val is None:
                return "I couldn't read that date. Try “October 21, 2026” or “2026-10-21”.", events
            args["purchase_date"] = val
        elif awaiting == "warranty_duration_months":
            val = extract_months(text)
            if val is None and re.fullmatch(r"\d+", text):
                val = int(text) * 12 if int(text) <= 10 else int(text)
            if val is None:
                return "How long is the warranty? For example “2 years” or “18 months”.", events
            args["warranty_duration_months"] = val
        elif awaiting == "issue_description":
            args["issue_description"] = text
        elif awaiting == "product_name":
            args["product_name"] = _trim(text)
        elif awaiting == "purchase_id":
            ids = [m["id"] for m in pending.get("matches", [])]
            pick = re.search(r"\d+", text)
            if pick and int(pick.group()) in range(1, len(ids) + 1):
                args["purchase_id"] = ids[int(pick.group()) - 1]
            else:
                return "Please answer with the number of the item (1, 2, …).", events
    else:
        session["pending"] = None
        if not intent:
            # ── Smart fallback: if the message looks like a bare product name,
            # try check_warranty before giving up with the HELP message.
            # Heuristic: ≤ 6 words, no sentence-structure words, not a greeting/help.
            candidate = _trim(text)
            words = candidate.split()
            is_greeting = re.fullmatch(r"hi+|hello+|hey+|help|what can you do|what do you do", candidate, re.I)
            if candidate and len(words) <= 6 and not is_greeting:
                tool, args = "check_warranty", {"product_name": candidate}
                try:
                    result = await mcp_bridge.call_tool(tool, args)
                except Exception as e:
                    return HELP, events
                label = TOOL_LABELS[tool]
                events.append({"name": tool, "label": label, "arguments": args,
                                "ok": bool(result.get("ok")), "result": result})
                if result.get("ok"):
                    session["pending"] = None
                    return _format(tool, result), events
                # Product not found → show help so user knows what they can do
                if result.get("error") == "not_found":
                    return (
                        f'I couldn\'t find "{candidate}" in your saved purchases. '
                        f'You can add it by saying something like: '
                        f'"I bought a {candidate} with a 2-year warranty."'
                    ), events
            return HELP, events
        tool, args = intent, {}
        if tool == "expiring_soon":
            args["within_days"] = parse_window(text)
        else:
            product = parse_product(tool, text)
            if product:
                args["product_name"] = product
            if tool == "log_purchase":
                price, cur = extract_price(text)
                months, when = extract_months(text), extract_date(text)
                if price is not None:
                    args["purchase_price"], args["currency"] = price, cur
                if months:
                    args["warranty_duration_months"] = months
                if when:
                    args["purchase_date"] = when
            elif tool == "draft_claim":
                issue = parse_issue(text)
                if issue:
                    args["issue_description"] = issue

    if tool in ("log_purchase", "check_warranty", "draft_claim") and not args.get("product_name"):
        session["pending"] = {"tool": tool, "args": args, "awaiting": "product_name"}
        return "Which product do you mean?", events

    try:
        result = await mcp_bridge.call_tool(tool, args)
    except Exception as e:
        events.append({"name": tool, "label": TOOL_LABELS[tool], "arguments": args, "ok": False,
                       "result": {"ok": False, "error": "tool_failed", "message": str(e)}})
        return "I couldn't reach the Warranty Vault server, so nothing was saved. Please check it is running.", events
    events.append({"name": tool, "label": TOOL_LABELS[tool], "arguments": args,
                   "ok": bool(result.get("ok")), "result": result})

    if not result.get("ok") and result.get("needs"):
        session["pending"] = {"tool": tool, "args": args, "awaiting": result["needs"][0],
                              "matches": result.get("matches", [])}
        msg = result["message"]
        if result.get("matches"):
            msg += " " + " ".join(f"{i}) {m['product_name']} ({m['purchase_date']})"
                                  for i, m in enumerate(result["matches"], 1))
        return msg, events
    session["pending"] = None
    return _format(tool, result), events
