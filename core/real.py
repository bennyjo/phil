#!/usr/bin/env python3
"""Real-money execution via Pearl Connect — the only code that touches funds.

PROTECTED CORE — the trading agent must not edit files under core/.

Wraps the connect-polymarket skill scripts that Pearl Connect provisions
into its workspace. This file owns every real-money decision: caps, edge-
class gating, one-real-bet-per-market, the daily stake cap, and the
pending-order discipline (a buy is never idempotent — an ambiguous
submission blocks further real bets until a settle reconciles it).

The Safe is the treasury; the maker is the Polymarket DepositWallet; the
agent EOA signs through the local connect service. This wrapper never sees
key material — it shells out to the audited skill scripts.

journal/real-ledger.jsonl is append-only and written ONLY by this file.
Rows share an id; the last row per id wins (place appends a pending row
before submitting, then a result row after).

Binary Polymarket V2 markets trade through the same scripts as V1 ones, and
need Pearl Connect v0.1.13 or later and the V2 approvals (`doctor --setup`).
A V2 position lives in the Safe like a V1 one. Connect claims a winner through
the Router and skips a loser, so a loser stays in the Safe; settle reads the
official resolution to close its row, and lists under `unclaimed` a resolved
position with value that Connect did not claim. Phil records no payout: the
Router's payout is the pUSD transfer in the claim tx, not its event's amount.

Requires env PEARL_CONNECT_STORE = the Pearl Connect workspace path
(the directory containing .mcp.json). Optional CONNECT_POLYMARKET_VENV
overrides where Connect's bootstrap_env.sh keeps its venv.

Usage:
  python3 core/real.py doctor [--setup]
  python3 core/real.py place --paper-id <id> --usd 1.0
  python3 core/real.py settle
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import functools
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAPER_LEDGER = ROOT / "journal" / "ledger.jsonl"
REAL_LEDGER = ROOT / "journal" / "real-ledger.jsonl"
PROTECTED = ROOT / "config" / "protected.json"

HEALTHCHECK_URL = "http://127.0.0.1:8716/healthcheck"
SKILL_SCRIPTS = pathlib.Path(".claude") / "skills" / "connect-polymarket" / "scripts"
FEE_HEADROOM = 0.15  # top-up = stake * (1 + headroom); taker fee on $1 is cents
# A fill reaches the chain after the match, so settle gives an order this long
# before it reads an empty balance as "never filled" or "already claimed".
# Connect's own guidance for an uncertain placement is "after a minute or so".
RECONCILE_GRACE_S = 300
# What trade.py prints when a failed buy may still have been placed: an uncertain
# reply (the start and the end of one message, in case stderr's tail cuts the
# start), an auth failure mid-submission, or a crash (a traceback's frames).
AMBIGUOUS_BUY = ("placement uncertain", "check the chain", "may be ambiguous", 'File "')
# What trade.py prints when it proves a buy never reached the book: its checks
# before posting, then the CLOB's refusals of a fill-or-kill order.
REFUSED_BUY = ("no DepositWallet", "lists token", "holds no pUSD", "would be rejected",
               "couldn't be fully filled", "not enough balance", "not yet ready to process",
               "invalid nonce", "invalid expiration")


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}, indent=2))
    sys.exit(1)


def load_protected():
    cfg = json.loads(PROTECTED.read_text())
    if cfg.get("real_trading_enabled") is not True:
        fail("real_trading_enabled is not true in config/protected.json")
    real = cfg.get("real")
    if not isinstance(real, dict):
        fail("config/protected.json has no 'real' caps block")
    return cfg, real


def store_path():
    raw = os.environ.get("PEARL_CONNECT_STORE")
    if not raw:
        fail("PEARL_CONNECT_STORE is not set (the Pearl Connect workspace dir)")
    store = pathlib.Path(raw).expanduser()
    if not (store / ".mcp.json").exists():
        fail(f"{store}/.mcp.json not found — is Pearl Connect running and "
             f"PEARL_CONNECT_STORE correct?")
    return store


def healthy():
    """True only for the connect signer — every Pearl agent serves
    /healthcheck on 8716, but only connect's body is bare (a trader FSM
    also reports is_healthy=true and would otherwise false-positive)."""
    try:
        with urllib.request.urlopen(HEALTHCHECK_URL, timeout=3) as r:
            data = json.load(r)
        return bool(data.get("is_healthy")) and "rounds" not in data
    except Exception:
        return False


@functools.lru_cache(maxsize=None)
def skill_env(store):
    """(python, env) from Connect's own bootstrap_env.sh, which builds the venv
    with the SDK its scripts pin and exports the TLS trust store they need. Each
    Connect release's scripts need that release's pin, so Phil keeps no pin."""
    bootstrap = store / SKILL_SCRIPTS / "bootstrap_env.sh"
    if not bootstrap.exists():
        fail(f"{bootstrap} is missing - real mode needs Pearl Connect v0.1.13 "
             f"or later, which provisions it at boot")
    # bootstrap_env.sh prints shell assignments to eval, and reports its own
    # failure by printing a failing command.
    report = 'eval "$(bash "$0")" && printf "%s\n" "$PY" "$SSL_CERT_FILE" "$REQUESTS_CA_BUNDLE"'
    try:
        proc = subprocess.run(["bash", "-c", report, str(bootstrap)], cwd=store,
                              capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        fail("connect-polymarket bootstrap_env.sh timed out after 600s")
    if proc.returncode != 0 or not proc.stdout.strip():
        fail(f"connect-polymarket bootstrap_env.sh failed: {proc.stderr.strip()[-2000:]}")
    py, cert_file, ca_bundle = proc.stdout.split("\n")[:3]
    return py, {**os.environ, "SSL_CERT_FILE": cert_file, "REQUESTS_CA_BUNDLE": ca_bundle}


def run_script(store, name, *args, timeout=180):
    """Run a connect-polymarket skill script; returns (rc, stdout_json|None, stderr)."""
    script = store / SKILL_SCRIPTS / name
    if not script.exists():
        fail(f"skill script missing: {script} (Pearl Connect provisions it "
             f"at boot — is the connect agent running?)")
    py, env = skill_env(store)
    try:
        proc = subprocess.run([py, str(script), *map(str, args)],
                              cwd=store, env=env, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, None, f"{name} timed out after {timeout}s"
    out = None
    if proc.stdout.strip():
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            out = {"raw": proc.stdout.strip()[:2000]}
    return proc.returncode, out, proc.stderr.strip()[-2000:]


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def real_rows():
    """Last row per id, in first-seen order."""
    latest, order = {}, []
    for row in read_jsonl(REAL_LEDGER):
        rid = row.get("id")
        if rid not in latest:
            order.append(rid)
        latest[rid] = row
    return [latest[r] for r in order]


def append_real(row):
    REAL_LEDGER.parent.mkdir(exist_ok=True)
    with REAL_LEDGER.open("a") as f:
        f.write(json.dumps(row) + "\n")


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextlib.contextmanager
def ledger_lock():
    """Hold the real ledger's lock, so two place calls can't both pass the gates
    before either writes its pending row. The kernel drops it if this process
    dies. A second call waits for the first's status script, up to its timeout."""
    REAL_LEDGER.parent.mkdir(exist_ok=True)
    with REAL_LEDGER.open("a") as ledger:
        fcntl.flock(ledger, fcntl.LOCK_EX)
        yield


