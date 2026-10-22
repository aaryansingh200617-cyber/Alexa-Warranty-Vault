"""Tool implementations. Every function returns a plain, JSON-serialisable dict.

Shape conventions:
  {"ok": True, ...}                       -> success
  {"ok": False, "needs": [...], "message"} -> missing information; ask the user
  {"ok": False, "error": "...", "message"} -> failure
"""
import re
from datetime import date, datetime
from typing import Optional

from database import (
    add_months, get_conn, iso_in, now_iso, parse_date, row_to_purchase, today,
    warranty_status,
)

CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
KNOWN_CURRENCIES = {
    "USD", "EUR", "GBP", "INR", "CAD", "AUD", "JPY", "CNY", "SGD", "AED",
    "CHF", "SEK", "NZD", "MXN", "BRL", "ZAR", "KRW", "HKD", "NOK", "DKK",
}
SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥"}


def _needs(fields: list[str], message: str) -> dict:
    return {"ok": False, "needs": fields, "message": message}


def _error(code: str, message: str) -> dict:
    return {"ok": False, "error": code, "message": message}


def _clean(text: Optional[str], limit: int = 200) -> Optional[str]:
    if text is None:
        return None
    text = " ".join(str(text).split())
    return text[:limit] or None


def _money(price, currency) -> str:
    if price is None:
        return "not recorded"
    sym = SYMBOLS.get(currency, "")
    amount = f"{price:,.2f}".rstrip("0").rstrip(".")
    return f"{sym}{amount}" if sym else f"{amount} {currency}"


def _pretty(d: Optional[str]) -> str:
    if not d:
        return "unknown"
    x = parse_date(d)
    return f"{x.strftime('%B')} {x.day}, {x.year}"


def _duration_label(months: Optional[int]) -> str:
    if not months:
        return "unknown"
    years, rem = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if rem:
        parts.append(f"{rem} month{'s' if rem != 1 else ''}")
    return " ".join(parts)


def _find(conn, product_name: str, user_id: str) -> list[dict]:
    """Case-insensitive match, parameterised. Exact matches win over partial ones."""
    name = _clean(product_name, 100) or ""
    rows = conn.execute(
        "SELECT * FROM purchases WHERE user_id = ? AND (LOWER(product_name) = LOWER(?) "
        "OR LOWER(product_name) LIKE ? ESCAPE '\\' OR LOWER(brand) = LOWER(?)) "
        "ORDER BY purchase_date DESC, id DESC",
        (user_id, name, "%" + name.lower().replace("%", r"\%").replace("_", r"\_") + "%", name),
    ).fetchall()
    items = [row_to_purchase(r) for r in rows]
    exact = [i for i in items if i["product_name"].lower() == name.lower()]
    return exact or items


# --------------------------------------------------------------------------- #
# Tool 1: log_purchase
# --------------------------------------------------------------------------- #
def log_purchase(
    product_name: str,
    purchase_date: Optional[str] = None,
    warranty_duration_months: Optional[int] = None,
    purchase_price: Optional[float] = None,
    currency: str = "USD",
    brand: Optional[str] = None,
    category: Optional[str] = None,
    receipt_path: Optional[str] = None,
    notes: Optional[str] = None,
    allow_unknown_warranty: bool = False,
    user_id: str = "demo",
) -> dict:
    name = _clean(product_name, 100)
    if not name:
        return _needs(["product_name"], "Which product did you buy?")
    if not purchase_date:
        return _needs(["purchase_date"], f"What was the purchase date for your {name}?")
    try:
        pdate = parse_date(purchase_date)
    except (ValueError, TypeError):
        return _error("invalid_date", "Dates must use the format YYYY-MM-DD.")
    if pdate > today():
        return _error("future_date", "The purchase date can't be in the future.")
    if warranty_duration_months is None and not allow_unknown_warranty:
        return _needs(["warranty_duration_months"],
                      f"How long is the warranty on your {name}? I won't guess an expiry date.")
    if warranty_duration_months is not None:
        try:
            warranty_duration_months = int(warranty_duration_months)
        except (ValueError, TypeError):
            return _error("invalid_warranty", "Warranty duration must be a whole number of months.")
        if not 0 < warranty_duration_months <= 600:
            return _error("invalid_warranty", "Warranty duration must be between 1 and 600 months.")
    if purchase_price is not None:
        try:
            purchase_price = float(purchase_price)
        except (ValueError, TypeError):
            return _error("invalid_price", "Price must be a number.")
        if purchase_price < 0:
            return _error("invalid_price", "Price can't be negative.")
    currency = (currency or "USD").upper().strip()
    if not CURRENCY_RE.match(currency) or currency not in KNOWN_CURRENCIES:
        return _error("invalid_currency", f"'{currency}' isn't a supported currency code.")

    expiry = (add_months(pdate, warranty_duration_months).isoformat()
              if warranty_duration_months else None)

    with get_conn() as conn:
        dup = conn.execute(
            "SELECT id FROM purchases WHERE user_id = ? AND LOWER(product_name) = LOWER(?) "
            "AND purchase_date = ?", (user_id, name, pdate.isoformat())).fetchone()
        if dup:
            return _error("duplicate", f"You already saved a {name} bought on {_pretty(pdate.isoformat())}.")
        cur = conn.execute(
            "INSERT INTO purchases (user_id, product_name, brand, category, purchase_date, "
            "purchase_price, currency, warranty_duration_months, warranty_expiry_date, "
            "receipt_path, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (user_id, name, _clean(brand, 60), _clean(category, 60), pdate.isoformat(),
             purchase_price, currency, warranty_duration_months, expiry,
             _clean(receipt_path, 300), _clean(notes, 500), now_iso()))
        row = conn.execute("SELECT * FROM purchases WHERE id = ?", (cur.lastrowid,)).fetchone()
    purchase = row_to_purchase(row)
    if expiry:
        msg = (f"Your {name} has been added to Warranty Vault. Its recorded warranty "
               f"expires on {_pretty(expiry)}.")
    else:
        msg = (f"Your {name} has been saved, but no warranty duration was recorded, "
               "so there is no confirmed expiry date.")
    return {"ok": True, "purchase": purchase, "message": msg}


