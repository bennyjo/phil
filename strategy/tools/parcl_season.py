"""Same-season check for Parcl Dec 31 legs: relative change from ~Oct 1 to
Dec 31 in each past year, per parcl id on argv (playbook 2026-10-03).

Usage: python3 strategy/tools/parcl_season.py <parcl_id> [<parcl_id> ...]
"""
import datetime as dt
import json
import sys
import urllib.request


def history(pid):
    req = urllib.request.Request(
        "https://api-app-service.parcllabs.com/v1/price-feeds/history",
        data=json.dumps({"parcl_ids": [pid], "start_date": "2020-01-01"}).encode(),
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


for pid in [int(a) for a in sys.argv[1:]]:
    rows = history(pid)["series"][str(pid)]["data"]
    pts = {}
    for r in rows:
        d = r.get("date") or r.get("price_date")
        v = r.get("price") or r.get("value") or r.get("price_feed")
        if d and v:
            pts[dt.date.fromisoformat(d[:10])] = float(v)
    days = sorted(pts)
    print(pid, "points", len(days), days[0], days[-1], pts[days[-1]])
    for y in range(2020, 2026):
        a = [d for d in days if dt.date(y, 9, 30) <= d <= dt.date(y, 10, 4)]
        b = [d for d in days if dt.date(y, 12, 29) <= d <= dt.date(y + 1, 1, 2)]
        if a and b:
            print("  ", y, a[0], b[-1], "%+.2f%%" % (100 * (pts[b[-1]] / pts[a[0]] - 1)))
