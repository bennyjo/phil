"""Append one mech-marketplace second-opinion record to journal/mech-requests.jsonl.

Cycle sessions call this right after every `mech_request` (CYCLE.md step 5a)
so retros can grade each mech tool against Phil's own estimate and the
market without re-parsing forecast notes. One line per request, including
failures (pass --error and no --result-json).

Usage:
  python3 core/mechlog.py record --market-id <id> --mech <address> \
    --tool <tool> --request-id <your invented id> --own-p <p> \
    [--market-p <mid>] [--result-json '<delivery result string>'] \
    [--params-json '<delivery metadata.params>'] [--latency-ms N] \
    [--error "<one line>"] [--note "<one line>"]
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "journal" / "mech-requests.jsonl"

RESULT_FIELDS = (
    "p_yes", "p_no", "confidence", "info_utility", "researchability",
    "research_class", "research_reason", "evidence_quality",
    "market_prob_seen", "p_independent", "error", "error_type",
)
PARAM_FIELDS = ("parse_tier", "scan_truncated", "null_reason", "model")


def _loads(text, label):
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.exit(f"--{label}: not valid JSON ({exc})")
    return data if isinstance(data, dict) else {}


def cmd_record(args):
    result = _loads(args.result_json, "result-json")
    params = _loads(args.params_json, "params-json")
    row = {
        "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "market_id": args.market_id,
        "mech": args.mech.lower(),
        "tool": args.tool,
        "request_id": args.request_id,
        "own_p": args.own_p,
        "market_p": args.market_p,
        "latency_ms": args.latency_ms,
        "error": args.error or result.get("error"),
        "note": args.note,
    }
    for key in RESULT_FIELDS:
        if key in result and key != "error":
            row[key] = result[key]
    for key in PARAM_FIELDS:
        if key in params:
            row[key] = params[key]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(row, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record", help="append one mech request record")
    p.add_argument("--market-id", required=True)
    p.add_argument("--mech", required=True, help="priority_mech address used")
    p.add_argument("--tool", required=True)
    p.add_argument("--request-id", required=True, help="the id you invented")
    p.add_argument("--own-p", type=float, required=True,
                   help="your pre-mech P(outcome) for the asked outcome")
    p.add_argument("--market-p", type=float, default=None,
                   help="market mid for that outcome at request time")
    p.add_argument("--result-json", default="",
                   help="the delivery's `result` string (JSON) verbatim")
    p.add_argument("--params-json", default="",
                   help="the delivery's `metadata.params` object as JSON")
    p.add_argument("--latency-ms", type=int, default=None)
    p.add_argument("--error", default="", help="one line if the request failed")
    p.add_argument("--note", default="")
    p.set_defaults(fn=cmd_record)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
