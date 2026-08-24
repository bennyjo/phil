#!/usr/bin/env python3
"""Cheap-model screening tier: rank scanned markets by price-vs-estimate gap.

PROTECTED CORE - the trading agent must not edit files under core/.

Why this exists (operator, 2026-08-24): frontier-model research reached ~3 of
~1,000 scanned markets per cycle, picked by intuition. Coverage, not depth, is
the binding constraint. This runs a cheap model over EVERY scanned candidate
and hands the agent a ranked shortlist. It ranks; it does not gate - the agent
may still research anything it likes.

Split of responsibilities, same shape as scan.py/discovery.py:
  * WHAT COUNTS AS A PROMISING GAP is the agent's: `strategy/screener-prompt.md`
    is the judgment brief sent to the model as a system block. The agent owns it
    under its normal evidence rules and can rewrite it as the screener's record
    accumulates.
  * THE MACHINERY stays here: batching, concurrency, the API contract, the
    output schema, cost accounting and the budget guard. A prompt edit cannot
    make this spend more, write elsewhere, or emit a different row shape.

If `strategy/screener-prompt.md` is missing or unreadable this falls back to a
short built-in brief and says so loudly on stderr - a broken judgment file
degrades ranking, it never silently stops the screen.

Two things this deliberately does NOT do:
  * It NEVER writes journal/forecasts.jsonl. Screener probabilities are cheap
    triage guesses, not honest researched beliefs; letting them near the
    forecast ledger would corrupt brier_delta and violate CYCLE.md's
    "never invent an estimate" rule. Screener output lives only in
    journal/screener.jsonl, which nothing else writes.
  * It never places, sizes or vetoes anything. It emits a reading list.

Divergence caveat: `outcome_prices` come from gamma's market record - they are
STALE MIDS, not fillable prices. A large divergence means "worth a look", not
"tradeable edge"; the live book (spread, depth) is still checked downstream by
the normal research path before any bet.

Usage:
  python3 core/scan.py | python3 core/screen.py          # normal cycle use
  python3 core/screen.py --file candidates.jsonl
  python3 core/screen.py --dry-run                       # contract check, no API
Input:  scan.py candidate JSON lines on stdin or --file.
Output: top-N rows (by divergence) as JSON lines on stdout; one row per
        screened market appended to journal/screener.jsonl; a summary on stderr.

Key: env ANTHROPIC_API_KEY, else ~/.config/phil/anthropic-api-key. NEVER store
the key in the repo - journal and strategy are public.

Budget: cost is computed from the response's own usage counters at the Haiku
pricing constants below and accumulated per UTC day in
journal/screener-quota.json - committed, so spend is public and survives
container churn. Once the day's spend reaches the budget this exits 0 before
any API call: an exhausted budget must degrade the cycle, never kill it.
`daily_budget_usd` is a tunable in config/protected.json; MAX_DAILY_BUDGET_USD
here is the hard ceiling it is clamped to, so a config edit alone cannot raise
spend past it (core/validate.py enforces the same ceiling in CI).

The agent may call this freely but may not edit it; if the batching, the row
schema or the budget guard are wrong, that is a journal/proposals.md entry.
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTECTED = json.loads((ROOT / "config" / "protected.json").read_text())
PROMPT_FILE = ROOT / "strategy" / "screener-prompt.md"
LOG_FILE = ROOT / "journal" / "screener.jsonl"
QUOTA_FILE = ROOT / "journal" / "screener-quota.json"
KEY_FILE = pathlib.Path.home() / ".config" / "phil" / "anthropic-api-key"

MAX_WORKERS = 8
HTTP_TIMEOUT_S = 60
RETRIES = 3
BACKOFF_S = 2.0
MAX_RETRY_SLEEP_S = 60.0
MAX_TOKENS_PER_MARKET = 200
MAX_TOKENS_CEILING = 8000

# Hard ceiling on the config tunable. Raising it is a protected-core edit, by
# design - same story as REAL_HARD_CEILINGS in core/validate.py.
MAX_DAILY_BUDGET_USD = 20.0

# Claude Haiku 4.5 list price, USD per million tokens (2026-08-24). Cache
# writes are 1.25x base input for the default 5-minute TTL, cache reads 0.1x.
# NOTE: Haiku 4.5's minimum cacheable prefix is 4096 tokens - a short system
# prefix silently does not cache (both cache counters stay 0) and everything is
# billed at PRICE_IN. The cache columns are logged so that is visible.
PRICE_IN = 1.00
PRICE_OUT = 5.00
PRICE_CACHE_WRITE = 1.25
PRICE_CACHE_READ = 0.10

SCREENER_DEFAULTS = {"model": "claude-haiku-4-5", "batch_size": 20,
                     "top_n": 15, "daily_budget_usd": 5.0}

CONFIDENCES = {"low", "medium", "high"}

REQUIRED_INPUT_FIELDS = ("market_id", "question", "outcomes", "outcome_prices")

# Stable across every request and every cycle - no timestamps, no counts, no
# per-batch text. This is the cached prefix; any byte that varies here costs
# the whole system block its cache entry.
PREAMBLE = """You are the screening tier of a prediction-market research \
pipeline. You are shown a batch of live Polymarket markets. For each one, give \
your quick honest probability for every outcome, how confident you are, and one \
line of reasoning.

