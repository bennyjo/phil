#!/usr/bin/env python3
"""Runner lease: one cycle at a time across Phil's runners.

PROTECTED CORE - the trading agent must not edit files under core/.

Why this exists (operator, 2026-09-06): two runners cycle on the same hours,
the cloud routine and the operator machine's loop.sh. CYCLE.md step 0's
collision guard reads origin/main's tip, so it only sees a cycle that has
already committed; two FULL cycles that start from the same tip inside the
same minute cannot see each other. On 2026-09-04 00:16Z both runners scanned,
both ran 15 Haiku batches, both researched the NFP bracket and both decided
to trade the same leg (journal/proposals.md, "collision-guard gap").

Where it lives (operator, 2026-10-08): journal/lease.json on origin's main.
The first lease was a custom ref, refs/phil/lease, and the cloud credential
cannot push custom refs (HTTP 403 since 2026-09-06) while it pushes main on
every cycle, so every cloud cycle ran unprotected. Main forked (an operator
merge of a 126/142-commit fork on 2026-10-05, the next fork 52 minutes
later), the shared screener quota ran to 195/150 batches, and the operator
runner placed d5cfa982fa21 on top of the open 9a2944acc280 (DEEP-2026-10-08
P3). Any credential that can push main can write this file.

The file holds one JSON object: {"runner", "started", "ttl_s"} while held,
{"runner": null, "released_by", "released"} once released; a missing file
is free too. acquire and release each push one commit that changes nothing
but this file, as a plain fast-forward push to main. Origin applies a push
only while main still points where the pusher saw it, so of two runners
racing for a free lease exactly one push lands; the loser re-reads and
yields.

acquire builds its commit on the local HEAD and fast-forwards HEAD onto it,
so the cycle starts from the commit that took the lease. It needs HEAD to
contain origin/main: a runner whose main is behind or diverged trades on a
stale ledger. ledger.py's duplicate-position guard missed d5cfa982fa21
because the operator runner's diverged main did not have 9a2944acc280.
release builds its commit on origin/main and leaves the local branch alone,
so it works whatever the cycle's own push did; the next sync fast-forwards
over it.

A runner that does not get the lease skips the tick; it does not run a LIGHT
one. A LIGHT tick still settles and commits ledger and forecast rows, which
are not union-merged (.gitattributes), so a LIGHT tick next to the holder's
cycle makes one of the two pushes conflict and fork main. The holder's own
cycle settles and monitors, so the skipped tick loses nothing. That covers
both refusals: held by the other runner (exit 3) and not written (exit 4:
origin unreachable, the push refused, or local main behind or diverged). A
runner that cannot write the lease could not publish its cycle either, since
both are pushes to main. A run that dies mid-cycle leaves a lease that
expires on its own after `ttl_s`, so nothing wedges the other runner for
longer than one cycle.

Runner identity is core/screen.py's runner_id(): $PHIL_RUNNER, else
"operator" when loop.sh's PHIL_PUSH_BY_LOOP is set, else "cloud". On the
operator machine loop.sh acquires and releases in the interactive shell
(the keyring is unlocked there; a push from inside `claude -p` hangs), and
tells the cycle agent through PHIL_LEASE. In the cloud the cycle agent runs
acquire and release itself.

Usage:
  python3 core/lease.py check                # never writes; prints JSON
  python3 core/lease.py acquire [--ttl S]    # exit 0 acquired, 3 held by other, 4 not written
  python3 core/lease.py release              # exit 0 released or not ours, 1 push failed
Every subcommand prints one JSON object. Without an origin remote there is
no shared main to protect, so acquire reports "acquired": true with
"written": false. Nothing here writes any file but journal/lease.json.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import screen  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEASE_FILE = "journal/lease.json"
MAIN = "refs/heads/main"
REMOTE_MAIN = "refs/remotes/origin/main"
DEFAULT_TTL_S = 50 * 60
RELEASE_ATTEMPTS = 3


def git(*args, check=True, input=None, env=None):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=check, timeout=120, input=input,
                          env=env)


def last_line(proc, fallback):
    """The line of git's stderr that says what failed, without the hints."""
    lines = [ln.strip() for ln in proc.stderr.splitlines()
             if ln.strip() and not ln.startswith("hint:")]
    rejected = [ln for ln in lines if "rejected]" in ln]
    return (rejected or lines or [fallback])[-1]