# --------------------------------------------------------------------------- #
# Tool 2: check_warranty
# --------------------------------------------------------------------------- #
CAVEAT = ("This status is calculated from the dates saved in Warranty Vault. "
          "It does not guarantee that the manufacturer will approve a claim.")


def check_warranty(product_name: str, user_id: str = "demo") -> dict:
    if not _clean(product_name):
        return _needs(["product_name"], "Which product should I check?")
    with get_conn() as conn:
        matches = _find(conn, product_name, user_id)
    if not matches:
        return _error("not_found", f"I couldn't find '{product_name}' in your saved purchases.")
    if len(matches) > 1:
        return {"ok": True, "multiple": True, "matches": matches, "caveat": CAVEAT,
                "message": f"You have {len(matches)} saved items matching '{product_name}'. "
                           "Here is each one's status."}
    p = matches[0]
    name, st, exp = p["product_name"], p["status"], p["warranty_expiry_date"]
    if st == "unknown":
        msg = f"I don't have a recorded expiry date for your {name}, so its status is unknown."
    elif st == "expired":
        msg = f"The recorded warranty for your {name} expired on {_pretty(exp)}."
    elif st == "expiring_soon":
        msg = (f"Your {name} is still covered, but only for {p['days_remaining']} more day"
               f"{'s' if p['days_remaining'] != 1 else ''}. The recorded expiry date is {_pretty(exp)}.")
    else:
        msg = f"Your {name} is covered. The recorded expiry date is {_pretty(exp)}."
    return {"ok": True, "multiple": False, "purchase": p, "caveat": CAVEAT, "message": msg}


# --------------------------------------------------------------------------- #
# Tool 3: expiring_soon
# --------------------------------------------------------------------------- #
def expiring_soon(within_days: int = 30, user_id: str = "demo") -> dict:
    try:
        within_days = int(within_days)
    except (ValueError, TypeError):
        return _error("invalid_window", "within_days must be a whole number.")
    if not 1 <= within_days <= 3650:
        return _error("invalid_window", "within_days must be between 1 and 3650.")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM purchases WHERE user_id = ? AND warranty_expiry_date IS NOT NULL "
            "AND warranty_expiry_date >= ? AND warranty_expiry_date <= ? "
            "ORDER BY warranty_expiry_date ASC",
            (user_id, today().isoformat(), iso_in(within_days))).fetchall()
    items = [row_to_purchase(r) for r in rows]
    if not items:
        msg = f"You have no recorded warranties expiring within the next {within_days} days."
    else:
        names = [i["product_name"] for i in items]
        listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        msg = (f"You have {len(items)} warrant{'y' if len(items) == 1 else 'ies'} expiring "
               f"in the next {within_days} days: {listed}.")
    return {"ok": True, "within_days": within_days, "count": len(items), "items": items, "message": msg}