You are NOT deciding trades. A downstream researcher spends real effort on the \
markets whose probabilities differ most from the market price, so your job is \
to be honestly calibrated and honestly uncertain - both a falsely confident \
number and a lazy echo of the market price waste that effort.

Rules:
- Probabilities for a market's outcomes must be non-negative and sum to about 1.
- The prices you are shown are stale mids. Do not copy them. If after thinking \
you genuinely agree with the price, say so with your own number and let the \
divergence be small.
- Use only what you already know plus the market text. You cannot browse. If \
resolving the question needs information you do not have, that is exactly what \
confidence "low" is for - say so in the reason.
- confidence "high" means you would defend the number without further research.

Output ONLY a JSON array, one object per market in the batch, no prose and no \
code fences:
[{"market_id": "<id as given>", "prob": {"<outcome name>": <0-1>, ...}, \
"confidence": "low"|"medium"|"high", "reason": "<one short line>"}]

Use the exact outcome names given for that market. Include every market in the \
batch exactly once."""

DEFAULT_BRIEF = """(built-in fallback brief - strategy/screener-prompt.md was \
unreadable)

Rank for research-worthiness, not for certainty. A large gap on a liquid, \
well-defined market is worth more than a large gap on a thin or exotic one, \
where the gap is usually your own ignorance. Be skeptical of your own \
confidence on questions whose resolution source you cannot name. Known traps: \
questions whose numbers read as already-settled for an event that has not \
happened; provisional figures repeated by many outlets (that is one source, \
not many); two different surveys reported on the same scale being treated as \
interchangeable."""

_lock = threading.Lock()
_fatal = []


class FatalAPIError(RuntimeError):
    """A request the API will reject the same way every time (key, model, shape)."""


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key and KEY_FILE.is_file():
        key = KEY_FILE.read_text().strip()
    if not key:
        sys.exit("ERROR: no ANTHROPIC_API_KEY in env and no "
                 "~/.config/phil/anthropic-api-key.\n"
                 "Operator has not provisioned the key on this runner - note "
                 "'screener key not provisioned' in the cycle log, research "
                 "unscreened candidates as before; do not work around.")
    return key


def screener_config():
    cfg = PROTECTED.get("screener")
    if not isinstance(cfg, dict):
        print("screen: config/protected.json has no 'screener' block; "
              "using built-in defaults", file=sys.stderr)
        cfg = {}
    out = dict(SCREENER_DEFAULTS)
    for k, v in SCREENER_DEFAULTS.items():
        got = cfg.get(k)
        if isinstance(got, type(v)) or (isinstance(v, float)
                                        and isinstance(got, (int, float))
                                        and not isinstance(got, bool)):
            out[k] = got
    budget = float(out["daily_budget_usd"])
    if budget > MAX_DAILY_BUDGET_USD:
        print(f"screen: daily_budget_usd {budget} exceeds the protected ceiling "
              f"{MAX_DAILY_BUDGET_USD}; clamping", file=sys.stderr)
        budget = MAX_DAILY_BUDGET_USD
    out["daily_budget_usd"] = budget
    return out


def load_brief():
    """Return (brief_text, prompt_rev). prompt_rev is 'default' on fallback."""
    try:
        text = PROMPT_FILE.read_text().strip()
        if not text:
            raise ValueError("file is empty")
    except Exception as e:  # noqa: BLE001 - any failure falls back, loudly
        print(f"screen: strategy/screener-prompt.md unusable "
              f"({type(e).__name__}: {e}); falling back to the built-in brief - "
              f"screening judgment is degraded until it is fixed", file=sys.stderr)
        return DEFAULT_BRIEF, "default"
    return text, blob_rev(PROMPT_FILE)


def blob_rev(path):
    """Git blob hash of the bytes actually sent, or 'unknown' outside a repo.

    `git hash-object` rather than `git rev-parse HEAD:<path>` on purpose: this
    log is the future training set, so the revision recorded must identify the
    exact text used, including an agent edit that has not been committed yet.
    For a clean working tree the two are the same hash.
    """
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "hash-object", "--", str(path)],
                             capture_output=True, text=True, timeout=10, check=True)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 - provenance is nice-to-have, never fatal
        return "unknown"


def load_quota():
    if QUOTA_FILE.is_file():
        try:
            q = json.loads(QUOTA_FILE.read_text())
            if q.get("day") == today():
                return q
        except json.JSONDecodeError as e:
            print(f"screen: journal/screener-quota.json unreadable ({e}); "
                  f"treating today as unspent", file=sys.stderr)
    return {"day": today(), "spent_usd": 0.0, "calls": 0, "markets_screened": 0,
            "input_tokens": 0, "output_tokens": 0, "last_request_utc": None}


def save_quota(q):
    QUOTA_FILE.write_text(json.dumps(q, indent=2) + "\n")


def read_candidates(path):
    """Parse scan.py JSON lines. Returns (valid, n_bad); never raises on input."""
    if path:
        raw = pathlib.Path(path).read_text()
    else:
        raw = sys.stdin.read()
    valid, bad = [], 0
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            c = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"screen: input line {lineno}: invalid JSON ({e}); skipped",
                  file=sys.stderr)
            bad += 1
            continue
        missing = [f for f in REQUIRED_INPUT_FIELDS if c.get(f) in (None, "", [])]
        if missing or not isinstance(c.get("outcomes"), list) \
                or not isinstance(c.get("outcome_prices"), list):
            print(f"screen: input line {lineno}: not a scan candidate "
                  f"(missing/!list {missing or 'outcomes/outcome_prices'}); skipped",
                  file=sys.stderr)
            bad += 1
            continue
        valid.append(c)
    return valid, bad


def mids_of(c):
    """outcome name -> stale gamma mid, for the outcomes that have a price."""
    out = {}
    for name, price in zip(c.get("outcomes") or [], c.get("outcome_prices") or []):
        try:
            out[str(name)] = float(price)
        except (TypeError, ValueError):
            continue
    return out


def brief_of(c):
    """The per-market payload sent to the model. Kept small - 1,000 of these."""
    return {
        "market_id": str(c.get("market_id")),
        "question": c.get("question"),
        "outcomes": [str(o) for o in (c.get("outcomes") or [])],
        "market_prices": mids_of(c),
        "end_date": c.get("end_date"),
        "volume_24h": round(float(c.get("volume_24h") or 0)),
        "liquidity": round(float(c.get("liquidity") or 0)),
        "description": (c.get("description") or "")[:400],
    }


def chunk(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def retry_after_s(headers):
    try:
        return float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None


def anthropic_post(payload, key):
    """POST /v1/messages with backoff. Raises FatalAPIError on non-retryables."""
    body = json.dumps(payload).encode()
    headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION,
               "content-type": "application/json"}
    last = None
    for attempt in range(RETRIES):
        req = urllib.request.Request(API_URL, data=body, headers=headers,
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code != 429 and e.code < 500:
                # 400/401/403/404 repeat identically - bad key, bad model id,
                # bad request shape. Stop the whole run rather than fill the
                # journal with one error row per market.
                raise FatalAPIError(f"HTTP {e.code}: {detail}") from e
            last = f"HTTP {e.code}: {detail}"
            sleep_s = retry_after_s(e.headers) or BACKOFF_S * (2 ** attempt)
        except Exception as e:  # noqa: BLE001 - transport hiccup, retry
            last = f"{type(e).__name__}: {e}"
            sleep_s = BACKOFF_S * (2 ** attempt)
        if attempt == RETRIES - 1:
            break
        time.sleep(min(sleep_s, MAX_RETRY_SLEEP_S))
    raise RuntimeError(f"POST {API_URL} failed after {RETRIES} tries: {last}")


def response_text(resp):
    return "".join(b.get("text", "") for b in (resp.get("content") or [])
                   if isinstance(b, dict) and b.get("type") == "text")


def parse_answers(text):
    """Model text -> {market_id: answer}. Raises ValueError if unparseable."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
        t = t.strip()
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("["), t.rfind("]")
        if start < 0 or end <= start:
            raise ValueError("no JSON array in model response") from None
        data = json.loads(t[start:end + 1])
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError(f"model returned {type(data).__name__}, not a list")
    out = {}
    for item in data:
        if isinstance(item, dict) and item.get("market_id") is not None:
            out[str(item["market_id"])] = item
    return out


