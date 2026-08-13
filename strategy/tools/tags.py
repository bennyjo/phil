"""Tag-taxonomy explorer — AGENT-EDITABLE (strategy/tools/).

Mandated by operator-notes 2026-08-05 ("tag taxonomy exploration is yours
now"), delivered by DEEP-2026-08-12 after seven days unstarted. Purpose:
the discovery queries are volume/tag-anchored, so whole mid-liquidity
categories can be structurally invisible. This tool makes the taxonomy
enumerable and lets a cycle answer, per tag: does it surface live markets,
in what volume range, and do they resolve on an official number?

Usage:
  python3 strategy/tools/tags.py list [--offset N] [--limit N]
      Page through gamma /tags (id, slug, label). Thousands exist; most are
      per-player/per-meme noise. Use for spot-checks, not full enumeration.
  python3 strategy/tools/tags.py grep <substr>
      Scan up to --max-pages pages of /tags for slugs/labels containing
      <substr> (case-insensitive). Cheap way to find candidate tag ids.
  python3 strategy/tools/tags.py check <tag_id> [--min-volume N]
      The verification query from operator-notes: live-market count, volume
      range, end dates, and sample questions for one tag, so the cycle can
      judge resolution mechanics before touching discovery.py.

Weekly-cadence intent (agent-owned pacing): spot-check a handful of tags,
fold winners into discovery.py with the evidence in the retro, and re-check
previously-empty tags (weather 1474 is the named example) on the same
cadence.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
import pmapi  # noqa: E402


def list_tags(offset, limit):
    return pmapi.get_json(f"{pmapi.GAMMA}/tags",
                          {"limit": limit, "offset": offset})


def cmd_list(args):
    for t in list_tags(args.offset, args.limit):
        print(f"{t.get('id'):>8}  {t.get('slug','')[:40]:<40}  {t.get('label','')[:40]}")


def cmd_grep(args):
    needle = args.substr.lower()
    hits = 0
    for page in range(args.max_pages):
        batch = list_tags(page * 100, 100)
        if not batch:
            break
        for t in batch:
            hay = (str(t.get("slug", "")) + " " + str(t.get("label", ""))).lower()
            if needle in hay:
                print(f"{t.get('id'):>8}  {t.get('slug','')[:40]:<40}  {t.get('label','')[:40]}")
                hits += 1
    if not hits:
        print(f"no tag slug/label containing {args.substr!r} in first "
              f"{args.max_pages * 100} tags", file=sys.stderr)


def cmd_check(args):
    markets = pmapi.gamma_markets(tag_id=args.tag_id, closed="false",
                                  limit=100, volume_num_min=args.min_volume)
    print(f"tag {args.tag_id}: {len(markets)} live markets "
          f"(volume_num_min={args.min_volume}, limit 100)")
    for m in sorted(markets, key=lambda m: -float(m.get("volumeNum") or 0))[:15]:
        vol = float(m.get("volumeNum") or 0)
        print(f"  vol={vol:>12,.0f}  end={str(m.get('endDate',''))[:10]}  "
              f"{(m.get('question') or '')[:75]}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("--offset", type=int, default=0)
    lp.add_argument("--limit", type=int, default=100)
    lp.set_defaults(fn=cmd_list)
    gp = sub.add_parser("grep")
    gp.add_argument("substr")
    gp.add_argument("--max-pages", type=int, default=10)
    gp.set_defaults(fn=cmd_grep)
    cp = sub.add_parser("check")
    cp.add_argument("tag_id")
    cp.add_argument("--min-volume", type=int, default=0)
    cp.set_defaults(fn=cmd_check)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
