#!/usr/bin/env python3
"""Project a Brazilian TSE partial count to its final valid-vote shares.

Usage: python3 strategy/tools/tse_count.py [--ele 6257] [--cargo 0001]
                                           [--ufs all|am,ap,...] [--names A,B]

Built 2026-10-04 (Brazil 1st round, FULL cycle 22:1xZ). The early national
count is badly biased: South/Centre-West and big-city sections land first,
North-East and interior sections later. At 64.8pct of sections the raw count
read Lula 42.77 / Flavio 49.11, while scaling each MUNICIPALITY's counted
shares to its full electorate gave Lula 44.84 / Flavio 47.26 (state-level
scaling gave 44.41 -- coarser weighting under-corrects). The market's
ladder (Lula >=44 at ~0.93) agreed with the municipality projection, not
the raw count. Grade this projection against the final TSE result before
leaning on it (first use, no error series yet -- see playbook vote-share
sd rule, DEEP-2026-10-04).

Data: resultados.tse.jus.br public JSON. config/mun-e<ele>-cm.json lists
municipalities; dados/<uf>/<uf><mun>-c<cargo>-e<ele>-u.json carries the
municipality's candidate votes ('vap'), valid votes (v.vv), and counted vs
total electorate (e.est / e.te). The national -r.json path 404s in 2026;
the -u.json files carry the results.
"""
import argparse
import concurrent.futures as cf
import json
import urllib.request

BASE = "https://resultados.tse.jus.br/oficial/ele2026/{ele}/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; paper-trader-tse)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=20))


def walk(o):
    if isinstance(o, dict):
        if "vap" in o and "nmu" in o:
            yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def muni(args, uf, cd):
    url = BASE.format(ele=args.ele) + (
        f"dados/{uf}/{uf}{cd}-c{args.cargo}-e{int(args.ele):06d}-u.json")
    for _ in range(3):
        try:
            d = fetch(url)
            votes = {c["nmu"]: int(c["vap"]) for c in walk(d)}
            return (uf, votes, int(d["v"]["vv"]), int(d["e"]["est"]),
                    int(d["e"]["te"]), d["hg"])
        except Exception:
            continue
    return (uf, None, 0, 0, 0, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ele", default="6257")
    ap.add_argument("--cargo", default="0001")
    ap.add_argument("--ufs", default="all")
    ap.add_argument("--names", default="LULA,FLAVIO BOLSONARO")
    args = ap.parse_args()
    names = args.names.split(",")
    cfg = fetch(BASE.format(ele=args.ele) +
                f"config/mun-e{int(args.ele):06d}-cm.json")
    want = None if args.ufs == "all" else set(args.ufs.split(","))
    jobs = [(a["cd"], m["cd"]) for a in cfg["abr"]
            if want is None or a["cd"] in want for m in a["mu"]]
    with cf.ThreadPoolExecutor(64) as ex:
        res = list(ex.map(lambda j: muni(args, *j), jobs))
    agg, fails, latest = {}, 0, ""
    for uf, votes, vv, est, te, hg in res:
        if votes is None:
            fails += 1
            continue
        latest = max(latest, hg or "")
        a = agg.setdefault(uf, {"raw": [0] * (len(names) + 1),
                                "proj": [0.0] * (len(names) + 1),
                                "uncounted_te": 0})
        row = [votes.get(n, 0) for n in names] + [vv]
        scale = te / est if est else 0.0
        if not est:
            a["uncounted_te"] += te
        for i, x in enumerate(row):
            a["raw"][i] += x
            a["proj"][i] += x * scale
    out = {"latest_hg": latest, "fails": fails, "by_uf": {}}
    tot_raw = [0] * (len(names) + 1)
    tot_proj = [0.0] * (len(names) + 1)
    for uf, a in sorted(agg.items()):
        r, p = a["raw"], a["proj"]
        out["by_uf"][uf] = {
            "counted": {n: round(100 * r[i] / r[-1], 2) if r[-1] else None
                        for i, n in enumerate(names)},
            "projected": {n: round(100 * p[i] / p[-1], 2) if p[-1] else None
                          for i, n in enumerate(names)},
            "uncounted_muni_electorate": a["uncounted_te"]}
        tot_raw = [x + y for x, y in zip(tot_raw, r)]
        tot_proj = [x + y for x, y in zip(tot_proj, p)]
    out["total"] = {
        "counted": {n: round(100 * tot_raw[i] / tot_raw[-1], 2)
                    for i, n in enumerate(names)} if tot_raw[-1] else None,
        "projected": {n: round(100 * tot_proj[i] / tot_proj[-1], 2)
                      for i, n in enumerate(names)} if tot_proj[-1] else None}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