def cost_of(usage):
    n_in = int(usage.get("input_tokens") or 0)
    n_out = int(usage.get("output_tokens") or 0)
    n_write = int(usage.get("cache_creation_input_tokens") or 0)
    n_read = int(usage.get("cache_read_input_tokens") or 0)
    usd = (n_in * PRICE_IN + n_out * PRICE_OUT + n_write * PRICE_CACHE_WRITE
           + n_read * PRICE_CACHE_READ) / 1e6
    return usd, n_in + n_write + n_read, n_out


def row_base(c, ts, model, prompt_rev, batch_id):
    return {"ts": ts, "market_id": str(c.get("market_id")),
            "question": c.get("question"), "model": model,
            "prompt_rev": prompt_rev, "probs": None, "mids": mids_of(c),
            "divergence": None, "confidence": None, "reason": None,
            "batch_id": batch_id, "input_tokens": 0, "output_tokens": 0,
            "cost_usd": 0.0}


def grade_answer(row, answer):
    """Fill probs/divergence/confidence/reason, or set screen_error. No raises."""
    if not isinstance(answer, dict):
        row["screen_error"] = "no answer for this market in the batch response"
        return row
    probs, mids = {}, row["mids"]
    raw = answer.get("prob")
    if not isinstance(raw, dict) or not raw:
        row["screen_error"] = f"prob is not a non-empty object ({type(raw).__name__})"
        return row
    for name, p in raw.items():
        try:
            p = float(p)
        except (TypeError, ValueError):
            continue
        if 0.0 <= p <= 1.0:
            probs[str(name)] = p
    if not probs:
        row["screen_error"] = "no outcome probability in [0, 1]"
        return row
    row["probs"] = probs
    shared = set(probs) & set(mids)
    if not shared:
        row["screen_error"] = ("model outcome names match none of the market's "
                               f"outcomes ({sorted(probs)} vs {sorted(mids)})")
        return row
    row["divergence"] = round(max(abs(probs[o] - mids[o]) for o in shared), 4)
    conf = answer.get("confidence")
    row["confidence"] = conf if conf in CONFIDENCES else "unknown"
    reason = answer.get("reason")
    row["reason"] = str(reason)[:300] if reason is not None else None
    return row