def has_origin():
    return git("remote", "get-url", "origin", check=False).returncode == 0


def now():
    return dt.datetime.now(dt.timezone.utc)


def fetch_main():
    """origin/main's sha after a fresh fetch.

    Raises RuntimeError when origin cannot be reached; acquire turns that
    into a refusal, since a runner that cannot reach origin cannot publish.
    """
    fetched = git("fetch", "--no-tags", "--quiet", "origin",
                  f"+{MAIN}:{REMOTE_MAIN}", check=False)
    if fetched.returncode != 0:
        raise RuntimeError(last_line(fetched, "fetch failed"))
    return git("rev-parse", REMOTE_MAIN).stdout.strip()


def read_lease(rev):
    """The lease payload at `rev`; {} (free) when absent or unreadable."""
    shown = git("show", f"{rev}:{LEASE_FILE}", check=False)
    try:
        payload = json.loads(shown.stdout) if shown.returncode == 0 else {}
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def describe(payload, me):
    runner = payload.get("runner")
    if not runner:
        return {"held": False, "mine": False, "fresh": False, "runner": None,
                "age_s": None}
    try:
        started = dt.datetime.fromisoformat(str(payload.get("started")).replace("Z", "+00:00"))
        age = int((now() - started).total_seconds())
    except (TypeError, ValueError):
        age = None
    try:
        ttl = int(payload.get("ttl_s", DEFAULT_TTL_S))
    except (TypeError, ValueError):
        ttl = DEFAULT_TTL_S
    # abs(): the two runners' clocks differ, so a lease read a moment after
    # it was taken can look a second or two old in the future.
    fresh = age is not None and abs(age) < ttl
    return {"held": True, "mine": runner == me, "fresh": fresh,
            "runner": runner, "age_s": age, "ttl_s": ttl}


def held_by_other(d):
    return d["held"] and d["fresh"] and not d["mine"]


def is_ancestor(a, b):
    return git("merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def lease_commit(parent, payload, message):
    """A commit on `parent` whose only change is the lease file holding `payload`.

    Built through a throwaway index, so the working tree and the real index
    stay untouched until the push has landed.
    """
    blob = git("hash-object", "-w", "--stdin",
               input=json.dumps(payload) + "\n").stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}
        git("read-tree", parent, env=env)
        git("update-index", "--add", "--cacheinfo",
            f"100644,{blob},{LEASE_FILE}", env=env)
        tree = git("write-tree", env=env).stdout.strip()
    return git("commit-tree", tree, "-p", parent, "-m", message).stdout.strip()


def push(commit):
    """(ok, error). Origin rejects the push unless main is still an ancestor."""
    pushed = git("push", "--quiet", "origin", f"{commit}:{MAIN}", check=False)
    return pushed.returncode == 0, last_line(pushed, "push rejected")


def out(obj, code=0):
    print(json.dumps(obj))
    return code


def refuse(me, reason):
    return out({"acquired": False, "written": False, "me": me, "reason": reason}, 4)


def cmd_check(args):
    me = screen.runner_id()
    if not has_origin():
        return out(dict(describe({}, me), reason="no remote", me=me))
    try:
        base = fetch_main()
    except RuntimeError as e:
        return out(dict(describe({}, me), reason=f"unreachable: {e}", me=me))
    return out(dict(describe(read_lease(base), me), me=me, main=base))