def buy_refused(rc, out, errtxt):
    """True only when trade.py's failure proves the order never reached the book.
    Anything else may have placed it, such as a signal kill (a negative exit), a
    crash, wording a later Connect release changed, or an `{"error": ...}` reply,
    which can report a timeout or a 4xx that arrived after the CLOB had the order.
    So it stays unknown until settle reads the chain. An unlisted refusal costs one
    blocked settle interval; a misfiled order costs a bet outside the caps."""
    if rc < 0 or any(mark in f"{errtxt} {out}" for mark in AMBIGUOUS_BUY):
        return False
    return any(mark in errtxt for mark in REFUSED_BUY)


def v2_approved(wallet_status):
    """True when `deposit_wallet.py status` shows every approval granted, V2's
    included. A Connect release without V2 support reports no PositionManager
    approvals, so this answers for the release as well as for the wallet."""
    approvals = (wallet_status or {}).get("approvals")
    if not isinstance(approvals, dict) or not approvals.get("position_manager_operators"):
        return False
    return all(all(group.values()) for group in approvals.values())


def too_fresh_to_call(row):
    """True while a fill of this order may still be on its way to the chain. A
    row with no timestamp is old enough."""
    if not row.get("ts"):
        return False
    placed = dt.datetime.strptime(row["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    age = dt.datetime.now(dt.timezone.utc) - placed
    return age.total_seconds() < RECONCILE_GRACE_S


def v2_payout_per_share(row):
    """What the official resolution pays per share of this V2 position, None until
    it resolves or when Gamma can't answer. Unlike a V1 claim, which burns both
    sides, redeem.py leaves a losing V2 position in the Safe, and claims a winner
    only if the Data API lists it. So a held position's fate comes from Gamma, not
    from the Data API's row, which marks a loser redeemable and may not list a
    position at all."""
    try:
        market = pmapi.gamma_market(row["market_id"])
        if market.get("resolutionStatus") != "resolved":
            return None
        prices = zip(json.loads(market["outcomes"]), json.loads(market["outcomePrices"]))
        return float(dict(prices)[row.get("outcome")])
    except (RuntimeError, KeyError, TypeError, ValueError):
        return None


def cmd_doctor(args):
    store = store_path()
    verdict = {"healthcheck": healthy()}
    if not verdict["healthcheck"]:
        print(json.dumps({"ok": False, "ready": False, **verdict,
                          "error": "connect signer not healthy on 127.0.0.1:8716"},
                         indent=2))
        sys.exit(1)
    if args.setup:
        rc, out, errtxt = run_script(store, "deposit_wallet.py", "ensure",
                                     timeout=400)
        verdict["ensure"] = out if rc == 0 else {"rc": rc, "stderr": errtxt}
        rc, out, errtxt = run_script(store, "funds.py", "wrap", timeout=300)
        verdict["wrap"] = out if rc == 0 else {"rc": rc, "stderr": errtxt}
    rc, out, errtxt = run_script(store, "deposit_wallet.py", "status")
    verdict["deposit_wallet"] = out if rc == 0 else {"rc": rc, "stderr": errtxt}
    rc, out, errtxt = run_script(store, "funds.py", "balances")
    verdict["balances"] = out if rc == 0 else {"rc": rc, "stderr": errtxt}
    dw = verdict.get("deposit_wallet") or {}
    approvals = dw.get("approvals")
    approvals_ok = approvals if isinstance(approvals, bool) else bool(approvals)
    ready = bool(dw.get("deposit_wallet")) and approvals_ok
    print(json.dumps({"ok": True, "ready": ready,
                      "v2_ready": ready and v2_approved(dw), **verdict}, indent=2))


def cmd_place(args):
    cfg, real = load_protected()
    store = store_path()
    if not healthy():
        fail("connect signer not healthy — refusing to place")

    if args.usd is None:
        args.usd = real["max_stake_usd"]
    if args.usd > real["max_stake_usd"]:
        fail(f"stake {args.usd} exceeds real.max_stake_usd {real['max_stake_usd']}")

    paper = {row["id"]: row for row in read_jsonl(PAPER_LEDGER)}
    twin = paper.get(args.paper_id)
    if not twin:
        fail(f"paper ledger has no row with id {args.paper_id}")
    edge_class = twin.get("edge_class", "unclassified")
    if edge_class not in real["allowed_edge_classes"]:
        fail(f"edge_class {edge_class!r} not in allowed_edge_classes "
             f"{real['allowed_edge_classes']} — this bet stays paper-only")

    # The paper ledger already refuses read-only markets; this check is on the
    # market itself, so no paper row can reach an order on one. Fails closed
    # before any top-up.
    try:
        market = pmapi.gamma_market(twin["market_id"])
    except RuntimeError as e:
        fail(f"cannot read market {twin['market_id']}'s protocol version: {e}")
    version = pmapi.market_version(market)
    if not pmapi.tradable(market):
        fail(f"market {twin['market_id']} (Gamma version {version!r}) is read-only "
             f"- real orders only go to V1 and binary V2 markets")
    # An id recorded under another protocol must never reach a V2 order, so the
    # twin's id has to be the one Gamma lists for this outcome right now.
    if version == "v2" and pmapi.market_tokens(market).get(twin.get("outcome")) != twin["token_id"]:
        fail(f"paper row {args.paper_id}'s token id is not the position id Gamma "
             f"lists for {twin.get('outcome')!r} on V2 market {twin['market_id']}")

    # Every gate below reads the ledger, so the lock runs from that read through
    # the pending row they all block on.
    with ledger_lock():
        rows = real_rows()
        if any(r.get("status") in ("pending", "unknown") for r in rows):
            fail("an earlier real order is unreconciled (pending/unknown) - run "
                 "`core/real.py settle` first; buys are not idempotent and must "
                 "never be blind-retried")
        if any(r.get("market_id") == twin["market_id"]
               and r.get("status") == "placed" for r in rows):
            fail(f"market {twin['market_id']} already has a real position - one "
                 f"real bet per market")
        open_count = sum(1 for r in rows if r.get("status") == "placed"
                         and not r.get("settled"))
        if open_count >= real["max_open_positions"]:
            fail(f"open real positions ({open_count}) at cap "
                 f"({real['max_open_positions']})")
        today = now_iso()[:10]
        spent_today = sum(r.get("usd", 0) for r in rows
                          if r.get("ts", "").startswith(today)
                          and r.get("status") in ("placed", "pending", "unknown"))
        if spent_today + args.usd > real["daily_stake_cap_usd"]:
            fail(f"daily stake cap: {spent_today} spent + {args.usd} would exceed "
                 f"{real['daily_stake_cap_usd']}")

        if version == "v2":
            rc, out, errtxt = run_script(store, "deposit_wallet.py", "status")
            if rc != 0 or not v2_approved(out):
                fail(f"not ready for V2 orders: the DepositWallet lacks the V2 approvals "
                     f"or Pearl Connect is older than v0.1.13. For the operator: "
                     f"`core/real.py doctor --setup` grants the approvals. {errtxt}".strip())

        rid = uuid.uuid4().hex[:12]
        base = {"id": rid, "ts": now_iso(), "paper_id": args.paper_id,
                "market_id": twin["market_id"], "token_id": twin["token_id"],
                "question": twin.get("question"), "outcome": twin.get("outcome"),
                "edge_class": edge_class, "usd": args.usd, "version": version,
                "strategy_rev": twin.get("strategy_rev")}
        append_real({**base, "status": "pending"})

    topup = round(args.usd * (1 + FEE_HEADROOM), 2)
    rc, out, errtxt = run_script(store, "funds.py", "top-up",
                                 "--amount", topup, timeout=300)
    if rc != 0:
        append_real({**base, "status": "failed",
                     "error": f"top-up failed: {errtxt or out}"})
        fail(f"top-up failed: {errtxt or out}")

    rc, out, errtxt = run_script(store, "trade.py", "buy",
                                 "--token-id", twin["token_id"],
                                 "--usd", args.usd, timeout=180)
    # An unknown row is stamped now, not before the top-up and the buy: settle's
    # grace has to start from the moment a fill can still reach the chain.
    if rc is None:
        append_real({**base, "ts": now_iso(), "status": "unknown",
                     "error": "buy timed out — submission ambiguous; do NOT "
                              "retry; settle must reconcile"})
        fail("buy timed out — status unknown, further real bets blocked "
             "until settle reconciles")
    if rc != 0 and not buy_refused(rc, out, errtxt):
        detail = errtxt or out or f"exit code {rc}"
        append_real({**base, "ts": now_iso(), "status": "unknown", "error": str(detail)})
        fail(f"buy may have been placed - status unknown, further real bets "
             f"blocked until settle reconciles: {detail}")
    if rc != 0:
        append_real({**base, "status": "failed", "error": errtxt or str(out)})
        fail(f"buy rejected: {errtxt or out}")
    # Accepted is not filled: a delayed order can still be killed before it matches.
    if isinstance(out, dict) and out.get("status") in ("live", "delayed"):
        append_real({**base, "ts": now_iso(), "status": "unknown", "order": out})
        fail(f"buy accepted but not matched ({out['status']}) - status unknown, "
             f"further real bets blocked until settle reconciles")
    append_real({**base, "status": "placed", "order": out})
    print(json.dumps({"ok": True, "id": rid, "status": "placed",
                      "order": out}, indent=2))


def cmd_settle(args):
    load_protected()
    store = store_path()
    if not healthy():
        fail("connect signer not healthy — refusing to settle")
    result = {"ts": now_iso()}
    rc, out, errtxt = run_script(store, "funds.py", "sweep", timeout=400)
    result["sweep"] = out if rc == 0 else {"rc": rc, "stderr": errtxt}
    rc, out, errtxt = run_script(store, "redeem.py", "all", timeout=400)
    result["redeem"] = out if rc == 0 else {"rc": rc, "stderr": errtxt}
    # The Data API lags the chain, so ask the chain about every token the ledger
    # still tracks.
    tracked = sorted({str(r.get("token_id")) for r in real_rows()
                      if r.get("status") in ("pending", "unknown")
                      or (r.get("status") == "placed" and not r.get("settled"))})
    token_args = ["--token-ids", ",".join(tracked)] if tracked else []
    rc, out, errtxt = run_script(store, "positions.py", "positions", *token_args)
    positions = out if rc == 0 else None
    result["positions"] = positions if positions is not None \
        else {"rc": rc, "stderr": errtxt}

    # Reconcile: a pending/unknown row whose token shows up as a position or
    # trade is a fill; mark placed rows settled when their token no longer
    # appears among open positions.
    # Fail closed: with no trustworthy position list (positions.py failed,
    # timed out, returned an unknown shape - e.g. after the Data API v1
    # retirement on 2026-10-24 - or could not read the chain) an empty token set
    # would fail every pending row and settle every placed one. Leave the rows
    # as they are; pending rows keep blocking new real bets.
    if isinstance(positions, list):
        live = positions
    elif isinstance(positions, dict) and isinstance(positions.get("positions"), list):
        live = positions["positions"]
    else:
        live = None
    onchain = positions.get("onchain_check") if isinstance(positions, dict) else None
    if live is None or (onchain or {}).get("error"):
        result["reconcile_skipped"] = "no usable positions list"
        append_real({"id": f"settle-{uuid.uuid4().hex[:8]}", "type": "settle",
                     **result})
        fail("positions.py gave no usable positions list - reconcile "
             "skipped, real-ledger rows left unchanged")
    open_tokens = {str(p.get("token_id")) for p in live}
    if onchain:
        # For a token it read, the chain outranks the indexer in both directions.
        open_tokens -= {str(t) for t in onchain.get("checked_token_ids", [])}
        open_tokens |= {str(hit.get("token_id")) for hit in onchain.get("held", [])}
    # A token this settle swept was filled, even if a claim has burned it since.
    sweep = result["sweep"].get("positions") if isinstance(result["sweep"], dict) else None
    swept = set(sweep) if isinstance(sweep, dict) else set()
    unclaimed = []
    for row in real_rows():
        tok = str(row.get("token_id"))
        if row.get("status") in ("pending", "unknown"):
            filled = tok in open_tokens or tok in swept
            if not filled and too_fresh_to_call(row):
                continue
            append_real({**row, "status": "placed" if filled else "failed",
                         "ts": now_iso(), "reconciled": True,
                         "note": "reconciled by settle from live positions"})
        elif row.get("status") == "placed" and not row.get("settled"):
            if tok not in open_tokens:
                if not too_fresh_to_call(row):
                    append_real({**row, "settled": True, "ts": now_iso(),
                                 "note": "no longer an open position - resolved "
                                         "and swept/redeemed"})
            elif row.get("version") == "v2":
                payout = v2_payout_per_share(row)
                if payout == 0:
                    append_real({**row, "settled": True, "ts": now_iso(),
                                 "note": "resolved against this position: no value "
                                         "to claim, so it stays in the Safe"})
                elif payout:
                    unclaimed.append({"id": row["id"], "market_id": row.get("market_id"),
                                      "token_id": tok, "payout_per_share": payout})
    # The money stays in the Safe, but each such row holds an open position slot.
    if unclaimed:
        result["unclaimed"] = unclaimed
    append_real({"id": f"settle-{uuid.uuid4().hex[:8]}", "type": "settle",
                 **result})
    print(json.dumps({"ok": True, **result}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor")
    d.add_argument("--setup", action="store_true",
                   help="also run deposit_wallet ensure (deploy + approvals, "
                        "V2's included)")
    d.set_defaults(fn=cmd_doctor)
    p = sub.add_parser("place")
    p.add_argument("--paper-id", required=True,
                   help="paper ledger row id this real bet mirrors")
    p.add_argument("--usd", type=float, default=None,
                   help="stake; defaults to real.max_stake_usd from "
                        "config/protected.json")
    p.set_defaults(fn=cmd_place)
    s = sub.add_parser("settle")
    s.set_defaults(fn=cmd_settle)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
