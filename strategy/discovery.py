"""Market discovery — AGENT-EDITABLE.

This is my sensing layer. `core/scan.py` calls `queries()` and then applies the
protected admissibility filters (banned classes, resolution floor, price
bounds) to whatever comes back. I decide WHAT TO LOOK FOR; core decides what is
allowed. A query I write cannot let a banned market through, so I can explore
freely.

Why this file exists (operator, 2026-08-03): for two days I produced zero bets
and correctly logged "no qualifying candidate" every cycle. The cause was not
the market — it was that scan paged in endDate order through a near-term
universe thousands of sub-daily markets deep and never escaped day 0. My
candidate pool was an artifact of a tool I could not edit and could not see
into. Now I can. Use it: if the pool looks structurally wrong, change the
queries and say so in the retro.

Contract: return a list of dicts of gamma `/markets` query params. Optional
`_label` names the query in scan's stderr. Anything raising here falls back to
core's default query (loudly), so a bug degrades sensing but never blinds me.
Gamma params that work: closed, order (endDate|volume24hr|liquidity),
ascending, end_date_min, end_date_max, volume_num_min, liquidity_num_min,
tag_id, related_tags.
"""


def queries(now, min_end, horizon, args, protected):
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    base = {"closed": "false", "end_date_min": iso(min_end),
            "end_date_max": iso(horizon)}

    return [
        # 1. Well-covered events out to the horizon. The lifetime-volume floor
        #    is what lets pagination escape today; do NOT add a 24h-volume
        #    floor here — an event five days out legitimately has little volume
        #    today, which re-creates the blindness this file was made to fix.
        {**base, "_label": "liquid-multiday", "order": "endDate",
         "ascending": "true", "volume_num_min": 50000},

        # 2. Deep books regardless of date order — surfaces the biggest events
        #    in the window (ATP/WTA main draws, major-league fixtures) even if
        #    thousands of small markets resolve sooner.
        {**base, "_label": "by-liquidity", "order": "liquidity",
         "ascending": "false", "liquidity_num_min": 20000},

        # 3. Today's active markets, kept from the old behaviour so nothing
        #    imminent is lost: heavy recent trading, near-term resolution.
        {"closed": "false", "_label": "active-today", "order": "volume24hr",
         "ascending": "false", "end_date_min": iso(min_end),
         "end_date_max": iso(min(horizon, now.replace(microsecond=0) +
                                 __import__("datetime").timedelta(hours=36)))},
    ]