def cmd_acquire(args):
    me = screen.runner_id()
    if not has_origin():
        return out({"acquired": True, "written": False, "reason": "no remote", "me": me})
    try:
        base = fetch_main()
    except RuntimeError as e:
        return refuse(me, f"origin unreachable: {e}")
    d = describe(read_lease(base), me)
    if held_by_other(d):
        return out(dict(d, acquired=False, me=me,
                        reason=f"held by {d['runner']} for {d['age_s']}s of {d['ttl_s']}s"), 3)
    head = git("rev-parse", "HEAD").stdout.strip()
    if not is_ancestor(base, head):
        where = "behind" if is_ancestor(head, base) else "diverged from"
        return refuse(me, f"local HEAD is {where} origin/main {base[:12]}; "
                          "a runner on a stale ledger must not cycle")
    if git("status", "--porcelain", "--", LEASE_FILE).stdout.strip():
        return refuse(me, f"{LEASE_FILE} has local changes")
    payload = {"runner": me, "started": screen.iso(now()), "ttl_s": args.ttl}
    try:
        commit = lease_commit(head, payload, f"lease: {me} acquired")
    except subprocess.CalledProcessError as e:
        return refuse(me, f"could not build the lease commit: {e.stderr.strip()}")
    ok, err = push(commit)
    if not ok:
        # Either the other runner's lease landed first (lost the race) or
        # origin refused the write. Re-read to say which; neither may cycle.
        try:
            d2 = describe(read_lease(fetch_main()), me)
        except RuntimeError:
            d2 = describe({}, me)
        if held_by_other(d2):
            return out(dict(d2, acquired=False, me=me, reason=f"lost the race: {err}"), 3)
        return refuse(me, f"push refused: {err}")
    result = {"acquired": True, "written": True, "me": me, "sha": commit,
              "started": payload["started"], "ttl_s": args.ttl,
              "replaced": d["runner"]}
    merged = git("merge", "--ff-only", "--quiet", commit, check=False)
    if merged.returncode != 0:
        # Harmless for exclusion: the cycle's push rebases over the commit.
        result["warning"] = ("lease is on origin but HEAD was not fast-forwarded: "
                             + last_line(merged, "merge failed"))
    return out(result)


def cmd_release(args):
    me = screen.runner_id()
    if not has_origin():
        return out({"released": False, "reason": "no remote", "me": me})
    err = "push rejected"
    for _ in range(RELEASE_ATTEMPTS):
        try:
            base = fetch_main()
        except RuntimeError as e:
            return out({"released": False, "me": me, "reason": f"unreachable: {e}"}, 1)
        d = describe(read_lease(base), me)
        if not d["held"]:
            return out({"released": False, "reason": "no lease held", "me": me})
        if not d["mine"]:
            return out({"released": False, "reason": f"held by {d['runner']}, not ours",
                        "me": me, "runner": d["runner"], "age_s": d["age_s"]})
        payload = {"runner": None, "released_by": me, "released": screen.iso(now())}
        try:
            commit = lease_commit(base, payload, f"lease: {me} released")
        except subprocess.CalledProcessError as e:
            return out({"released": False, "me": me,
                        "reason": f"could not build the release commit: {e.stderr.strip()}"}, 1)
        ok, err = push(commit)
        if ok:
            return out({"released": True, "me": me, "sha": commit, "age_s": d["age_s"]})
        # Main moved between the fetch and the push (a triggered cycle, the
        # deep retro): rebuild on the new tip and try again.
    return out({"released": False, "me": me, "reason": err}, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    a = sub.add_parser("acquire")
    a.add_argument("--ttl", type=int, default=DEFAULT_TTL_S,
                   help=f"seconds before a held lease expires (default {DEFAULT_TTL_S})")
    sub.add_parser("release")
    args = ap.parse_args()
    return {"check": cmd_check, "acquire": cmd_acquire,
            "release": cmd_release}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
