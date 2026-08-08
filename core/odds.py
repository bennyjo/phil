#!/usr/bin/env python3
"""Keyed bookmaker odds + event status via the-odds-api.com (operator-owned).

Provisioned 2026-08-08 after the 2026-08-04 reachability rejection's re-open
condition was met: a week of cycles attributed skipped candidates to
benchmark/status unreachability (15/35 candidates in the 2026-08-08 deep-retro
window alone), while book-devig — the only edge class with a positive settled
record post-power-devig-fix — stayed starved. This replaces scraping the ~20
odds domains that 403 datacenter IPs.

Usage:
  python3 core/odds.py sports                  # list in-season sport keys (quota-free)
  python3 core/odds.py odds <sport_key> [--markets h2h] [--region us]
  python3 core/odds.py scores <sport_key> [--days-from N]
  python3 core/odds.py quota                   # show monthly budget state

Key: env ODDS_API_KEY, else ~/.config/phil/odds-api-key. NEVER store the key
in the repo — journal and strategy are public.

Quota: free tier is 500 credits/month. This tool hard-refuses once
LOCAL_BUDGET credits are recorded for the current month (buffer for header
lag and out-of-band use), tracked in journal/odds-quota.json — committed, so
spend is public and survives runner churn. The API's own
x-requests-used/remaining headers are authoritative and overwrite the local
estimate whenever present. Identical requests within CACHE_TTL_S are served
from cache and spend nothing, so re-running a command mid-cycle is free.

Costs (per the-odds-api docs): /sports is free; /odds costs regions x
markets per call (defaults here: 1 x 1 = 1 credit); /scores costs 1, or 2
with --days-from. Odds are returned in DECIMAL format — feed them straight
to strategy/tools/devig.py.

The agent may call this freely but may not edit it; if the budget guard or
defaults are wrong, that is a journal/proposals.md entry.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.the-odds-api.com/v4"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
QUOTA_FILE = REPO_ROOT / "journal" / "odds-quota.json"
KEY_FILE = pathlib.Path.home() / ".config" / "phil" / "odds-api-key"
CACHE_DIR = pathlib.Path.home() / ".cache" / "phil-odds"
CACHE_TTL_S = 600
LOCAL_BUDGET = 450  # hard local stop under the 500/month free tier

# Same TLS-fingerprint story as strategy/tools/quote.py: urllib first, curl
# fallback on any failure — datacenter blocks are the whole reason this tool
# exists, so never let a transport quirk masquerade as "no key/no quota".
UA = "Mozilla/5.0 (compatible; paper-trader-odds)"


def api_key():
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key and KEY_FILE.is_file():
        key = KEY_FILE.read_text().strip()
    if not key:
        sys.exit("ERROR: no ODDS_API_KEY in env and no ~/.config/phil/odds-api-key.\n"
                 "Operator has not provisioned the key on this runner — note "
                 "'odds key not provisioned' in the cycle log; do not work around.")
    return key


def month_now():
    return time.strftime("%Y-%m", time.gmtime())


def load_quota():
    if QUOTA_FILE.is_file():
        q = json.loads(QUOTA_FILE.read_text())
        if q.get("month") == month_now():
            return q
    return {"month": month_now(), "used_credits": 0, "remaining_reported": None,
            "last_request_utc": None}


def save_quota(q):
    QUOTA_FILE.write_text(json.dumps(q, indent=2) + "\n")


def cache_path(url):
    return CACHE_DIR / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")


def fetch(url):
    """GET url (key already in query string). Returns (body_dict_or_list, headers)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode()), dict(resp.headers)
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 422):
            sys.exit(f"ERROR: the-odds-api rejected the request ({exc.code}): "
                     f"{exc.read().decode()[:300]}")
        out = subprocess.run(
            ["curl", "-s", "--max-time", "20", "-D", "-", "-H", f"User-Agent: {UA}", url],
            capture_output=True, text=True, timeout=25, check=True,
        )
        head, _, body = out.stdout.partition("\r\n\r\n")
        if not body:
            head, _, body = out.stdout.partition("\n\n")
        headers = {}
        for line in head.splitlines()[1:]:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()
        return json.loads(body), headers


def spend_guarded(path, params, cost):
    """Cached, quota-guarded GET of API_BASE+path. Exits before spending if over budget."""
    q = load_quota()
    key = api_key()
    params = {**params, "apiKey": key}
    url = f"{API_BASE}{path}?{urllib.parse.urlencode(params)}"

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cp = cache_path(url)
    if cp.is_file() and time.time() - cp.stat().st_mtime < CACHE_TTL_S:
        return json.loads(cp.read_text())

    if cost > 0 and q["used_credits"] + cost > LOCAL_BUDGET:
        sys.exit(f"ERROR: monthly odds-API budget exhausted "
                 f"({q['used_credits']}/{LOCAL_BUDGET} local cap, month {q['month']}). "
                 "Log 'odds budget exhausted' and skip — do not work around.")

    body, headers = fetch(url)
    headers = {k.lower(): v for k, v in headers.items()}
    q["used_credits"] += cost
    used = headers.get("x-requests-used")
    remaining = headers.get("x-requests-remaining")
    if used is not None:
        try:
            q["used_credits"] = int(float(used))
        except ValueError:
            pass
    if remaining is not None:
        try:
            q["remaining_reported"] = int(float(remaining))
        except ValueError:
            pass
    q["last_request_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    save_quota(q)

    cp.write_text(json.dumps(body))
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sports")
    ap_odds = sub.add_parser("odds")
    ap_odds.add_argument("sport_key")
    ap_odds.add_argument("--markets", default="h2h",
                         help="comma-separated: h2h,spreads,totals (each adds 1 credit)")
    ap_odds.add_argument("--region", default="us")
    ap_scores = sub.add_parser("scores")
    ap_scores.add_argument("sport_key")
    ap_scores.add_argument("--days-from", type=int, default=None,
                           help="include games completed up to N days ago (costs 2 instead of 1)")
    sub.add_parser("quota")
    args = ap.parse_args()

    if args.cmd == "quota":
        q = load_quota()
        q["local_cap"] = LOCAL_BUDGET
        print(json.dumps(q, indent=2))
        return

    if args.cmd == "sports":
        body = spend_guarded("/sports", {}, cost=0)
    elif args.cmd == "odds":
        n_markets = len([m for m in args.markets.split(",") if m])
        n_regions = len([r for r in args.region.split(",") if r])
        body = spend_guarded(
            f"/sports/{args.sport_key}/odds",
            {"regions": args.region, "markets": args.markets, "oddsFormat": "decimal"},
            cost=n_markets * n_regions)
    else:
        params, cost = {}, 1
        if args.days_from is not None:
            params["daysFrom"] = args.days_from
            cost = 2
        body = spend_guarded(f"/sports/{args.sport_key}/scores", params, cost=cost)

    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()
