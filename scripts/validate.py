#!/usr/bin/env python3
"""Validates feed.json before it reaches the Crypto Watch app. Exit code 1 on any problem."""
import json, re, sys
from datetime import datetime

PATH = sys.argv[1] if len(sys.argv) > 1 else "feed.json"
errors = []

def err(msg): errors.append(msg)

def ts_ok(v):
    if v is None: return False
    if isinstance(v, (int, float)): return True
    s = str(v).strip()
    if s.isdigit(): return True
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00")); return True
    except ValueError:
        return False

ENUMS = {
    "status": {"EARLY", "UPCOMING", "LIVE"},
    "priority": {"LOW", "NORMAL", "HIGH", "CRITICAL"},
    "verification": {"OFFICIAL", "DETECTED", "UNVERIFIED"},
    "wallet": {"TOKEN_CA", "OFFICIAL_WALLET", "TREASURY", "CREATOR", "FUNDER", "CLUSTER", "OTHER"},
    "link": {"WEBSITE", "X", "TWITTER", "TELEGRAM", "DISCORD", "DOCS", "EXPLORER", "GITHUB", "OTHER"},
    "signal": {"FIRST", "RECALL"},
    "kind": {"SIGNAL", "MILESTONE", "WALLET"},
    "alert": {"NEW_PROJECT", "PROJECT_UPDATE", "TGE", "LAUNCH", "CA_DETECTED", "OFFICIAL_WALLET_DETECTED",
              "WALLET_CHANGED", "CREATOR_DETECTED", "FUNDER_DETECTED", "CLUSTER_DETECTED", "FIRST", "RECALL",
              "MILESTONE_1_5X", "MILESTONE_2X", "MILESTONE_3X", "MILESTONE_5X", "1.5X", "2X", "3X", "5X", "5X+",
              "PRICE_ALERT", "SYSTEM"},
}
SECRET = re.compile(r"(api[_-]?key|secret|token|password|private[_-]?key|bearer)\s*[:=]", re.I)

def enum(where, field, value, kind, required=False):
    if value is None:
        if required: err(f"{where}: missing {field}")
        return
    if str(value).upper() not in ENUMS[kind]:
        err(f"{where}: {field}={value!r} not one of {sorted(ENUMS[kind])}")

def url_ok(where, v):
    if v is not None and not str(v).startswith("https://"):
        err(f"{where}: URL must be https:// ({v!r})")

try:
    raw = open(PATH, encoding="utf-8").read()
    feed = json.loads(raw)
except Exception as e:
    print(f"::error::{PATH} is not valid JSON: {e}"); sys.exit(1)

if SECRET.search(raw): err("feed looks like it contains a secret (api key / token / password)")
if feed.get("schemaVersion") != 1: err("schemaVersion must be 1")

project_ids, signal_ids, ids = set(), set(), set()
for i, p in enumerate(feed.get("projects", [])):
    w = f"projects[{i}]({p.get('id')})"
    if not p.get("id") or not p.get("name"): err(f"{w}: id and name are required")
    if p.get("id") in project_ids: err(f"{w}: duplicate project id")
    project_ids.add(p.get("id"))
    enum(w, "status", p.get("status"), "status")
    url_ok(w + ".logoUrl", p.get("logoUrl")); url_ok(w + ".bannerUrl", p.get("bannerUrl"))
    for j, l in enumerate(p.get("links", [])):
        enum(f"{w}.links[{j}]", "type", l.get("type"), "link"); url_ok(f"{w}.links[{j}]", l.get("url"))
        if not l.get("url"): err(f"{w}.links[{j}]: url required")
    for j, wl in enumerate(p.get("wallets", [])):
        ww = f"{w}.wallets[{j}]"
        enum(ww, "type", wl.get("type"), "wallet", required=True)
        enum(ww, "verification", wl.get("verification"), "verification")
        if wl.get("address") and not wl.get("source"): err(f"{ww}: an address needs a source")
    for j, u in enumerate(p.get("updates", [])):
        uw = f"{w}.updates[{j}]({u.get('id')})"
        if not u.get("id") or not u.get("title"): err(f"{uw}: id and title required")
        if u.get("id") in ids: err(f"{uw}: duplicate update id")
        ids.add(u.get("id"))
        if not ts_ok(u.get("timestamp")): err(f"{uw}: bad timestamp {u.get('timestamp')!r}")
        enum(uw, "priority", u.get("priority"), "priority"); url_ok(uw, u.get("url"))

for i, s in enumerate(feed.get("signals", [])):
    w = f"signals[{i}]({s.get('id')})"
    if not s.get("id"): err(f"{w}: id required")
    if s.get("id") in signal_ids: err(f"{w}: duplicate signal id")
    signal_ids.add(s.get("id"))
    enum(w, "type", s.get("type"), "signal")
    if not ts_ok(s.get("signalTime")): err(f"{w}: bad signalTime")
    if not (s.get("token") or {}).get("name"): err(f"{w}: token.name required")
    for j, h in enumerate(s.get("history", [])):
        enum(f"{w}.history[{j}]", "kind", h.get("kind"), "kind")
        if not ts_ok(h.get("timestamp")): err(f"{w}.history[{j}]: bad timestamp")

alert_ids = set()
for i, a in enumerate(feed.get("alerts", [])):
    w = f"alerts[{i}]({a.get('id')})"
    if not a.get("id") or not a.get("title"): err(f"{w}: id and title required")
    if a.get("id") in alert_ids: err(f"{w}: duplicate alert id")
    alert_ids.add(a.get("id"))
    enum(w, "type", a.get("type"), "alert", required=True)
    enum(w, "priority", a.get("priority"), "priority")
    if not ts_ok(a.get("timestamp")): err(f"{w}: bad timestamp")
    if a.get("projectId") and a["projectId"] not in project_ids: err(f"{w}: unknown projectId {a['projectId']!r}")
    if a.get("signalId") and a["signalId"] not in signal_ids: err(f"{w}: unknown signalId {a['signalId']!r}")

if errors:
    for e in errors: print(f"::error::{e}")
    sys.exit(1)
print(f"OK: {len(project_ids)} projects, {len(signal_ids)} signals, {len(alert_ids)} alerts")
