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

Requires env PEARL_CONNECT_STORE = the Pearl Connect workspace path
(the directory containing .mcp.json). Optional CONNECT_POLYMARKET_VENV.

Usage:
  python3 core/real.py doctor [--setup]
  python3 core/real.py place --paper-id <id> --usd 1.0
  python3 core/real.py settle
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAPER_LEDGER = ROOT / "journal" / "ledger.jsonl"
REAL_LEDGER = ROOT / "journal" / "real-ledger.jsonl"
PROTECTED = ROOT / "config" / "protected.json"

HEALTHCHECK_URL = "http://127.0.0.1:8716/healthcheck"
SKILL_SCRIPTS = pathlib.Path(".claude") / "skills" / "connect-polymarket" / "scripts"
VENV_DEFAULT = pathlib.Path.home() / ".cache" / "connect-polymarket" / "venv"
VENV_DEPS = ["py-clob-client-v2==1.0.2", "web3>=7.15,<8", "requests"]
FEE_HEADROOM = 0.15  # top-up = stake * (1 + headroom); taker fee on $1 is cents


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


def venv_python(store):
    venv = pathlib.Path(os.environ.get("CONNECT_POLYMARKET_VENV", VENV_DEFAULT))
    py = venv / "bin" / "python"
    if not py.exists():
        print(f"bootstrapping venv at {venv}", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade",
                        "pip"], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", *VENV_DEPS],
                       check=True)
    return py


def run_script(store, name, *args, timeout=180):
    """Run a connect-polymarket skill script; returns (rc, stdout_json|None, stderr)."""
    py = venv_python(store)
    script = store / SKILL_SCRIPTS / name
    if not script.exists():
        fail(f"skill script missing: {script} (Pearl Connect provisions it "
             f"at boot — is the connect agent running?)")
    cacert = subprocess.run([str(py), "-c", "import certifi; print(certifi.where())"],
                            capture_output=True, text=True).stdout.strip()
    env = {**os.environ}
    if cacert:
        env["SSL_CERT_FILE"] = env["REQUESTS_CA_BUNDLE"] = cacert
    try:
        proc = subprocess.run([str(py), str(script), *map(str, args)],
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
    print(json.dumps({"ok": True, "ready": ready, **verdict}, indent=2))


def cmd_place(args):
    cfg, real = load_protected()
    store = store_path()
    if not healthy():
        fail("connect signer not healthy — refusing to place")

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

    rows = real_rows()
    if any(r.get("status") in ("pending", "unknown") for r in rows):
        fail("an earlier real order is unreconciled (pending/unknown) — run "
             "`core/real.py settle` first; buys are not idempotent and must "
             "never be blind-retried")
    if any(r.get("market_id") == twin["market_id"]
           and r.get("status") == "placed" for r in rows):
        fail(f"market {twin['market_id']} already has a real position — one "
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

    rid = uuid.uuid4().hex[:12]
    base = {"id": rid, "ts": now_iso(), "paper_id": args.paper_id,
            "market_id": twin["market_id"], "token_id": twin["token_id"],
            "question": twin.get("question"), "outcome": twin.get("outcome"),
            "edge_class": edge_class, "usd": args.usd,
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
    if rc is None:
        append_real({**base, "status": "unknown",
                     "error": "buy timed out — submission ambiguous; do NOT "
                              "retry; settle must reconcile"})
        fail("buy timed out — status unknown, further real bets blocked "
             "until settle reconciles")
    if rc != 0:
        append_real({**base, "status": "failed", "error": errtxt or str(out)})
        fail(f"buy rejected: {errtxt or out}")
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
    rc, out, errtxt = run_script(store, "positions.py", "positions")
    positions = out if rc == 0 else None
    result["positions"] = positions if positions is not None \
        else {"rc": rc, "stderr": errtxt}

    # Reconcile: a pending/unknown row whose token shows up as a position or
    # trade is a fill; mark placed rows settled when their token no longer
    # appears among open positions.
    open_tokens = set()
    if isinstance(positions, list):
        open_tokens = {str(p.get("token_id")) for p in positions}
    elif isinstance(positions, dict):
        open_tokens = {str(p.get("token_id"))
                       for p in positions.get("positions", [])}
    for row in real_rows():
        tok = str(row.get("token_id"))
        if row.get("status") in ("pending", "unknown"):
            new_status = "placed" if tok in open_tokens else "failed"
            append_real({**row, "status": new_status, "ts": now_iso(),
                         "reconciled": True,
                         "note": "reconciled by settle from live positions"})
        elif row.get("status") == "placed" and not row.get("settled") \
                and tok not in open_tokens:
            append_real({**row, "settled": True, "ts": now_iso(),
                         "note": "no longer an open position — resolved and "
                                 "swept/redeemed"})
    append_real({"id": f"settle-{uuid.uuid4().hex[:8]}", "type": "settle",
                 **result})
    print(json.dumps({"ok": True, **result}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor")
    d.add_argument("--setup", action="store_true",
                   help="also run deposit_wallet ensure (deploy + approvals)")
    d.set_defaults(fn=cmd_doctor)
    p = sub.add_parser("place")
    p.add_argument("--paper-id", required=True,
                   help="paper ledger row id this real bet mirrors")
    p.add_argument("--usd", type=float, required=True)
    p.set_defaults(fn=cmd_place)
    s = sub.add_parser("settle")
    s.set_defaults(fn=cmd_settle)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
