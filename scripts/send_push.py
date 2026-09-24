#!/usr/bin/env python3
"""
Sends new feed alerts to the Crypto Watch app in real time through Firebase Cloud Messaging (HTTP v1).

  python3 scripts/send_push.py --old old.json --new feed.json    # alerts added by a commit
  python3 scripts/send_push.py --test "Push test from GitHub"    # delivery test

Needs the FCM_SERVICE_ACCOUNT_JSON environment variable (a Firebase service account key, stored as a
GitHub Secret). Without it the script explains what is missing and exits successfully, so the feed still
publishes. Every app install subscribes to the topic below; each phone applies its own Settings switches.
"""
import argparse, json, os, sys, time
from datetime import datetime, timezone

TOPIC = "cw_alerts"
MAX_PER_RUN = 20
MAX_AGE_S = 3 * 24 * 3600
FIELDS = ["id", "type", "title", "message", "source", "timestamp", "priority", "projectId", "signalId", "address"]


def load(path):
    if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def age_seconds(ts):
    try:
        s = str(ts).strip()
        if s.isdigit():
            t = int(s) / (1000 if int(s) > 100_000_000_000 else 1)
        else:
            t = datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
        return time.time() - t
    except Exception:
        return 0


def new_alerts(old, new):
    known = {a.get("id") for a in old.get("alerts", [])}
    fresh = [a for a in new.get("alerts", []) if a.get("id") and a["id"] not in known]
    return [a for a in fresh if age_seconds(a.get("timestamp")) < MAX_AGE_S][:MAX_PER_RUN]


def access_token(info):
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/firebase.messaging"])
    creds.refresh(Request())
    return creds.token


def send(project_id, token, alert):
    import requests
    data = {k: str(alert[k]) for k in FIELDS if alert.get(k) is not None}
    body = {"message": {"topic": TOPIC, "data": data, "android": {"priority": "HIGH", "ttl": "86400s"}}}
    r = requests.post(
        f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(body), timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"FCM HTTP {r.status_code}: {r.text[:300]}")
    return r.json().get("name")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--test", help="send a delivery test with this title")
    ap.add_argument("--project", help="optional projectId the test notification opens")
    args = ap.parse_args()

    if args.test:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        alerts = [{
            "id": f"push-test-{int(time.time())}", "type": "TEST", "title": args.test,
            "message": "Real-time push delivery check from the cryptowatch-feed repository.",
            "source": "Crypto Watch push test", "timestamp": now, "priority": "HIGH",
            "projectId": args.project or None,
        }]
    else:
        alerts = new_alerts(load(args.old), load(args.new))

    if not alerts:
        print("No new alerts to push.")
        return 0

    raw = os.environ.get("FCM_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        print(f"::warning::{len(alerts)} new alert(s) not pushed: secret FCM_SERVICE_ACCOUNT_JSON is not set. "
              "The app still gets them on its next sync.")
        return 0

    info = json.loads(raw)
    token = access_token(info)
    failures = 0
    for a in alerts:
        try:
            print(f"pushed {a['id']} ({a.get('type')}): {send(info['project_id'], token, a)}")
        except Exception as e:
            failures += 1
            print(f"::error::push failed for {a.get('id')}: {e}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
