"""Run: python tests/test_tools.py   (uses a throw-away database)"""
import os, sys, tempfile
from pathlib import Path

os.environ["WARRANTY_DB"] = str(Path(tempfile.mkdtemp()) / "test.db")
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

import tools
from database import add_months, init_db, today
from datetime import date, timedelta

init_db()
t = today().isoformat()

# missing info is requested, never invented
assert tools.log_purchase("Dishwasher")["needs"] == ["purchase_date"]
assert tools.log_purchase("Dishwasher", t)["needs"] == ["warranty_duration_months"]
# validation
assert tools.log_purchase("X", "2999-01-01", 12)["error"] == "future_date"
assert tools.log_purchase("X", "bad", 12)["error"] == "invalid_date"
assert tools.log_purchase("X", t, 12, purchase_price=-5)["error"] == "invalid_price"
assert tools.log_purchase("X", t, 12, currency="ZZZ")["error"] == "invalid_currency"
assert tools.log_purchase("X", t, 0)["error"] == "invalid_warranty"
# happy path + calendar-safe expiry
r = tools.log_purchase("Dishwasher", t, 24, 600)
assert r["ok"] and r["purchase"]["warranty_expiry_date"] == add_months(today(), 24).isoformat()
assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
assert tools.log_purchase("dishwasher", t, 24)["error"] == "duplicate"
# unknown warranty is stored without a made-up expiry
u = tools.log_purchase("Toaster", t, None, allow_unknown_warranty=True)
assert u["ok"] and u["purchase"]["status"] == "unknown"
# statuses
tools.log_purchase("Phone", (today() - timedelta(days=350)).isoformat(), 12)
tools.log_purchase("Old TV", (today() - timedelta(days=800)).isoformat(), 12)
assert tools.check_warranty("phone")["purchase"]["status"] == "expiring_soon"
assert tools.check_warranty("old tv")["purchase"]["status"] == "expired"
assert tools.check_warranty("dishwasher")["purchase"]["status"] == "active"
assert tools.check_warranty("nothing")["error"] == "not_found"
# SQL injection attempt is treated as plain text
assert tools.check_warranty("'; DROP TABLE purchases; --")["error"] == "not_found"
assert tools.check_warranty("dishwasher")["ok"]
# expiring window
e = tools.expiring_soon(30)
assert [i["product_name"] for i in e["items"]] == ["Phone"]
assert tools.expiring_soon(1)["count"] == 0 and "no recorded" in tools.expiring_soon(1)["message"]
assert tools.expiring_soon(0)["error"] == "invalid_window"
# claims
assert tools.draft_claim("dishwasher")["needs"] == ["issue_description"]
c = tools.draft_claim("dishwasher", "It stopped cleaning properly.")
assert c["ok"] and "$600" in c["claim"]["body"] and "stopped cleaning" in c["claim"]["body"]
assert tools.draft_claim("old tv", "No picture")["warnings"]
assert tools.save_claim_draft(c["claim"]["id"], "New subject", "New body")["ok"]
# dashboard + FK cascade
s = tools.dashboard_summary()
assert s["counts"]["total"] == 4 and len(s["claims"]) == 2
did = next(p["id"] for p in s["purchases"] if p["product_name"] == "Old TV")
tools.delete_purchase(did)
assert len(tools.dashboard_summary()["claims"]) == 1
print("All tool tests passed.")