# --------------------------------------------------------------------------- #
# Tool 4: draft_claim
# --------------------------------------------------------------------------- #
def draft_claim(
    product_name: str,
    issue_description: Optional[str] = None,
    customer_name: Optional[str] = None,
    purchase_id: Optional[int] = None,
    user_id: str = "demo",
) -> dict:
    if not _clean(product_name) and not purchase_id:
        return _needs(["product_name"], "Which product is the claim for?")
    with get_conn() as conn:
        if purchase_id:
            row = conn.execute("SELECT * FROM purchases WHERE id = ? AND user_id = ?",
                               (purchase_id, user_id)).fetchone()
            matches = [row_to_purchase(row)] if row else []
        else:
            matches = _find(conn, product_name, user_id)
        if not matches:
            return _error("not_found", f"I couldn't find '{product_name}' in your saved purchases.")
        if len(matches) > 1:
            return {"ok": False, "needs": ["purchase_id"], "matches": matches,
                    "message": f"You have {len(matches)} items matching '{product_name}'. Which one is the claim for?"}
        issue = _clean(issue_description, 1000)
        p = matches[0]
        if not issue:
            return _needs(["issue_description"], f"What problem is your {p['product_name']} having?")

        who = _clean(customer_name, 80) or "[Customer Name]"
        name = p["product_name"]
        title = f"{p['brand']} {name}" if p.get("brand") and p["brand"].lower() not in name.lower() else name
        lines = [
            "Dear Customer Support Team,", "",
            f"I would like to request assistance regarding my {title.lower() if title == name else title}.", "",
            f"Product: {title}",
            f"Purchase price: {_money(p['purchase_price'], p['currency'])}",
            f"Purchase date: {_pretty(p['purchase_date'])}",
            f"Recorded warranty duration: {_duration_label(p['warranty_duration_months'])}",
            f"Recorded warranty expiry: {_pretty(p['warranty_expiry_date'])}",
        ]
        if p.get("receipt_path"):
            lines.append(f"Receipt reference: {p['receipt_path']}")
        lines += [f"Issue: {issue}", "",
                  "Please advise me on the next steps for inspection, repair, or replacement "
                  "under the applicable warranty terms.", "",
                  "Thank you for your assistance.", "", "Kind regards,", who]
        body, subject = "\n".join(lines), f"Warranty Claim Request — {title}"
        cur = conn.execute(
            "INSERT INTO claims (purchase_id, issue_description, draft_subject, draft_body, status, created_at) "
            "VALUES (?,?,?,?, 'draft', ?)", (p["id"], issue, subject, body, now_iso()))
        claim_id = cur.lastrowid

    warnings = []
    if p["status"] == "expired":
        warnings.append(f"The recorded warranty expired on {_pretty(p['warranty_expiry_date'])}. "
                        "The manufacturer may decline the claim, but you can still ask.")
    elif p["status"] == "unknown":
        warnings.append("No warranty expiry date is recorded for this product.")
    return {"ok": True, "claim": {"id": claim_id, "subject": subject, "body": body, "status": "draft",
                                 "issue_description": issue},
            "purchase": p, "warnings": warnings,
            "message": "Your warranty claim draft is ready. Would you like to review it?"}


# --------------------------------------------------------------------------- #
# UI-support tools (read-only dashboard, draft editing, demo data).
# Not offered to the language model.
# --------------------------------------------------------------------------- #
def dashboard_summary(user_id: str = "demo") -> dict:
    with get_conn() as conn:
        purchases = [row_to_purchase(r) for r in conn.execute(
            "SELECT * FROM purchases WHERE user_id = ? ORDER BY created_at DESC, id DESC", (user_id,))]
        claims = [dict(r) for r in conn.execute(
            "SELECT c.*, p.product_name FROM claims c JOIN purchases p ON p.id = c.purchase_id "
            "WHERE p.user_id = ? ORDER BY c.id DESC LIMIT 20", (user_id,))]
    counts = {"total": len(purchases), "active": 0, "expiring_soon": 0, "expired": 0, "unknown": 0}
    for p in purchases:
        counts[p["status"]] += 1
    expiring = sorted([p for p in purchases if p["status"] == "expiring_soon"],
                      key=lambda p: p["days_remaining"])
    return {"ok": True, "counts": counts, "purchases": purchases, "expiring": expiring, "claims": claims}


def save_claim_draft(claim_id: int, subject: str, body: str, user_id: str = "demo") -> dict:
    subject, body = _clean(subject, 300), (body or "").strip()[:5000]
    if not subject or not body:
        return _error("invalid_draft", "A draft needs both a subject and a body.")
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE claims SET draft_subject = ?, draft_body = ?, updated_at = ? WHERE id = ? "
            "AND purchase_id IN (SELECT id FROM purchases WHERE user_id = ?)",
            (subject, body, now_iso(), claim_id, user_id))
        if cur.rowcount == 0:
            return _error("not_found", "Draft not found.")
    return {"ok": True, "message": "Draft saved."}


def delete_purchase(purchase_id: int, user_id: str = "demo") -> dict:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM purchases WHERE id = ? AND user_id = ?", (purchase_id, user_id))
    return {"ok": cur.rowcount > 0, "message": "Purchase removed." if cur.rowcount else "Purchase not found."}


def seed_demo_data(user_id: str = "demo") -> dict:
    """Synthetic sample data, dated relative to today so every status shows up."""
    from datetime import timedelta
    t = today()
    samples = [
        ("Dishwasher", "Bosch", "Kitchen", t - timedelta(days=40), 599, 24),
        ("Refrigerator", "Samsung", "Kitchen", t - timedelta(days=300), 1250, 36),
        ("Noise-cancelling headphones", "Sony", "Audio", t - timedelta(days=335), 349, 12),
        ("4K Monitor", "Dell", "Computing", t - timedelta(days=350), 429, 12),
        ("Washing machine", "LG", "Laundry", t - timedelta(days=900), 799, 24),
        ("Laptop", "Lenovo", "Computing", t - timedelta(days=120), 1099, 24),
    ]
    added = 0
    for name, brand, cat, d, price, months in samples:
        r = log_purchase(name, d.isoformat(), months, price, "USD", brand, cat, user_id=user_id)
        added += 1 if r["ok"] else 0
    return {"ok": True, "added": added, "message": f"Loaded {added} sample purchases."}
