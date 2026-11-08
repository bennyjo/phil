"""Per-event book medians, POWER devig first, from `core/odds.py odds` JSON.

Usage:
  python3 core/odds.py odds basketball_nba | python3 strategy/tools/bookmed.py
  python3 strategy/tools/bookmed.py saved_odds.json [--team Hawks]

For every event and every h2h outcome it prints the median across books of
the power-devigged fair prob (the number to record), the proportional median
(for the devig-method gap only), and the book count.

Why (RETRO-20261108-0415): the playbook already says to use the POWER number
for any side priced below ~0.60 (DEEP-2026-07-31), but the Nov 7 12:15Z NBA
book-devig rows were all recorded off proportional medians (Nets .31, Wizards
.21 underdogs; Nuggets .71 / Knicks .64 favourites under-stated) and every
one scored worse than the PM mid. Doing the devig per book by hand invites
the shortcut; this tool prints power first so the shortcut is gone.
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from devig import power_devig  # noqa: E402


def event_rows(ev):
    per_outcome = {}
    for bk in ev.get("bookmakers", []):
        for mk in bk.get("markets", []):
            if mk.get("key") != "h2h":
                continue
            outs = mk.get("outcomes", [])
            prices = [o.get("price") for o in outs]
            if len(outs) < 2 or any(not p or p <= 1 for p in prices):
                continue
            raw = [1.0 / p for p in prices]
            tot = sum(raw)
            pw, _k = power_devig(raw)
            for o, r, f in zip(outs, raw, pw):
                d = per_outcome.setdefault(o["name"], {"prop": [], "power": []})
                d["prop"].append(r / tot)
                d["power"].append(f)
    return per_outcome


def main(argv):
    team = None
    if "--team" in argv:
        i = argv.index("--team")
        team = argv[i + 1].lower()
        argv = argv[:i] + argv[i + 2:]
    src = open(argv[0]) if argv else sys.stdin
    data = json.load(src)
    if isinstance(data, dict):
        data = data.get("data", [data])
    for ev in data:
        rows = event_rows(ev)
        if not rows:
            continue
        names = " vs ".join(rows)
        if team and team not in names.lower():
            continue
        print(f"{ev.get('commence_time', '?')}  {ev.get('away_team', '')} @ {ev.get('home_team', '')}")
        for name, d in rows.items():
            pw = statistics.median(d["power"])
            pr = statistics.median(d["prop"])
            print(f"  {name:28s} power={pw:.3f}  prop={pr:.3f}  gap={pr - pw:+.3f}  books={len(d['power'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