def screen_batch(batch, batch_id, key, cfg, brief, prompt_rev, budget_state):
    """One API call over `batch`. Returns (rows, spend_usd, called)."""
    ts = iso(utcnow())
    rows = [row_base(c, ts, cfg["model"], prompt_rev, batch_id) for c in batch]

    with _lock:
        if _fatal:
            return [], 0.0, False
        if budget_state["spent"] >= budget_state["budget"]:
            return [], 0.0, False

    payload = {
        "model": cfg["model"],
        "max_tokens": min(MAX_TOKENS_CEILING, MAX_TOKENS_PER_MARKET * len(batch)),
        "temperature": 0,
        "system": [
            {"type": "text", "text": PREAMBLE},
            # The breakpoint sits on the LAST system block so the cached prefix
            # covers the preamble AND the judgment brief. Both are stable for
            # the whole run; marking only the preamble would leave the brief
            # billed at full price on every batch.
            {"type": "text", "text": brief,
             "cache_control": {"type": "ephemeral"}},
        ],
        "messages": [{"role": "user", "content": json.dumps(
            {"markets": [brief_of(c) for c in batch]}, ensure_ascii=False)}],
    }

    try:
        resp = anthropic_post(payload, key)
    except FatalAPIError as e:
        with _lock:
            _fatal.append(str(e))
        return [], 0.0, False
    except RuntimeError as e:
        for row in rows:
            row["screen_error"] = f"api call failed: {e}"
        return rows, 0.0, False

    spend, n_in, n_out = cost_of(resp.get("usage") or {})
    with _lock:
        budget_state["spent"] += spend
    share_in = round(n_in / len(batch))
    share_out = round(n_out / len(batch))
    share_cost = round(spend / len(batch), 8)
    for row in rows:
        row["input_tokens"] = share_in
        row["output_tokens"] = share_out
        row["cost_usd"] = share_cost

    try:
        answers = parse_answers(response_text(resp))
    except (ValueError, json.JSONDecodeError) as e:
        for row in rows:
            row["screen_error"] = f"unparseable batch response: {e}"
        return rows, spend, True

    return ([grade_answer(row, answers.get(row["market_id"])) for row in rows],
            spend, True)


