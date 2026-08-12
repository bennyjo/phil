#!/usr/bin/env python3
"""Report the CI verdict for the latest pushed commits (read-only probe).

PROTECTED (operator-owned). Queries GitHub's public check-runs API for
origin/main's tip, falling back one commit when the tip's checks have not
completed yet, and prints a single JSON line. It must never crash a cycle:
any network or parsing trouble degrades to {"status": "unknown"}.

Usage:  python3 core/ci.py
Output: {"sha": "...", "ref": "...", "status": "success|failure|pending|none|unknown",
         "failed_checks": [{"name": "...", "url": "..."}]}

The cycle procedure (CYCLE.md step 0c) defines what the agent must do with
a "failure" verdict. This script only reports.
"""
import json
import re
import subprocess
import sys
import urllib.request

API = "https://api.github.com"
# Polymarket taught us the default Python-urllib UA gets 403s (quote.py,
# DEEP-2026-07-31); GitHub is friendlier but a real UA costs nothing.
HEADERS = {"User-Agent": "phil-ci-probe", "Accept": "application/vnd.github+json"}


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


def repo_slug():
    url = sh("git", "remote", "get-url", "origin")
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if not m:
        raise ValueError(f"cannot parse a GitHub slug from remote {url!r}")
    return f"{m.group(1)}/{m.group(2)}"


def check_runs(slug, sha):
    req = urllib.request.Request(
        f"{API}/repos/{slug}/commits/{sha}/check-runs", headers=HEADERS
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)["check_runs"]


def main():
    out = {"status": "unknown"}
    try:
        slug = repo_slug()
        for ref in ("origin/main", "origin/main~1"):
            sha = sh("git", "rev-parse", ref)
            runs = check_runs(slug, sha)
            if not runs:
                out = {"sha": sha, "ref": ref, "status": "none"}
                continue
            if any(r["status"] != "completed" for r in runs):
                out = {"sha": sha, "ref": ref, "status": "pending"}
                continue
            failed = [
                {"name": r["name"], "url": r["html_url"]}
                for r in runs
                if r["conclusion"] not in ("success", "neutral", "skipped")
            ]
            out = {
                "sha": sha,
                "ref": ref,
                "status": "failure" if failed else "success",
                "failed_checks": failed,
            }
            break
    except Exception as e:  # never kill the cycle over a status probe
        out = {"status": "unknown", "error": str(e)[:200]}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
