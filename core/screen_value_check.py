#!/usr/bin/env python3
"""Out-of-sample check for the dormant research-value prior (screen_value.py).

PROTECTED CORE - the trading agent must not edit files under core/.

This is condition 2 of the switch bar in journal/screener-value-decision.md:
does the shrunk prior order held-out rows better than a permutation of its
own scores? It is kept in core/ so the bar can be re-checked with the same
statistic that set it, instead of being rebuilt from the memo's prose.

Walk-forward, event-clustered folds (replay.py's cut). For each fold the prior
is fitted ONLY on rows that settled earlier, then used to order that fold's
rows. The statistic is the lift of the top quartile: mean brier_delta of the
rows the prior ranks best, minus the fold mean. Negative is good.

The null is a permutation of the fold's own scores, which keeps both marginal
distributions and destroys only the pairing - the run-2 rule: prove the null
by simulation before quoting a lift.

Usage: python3 core/screen_value_check.py        (about a minute, offline)
"""
import math
import random
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
import screen_replay  # noqa: E402
import screen_value  # noqa: E402
FOLDS = 5
TOPS = (0.25, 0.10)
DRAWS = 4000
MODELS = {
    "null (constant)": (),
    "family": ("family",),
    "age": ("age_band",),
    "price": ("price_band",),
    "hours": ("hours_band",),
    "family+age": ("family", "age_band"),
    "all four": ("family", "price_band", "hours_band", "age_band"),
}


def chunks(rows, folds):
    size = math.ceil(len(rows) / folds)
    return [rows[i:i + size] for i in range(0, len(rows), size)]


def lift(scored, top):
    """mean brier_delta of the best-ranked `top` share, minus the group mean.

    Ties averaged over rather than broken, screen_replay.top_k_weights: the
    prior takes at most nine distinct values on a family-only fit, so the
    top-quartile cut falls inside a tie group nearly always, and a stable
    sort would then select on record order. That artifact is worth -0.0069
    here, comparable to every lift in the table.
    """
    k = max(1, int(round(len(scored) * top)))
    w = screen_replay.top_k_weights([-p[0] for p in scored], k)
    all_mean = sum(p[1] for p in scored) / len(scored)
    return sum(wi * p[1] for wi, p in zip(w, scored)) / k - all_mean, k


def walk(items, features, top, rng=None):
    """Per-fold (n, k, lift) using a prior fitted only on earlier folds."""
    cs = chunks(items, FOLDS)
    out = []
    for k in range(1, len(cs)):
        train = [s for c in cs[:k] for s in c]
        test = cs[k]
        if features:
            prior = screen_value.fit_prior(train, features)
            scored = [(screen_value.prior_score(prior, s)[0], s["brier_delta"])
                      for s in test]
        else:
            scored = [(0.0, s["brier_delta"]) for s in test]
        if rng:
            vals = [p[0] for p in scored]
            rng.shuffle(vals)
            scored = [(v, p[1]) for v, p in zip(vals, scored)]
        lf, kk = lift(scored, top)
        out.append({"fold": k, "n": len(test), "k": kk, "lift": lf,
                    "mean": sum(p[1] for p in scored) / len(scored)})
    return out


def pooled(folds):
    """Row-weighted aggregate of the per-fold lifts."""
    w = sum(f["k"] for f in folds)
    return sum(f["lift"] * f["k"] for f in folds) / w


def main():
    rules, bands = screen_value.load_value_config()
    items = screen_value.observations(rules, bands)
    print(f"screen_value check: {len(items)} settled rows, {FOLDS} walk-forward folds, "
          f"{DRAWS} permutation draws")
    rng = random.Random(20260908)
    for top in TOPS:
        print(f"\ntop {top:.0%} of each held-out fold")
        print(f"{'model':<18} {'lift':>9} {'p(null)':>8} {'null mean':>10} "
              f"{'null sd':>8}   per-fold lift")
        _table(items, top, rng)
    print("\nfold sizes / fold mean brier_delta")
    for f in walk(items, ("family",), 0.25):
        print(f"  fold {f['fold']}: n {f['n']:>4}, top {f['k']:>3}, "
              f"fold mean {f['mean']:+.4f}")


def _table(items, top, rng):
    for name, feats in MODELS.items():
        fs = walk(items, feats, top)
        obs = pooled(fs)
        draws = [pooled(walk(items, feats, top, rng)) for _ in range(DRAWS)] \
            if feats else []
        if draws:
            p = sum(1 for d in draws if d <= obs) / len(draws)
            mu = sum(draws) / len(draws)
            sd = (sum((d - mu) ** 2 for d in draws) / (len(draws) - 1)) ** 0.5
            tail = f"{p:>8.3f} {mu:>+10.4f} {sd:>8.4f}"
        else:
            tail = f"{'-':>8} {'-':>10} {'-':>8}"
        per = " ".join(f"{f['lift']:+.4f}" for f in fs)
        print(f"{name:<18} {obs:>+9.4f} {tail}   {per}")


if __name__ == "__main__":
    main()