def dry_run(candidates, cfg, prompt_rev, brief):
    batches = chunk(candidates, cfg["batch_size"])
    # ~4 chars per token, plus the fixed system prefix on every call.
    prefix_tok = (len(PREAMBLE) + len(brief)) / 4
    est_in = sum(prefix_tok + len(json.dumps({"markets": [brief_of(c) for c in b]})) / 4
                 for b in batches)
    est_out = 60 * len(candidates)
    est_cost = (est_in * PRICE_IN + est_out * PRICE_OUT) / 1e6
    q = load_quota()
    print(json.dumps({
        "dry_run": True, "candidates": len(candidates), "batches": len(batches),
        "batch_size": cfg["batch_size"], "top_n": cfg["top_n"],
        "model": cfg["model"], "prompt_rev": prompt_rev,
        "est_input_tokens": round(est_in), "est_output_tokens": est_out,
        "est_cost_usd": round(est_cost, 4),
        "day_spent_usd": round(float(q.get("spent_usd") or 0), 4),
        "daily_budget_usd": cfg["daily_budget_usd"],
        "sample_market_ids": [str(c.get("market_id")) for c in candidates[:5]],
    }, indent=2))
    print(f"screen: dry run - would screen {len(candidates)} markets in "
          f"{len(batches)} batches for about ${est_cost:.2f}; nothing written",
          file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=None,
                    help="read scan candidates from this file instead of stdin")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate the input contract and estimate cost; no API "
                         "calls, nothing written")
    ap.add_argument("--batch-size", type=int, default=None,
                    help="override config screener.batch_size")
    ap.add_argument("--top-n", type=int, default=None,
                    help="override config screener.top_n")
    args = ap.parse_args()

    cfg = screener_config()
    if args.batch_size is not None:
        cfg["batch_size"] = max(1, args.batch_size)
    if args.top_n is not None:
        cfg["top_n"] = max(1, args.top_n)

    candidates, n_bad = read_candidates(args.file)
    if n_bad:
        print(f"screen: {n_bad} input line(s) failed the candidate contract",
              file=sys.stderr)
    if not candidates:
        print("screen: no valid candidates on input; nothing to screen",
              file=sys.stderr)
        return 0

    brief, prompt_rev = load_brief()

    if args.dry_run:
        dry_run(candidates, cfg, prompt_rev, brief)
        return 0

    quota = load_quota()
    day_spent = float(quota.get("spent_usd") or 0.0)
    if day_spent >= cfg["daily_budget_usd"]:
        print(f"screen: daily screener budget exhausted "
              f"(${day_spent:.2f} / ${cfg['daily_budget_usd']:.2f}, UTC day "
              f"{quota['day']}) - screening skipped, no API call made. Research "
              f"unscreened candidates as before and log 'screener budget "
              f"exhausted'; do not work around.", file=sys.stderr)
        return 0

    key = api_key()
    batches = chunk(candidates, cfg["batch_size"])
    budget_state = {"spent": 0.0, "budget": cfg["daily_budget_usd"] - day_spent}

    rows, calls = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(screen_batch, b, f"{iso(utcnow())}-{i}", key, cfg,
                               brief, prompt_rev, budget_state)
                   for i, b in enumerate(batches)]
        for fut in concurrent.futures.as_completed(futures):
            got, _spend, called = fut.result()
            rows.extend(got)
            calls += 1 if called else 0

    spent = budget_state["spent"]
    if rows:
        with LOG_FILE.open("a") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
    if calls:
        quota["spent_usd"] = round(day_spent + spent, 8)
        quota["calls"] = int(quota.get("calls") or 0) + calls
        quota["markets_screened"] = int(quota.get("markets_screened") or 0) + len(rows)
        quota["input_tokens"] = int(quota.get("input_tokens") or 0) + \
            sum(r["input_tokens"] for r in rows)
        quota["output_tokens"] = int(quota.get("output_tokens") or 0) + \
            sum(r["output_tokens"] for r in rows)
        quota["last_request_utc"] = iso(utcnow())
        save_quota(quota)

    if _fatal:
        print(f"screen: ABORTED - the API rejected the request and will keep "
              f"rejecting it: {_fatal[0]}\n"
              f"screen: check screener.model in config/protected.json and the "
              f"ANTHROPIC_API_KEY on this runner. {len(rows)} row(s) logged.",
              file=sys.stderr)
        return 1

    ranked = sorted((r for r in rows if r.get("divergence") is not None),
                    key=lambda r: r["divergence"], reverse=True)
    escalated = ranked[:cfg["top_n"]]
    for row in escalated:
        print(json.dumps(row))

    n_err = sum(1 for r in rows if r.get("screen_error"))
    if n_err:
        print(f"screen: {n_err} market(s) came back malformed (see screen_error "
              f"in journal/screener.jsonl)", file=sys.stderr)
    day_total = day_spent + spent
    print(f"screen: screened {len(rows)} markets in {calls} batches, "
          f"escalated {len(escalated)}, spent ${spent:.4f}, day total "
          f"${day_total:.4f} / ${cfg['daily_budget_usd']:.2f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
