#!/usr/bin/env python3
"""Headline Arena daily questions: an external score the loop cannot touch.

PROTECTED CORE - the trading agent must not edit files under core/.

Headline Arena (headlinearena.com, API docs at /api/docs) posts one daily
question per futures asset (GC gold, SI silver, CL crude, ES S&P 500, ZN
10-year note, NG, HG, ...): will the price close the window above +X%,
below -X%, or inside the dead zone, versus the session open. Criteria are
frozen at creation, settlement is mechanical, and every forecast is
Brier-scored in public. Phil's own scoring lives in this repo, which the
agent rewrites every cycle; this score lives somewhere it cannot.

Off until the operator provisions credentials (see operator-notes
2026-10-13). With none, every command prints {"enabled": false} and exits 0.

Usage:
  python3 core/headline_arena.py open
      today's open daily questions (public read)
  python3 core/headline_arena.py submit --challenge ID --forecast-id FID \\
      --bearish P --neutral P --bullish P
      one probability vector on one open daily question
  python3 core/headline_arena.py score
      the agent's Headline Arena scorecard and calibration (public reads)

What leaves the repo: the three probabilities and nothing else. No
reasoning, summary, stake or forecast_context is ever sent, so nothing
about Phil's positions or money reaches Headline Arena. Only questions of
challenge_type "daily" are accepted, and only when --forecast-id names a
forecast row recorded today: the vector must come out of research the
cycle already did on that asset's underlying.

Credentials: env HEADLINE_ARENA_AGENT_ID + HEADLINE_ARENA_CLIENT_SECRET,
else ~/.config/phil/headline-arena.json {"agent_id": ..., "client_secret":
...}. NEVER store them in the repo - journal and strategy are public.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
import uuid

API_BASE = "https://headlinearena.com/api/v1"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FORECASTS = REPO_ROOT / "journal" / "forecasts.jsonl"
CRED_FILE = pathlib.Path.home() / ".config" / "phil" / "headline-arena.json"
UA = "phil-headline-arena/1"
OUTCOMES = ("bearish", "neutral", "bullish")


def credentials():
    """(agent_id, client_secret), or None when the operator has not opted in."""
    agent_id = os.environ.get("HEADLINE_ARENA_AGENT_ID", "").strip()
    secret = os.environ.get("HEADLINE_ARENA_CLIENT_SECRET", "").strip()
    if not (agent_id and secret) and CRED_FILE.is_file():
        c = json.loads(CRED_FILE.read_text())
        agent_id = str(c.get("agent_id", "")).strip()
        secret = str(c.get("client_secret", "")).strip()
    return (agent_id, secret) if agent_id and secret else None


def request(method, path, body=None, token=None, agent_id=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if agent_id:
        headers["X-Agent-Id"] = agent_id
        headers["X-Request-Id"] = uuid.uuid4().hex
    req = urllib.request.Request(API_BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        sys.exit(f"ERROR: Headline Arena {method} {path} -> {exc.code}: "
                 f"{exc.read().decode()[:300]}")


def token(agent_id, secret):
    return request("POST", "/agent/auth/token", {
        "grant_type": "client_credentials", "agent_id": agent_id,
        "client_secret": secret})["access_token"]


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def parse_ts(s):
    s = s[:-1] if s.endswith("Z") else s
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def is_open_daily(c, now):
    return (c.get("challenge_type") == "daily" and c.get("status") == "open"
            and parse_ts(c["deadline"]) > now)


def vector(bearish, neutral, bullish):
    """Validate and round so the three probabilities sum to exactly 1."""
    p = {"bearish": bearish, "neutral": neutral, "bullish": bullish}
    if any(v < 0 or v > 1 for v in p.values()):
        sys.exit("ERROR: each probability must be in [0, 1]")
    total = sum(p.values())
    if abs(total - 1) > 0.01:
        sys.exit(f"ERROR: probabilities sum to {total:.4f}, not 1")
    p = {k: round(v / total, 4) for k, v in p.items()}
    top = max(p, key=p.get)  # absorb the rounding remainder in the largest
    p[top] = round(1 - sum(v for k, v in p.items() if k != top), 4)
    return p


def forecast_today(fid, now):
    for line in FORECASTS.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("id") == fid:
                return r["ts"][:10] == now.strftime("%Y-%m-%d")
    return False


def cmd_open():
    now = now_utc()
    items = request("GET", "/eval/challenges?status=open&limit=100")["items"]
    keep = ("id", "asset", "contract_name", "exchange", "open_price",
            "dead_zone_pct", "deadline", "resolve_at", "resolution_criteria")
    return {"enabled": True, "challenges": [
        {k: c.get(k) for k in keep} for c in items if is_open_daily(c, now)]}


def cmd_submit(creds, a):
    now = now_utc()
    if not forecast_today(a.forecast_id, now):
        sys.exit(f"ERROR: --forecast-id {a.forecast_id} is not a forecast row recorded "
                 "today; submit only on an asset this cycle researched")
    c = request("GET", f"/eval/challenges/{a.challenge}")
    if not is_open_daily(c, now):
        sys.exit(f"ERROR: challenge {a.challenge} is not an open daily question "
                 f"(type {c.get('challenge_type')}, status {c.get('status')}, "
                 f"deadline {c.get('deadline')})")
    p = vector(a.bearish, a.neutral, a.bullish)
    agent_id, secret = creds
    resp = request("POST", f"/eval/challenges/{a.challenge}/predict",
                   {"probabilities": p, "idempotency_key": f"phil-{a.challenge}"},
                   token=token(agent_id, secret), agent_id=agent_id)
    return {"enabled": True, "asset": c.get("asset"), "challenge_id": a.challenge,
            "forecast_id": a.forecast_id, "probabilities": p,
            "prediction_id": resp.get("prediction_id"),
            "counts_for_score": resp.get("counts_for_score"), "note": resp.get("note")}


def cmd_score(creds):
    agent_id = creds[0]
    return {"enabled": True, "agent_id": agent_id,
            "scorecard": request("GET", f"/eval/agents/{agent_id}/scorecard"),
            "calibration": request("GET", f"/eval/agents/{agent_id}/calibration")}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("open")
    s = sub.add_parser("submit")
    s.add_argument("--challenge", required=True)
    s.add_argument("--forecast-id", required=True)
    for o in OUTCOMES:
        s.add_argument(f"--{o}", type=float, required=True)
    sub.add_parser("score")
    a = ap.parse_args(argv)

    creds = credentials()
    if creds is None:
        out = {"enabled": False, "why": "no Headline Arena credentials on this runner; "
               "skip the step, do not work around"}
    elif a.cmd == "open":
        out = cmd_open()
    elif a.cmd == "submit":
        out = cmd_submit(creds, a)
    else:
        out = cmd_score(creds)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
