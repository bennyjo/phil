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

Where it lived first (operator, 2026-10-08): journal/lease.json on origin's
main. The first lease was a custom ref, refs/phil/lease, and the cloud
credential cannot push custom refs (HTTP 403 since 2026-09-06) while it
pushes main on every cycle, so every cloud cycle ran unprotected. Main forked
(an operator merge of a 126/142-commit fork on 2026-10-05, the next fork 52
minutes later), the shared screener quota ran to 195/150 batches, and the
operator runner placed d5cfa982fa21 on top of the open 9a2944acc280
(DEEP-2026-10-08 P3).

Where it lives (operator, 2026-11-08): journal/lease.json on origin's `lease`
branch, a branch that holds nothing else. On main the lease was two commits
per cycle, half of main's history, and each one started its own CI run. The
lease uses that branch only when origin has it, and main otherwise, so the
code ships before the branch exists. To move the lease, create the branch
from the cloud routine's environment, because the cloud credential is the one
that may lack the right to push it:

  git push origin "$(git commit-tree "$(git mktree </dev/null)" -m 'lease: branch created')":refs/heads/lease

A refused push leaves everything as it was. Deleting the branch moves the
lease back to main. While the lease is on its branch, acquire also refuses a
live lease still held on main, and release clears whichever of the two is
this run's, so a cycle in flight when the branch appears stays protected.

The file holds one JSON object: {"runner", "holder", "started", "ttl_s"}
while held, {"runner": null, "released_by", "released"} once released; a
missing file is free too. acquire and release each push one commit that
changes nothing but this file, as a plain fast-forward push to the lease
branch (or main). Origin applies a push only while that branch still points
where the pusher saw it, so of two runners racing for a free lease exactly
one push lands; the loser re-reads and yields.

acquire needs HEAD to contain origin/main: a runner whose main is behind or
diverged trades on a stale ledger. ledger.py's duplicate-position guard
missed d5cfa982fa21 because the operator runner's diverged main did not have
9a2944acc280. On the lease branch, acquire leaves HEAD alone. On main, it
builds its commit on HEAD and fast-forwards HEAD onto it, so the cycle starts
from the commit that took the lease. release builds its commit on origin's
tip and leaves the local branch alone, so it works whatever the cycle's own
push did.

A runner that does not get the lease skips the tick; it does not run a LIGHT
one. A LIGHT tick still settles and commits ledger and forecast rows, which
are not union-merged (.gitattributes), so a LIGHT tick next to the holder's
cycle makes one of the two pushes conflict and fork main. The holder's own
cycle settles and monitors, so the skipped tick loses nothing. That covers
both refusals: held by another run (exit 3) and not written (exit 4:
origin unreachable, the push refused, or local main behind or diverged). A
runner that cannot reach origin could not publish its cycle either. A run
that dies mid-cycle leaves a lease that expires on its own after `ttl_s`, so
nothing wedges the other runner for longer than one cycle.

Runner identity is core/screen.py's runner_id(): $PHIL_RUNNER, else
"operator" when loop.sh's PHIL_PUSH_BY_LOOP is set, else "cloud". On the
operator machine loop.sh acquires and releases in the interactive shell
(the keyring is unlocked there; a push from inside `claude -p` hangs), and
tells the cycle agent through PHIL_LEASE. In the cloud the cycle agent runs
acquire and release itself.

Run identity (operator, 2026-11-05): the runner name cannot tell two runs of
one runner apart. On 2026-10-22 16:24Z a second cloud session read a live
"cloud" lease as its own, overwrote it, then released it, so the first
session's cycle ran unprotected. Each acquire now creates a holder id
(core/screen.py's new_holder_id()), saves it to phil-lease-holder in the
checkout's git directory, and pushes it in the lease. The file carries the id
from acquire to release, which run as separate processes, and no commit can
pick it up. Only a release from the checkout whose file matches the lease's
holder clears the lease. acquire refuses any fresh lease, whoever holds it, so
no run can extend one; a lease with no holder matches nothing. A run that
dies mid-cycle therefore blocks the next ones until its ttl runs out. To clear
it sooner, the operator runs `core/lease.py release` in the same checkout.

Usage:
  python3 core/lease.py check                # never writes; prints JSON
  python3 core/lease.py acquire [--ttl S]    # exit 0 acquired, 3 held, 4 not written
  python3 core/lease.py release              # exit 0 released or not ours, 1 push failed
Every subcommand prints one JSON object; "ref" names the branch the lease
was read from. Without an origin remote there is no shared main to protect,
so acquire reports "acquired": true with "written": false. The only files
written here are journal/lease.json (on main, only while origin has no lease
branch) and the holder file in the git directory.
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
LEASE_BRANCH = "refs/heads/lease"
REMOTE_LEASE = "refs/remotes/origin/lease"
# A pattern, so a missing lease branch fetches nothing instead of failing,
# and --prune drops the tracking ref once origin deletes the branch.
LEASE_REFSPEC = "+refs/heads/lease*:refs/remotes/origin/lease*"
DEFAULT_TTL_S = 50 * 60
RELEASE_ATTEMPTS = 3
HOLDER_FILE = "phil-lease-holder"


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


def fetch():
    """(origin/main's sha, origin/lease's sha or None) after one fresh fetch.

    Raises RuntimeError when origin cannot be reached; acquire turns that
    into a refusal, since a runner that cannot reach origin cannot publish.
    """
    fetched = git("fetch", "--no-tags", "--quiet", "--prune", "origin",
                  f"+{MAIN}:{REMOTE_MAIN}", LEASE_REFSPEC, check=False)
    if fetched.returncode != 0:
        raise RuntimeError(last_line(fetched, "fetch failed"))
    lease = git("rev-parse", "--verify", "--quiet", REMOTE_LEASE, check=False)
    return git("rev-parse", REMOTE_MAIN).stdout.strip(), lease.stdout.strip() or None


def where(main, lease):
    """(branch, tip) that holds the lease: the lease branch if origin has one."""
    return (LEASE_BRANCH, lease) if lease else (MAIN, main)


def short(ref):
    return ref.rpartition("/")[2]


def read_lease(rev):
    """The lease payload at `rev`; {} (free) when absent or unreadable."""
    shown = git("show", f"{rev}:{LEASE_FILE}", check=False)
    try:
        payload = json.loads(shown.stdout) if shown.returncode == 0 else {}
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def holder_path():
    """Inside the git directory, so no commit can pick the file up."""
    return ROOT / git("rev-parse", "--git-path", HOLDER_FILE).stdout.strip()


def read_holder():
    """The holder id of this checkout's last acquire; None if it has none."""
    try:
        return holder_path().read_text().strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def save_holder(holder):
    holder_path().write_text(holder + "\n")


def describe(payload, my_holder):
    runner = payload.get("runner")
    if not runner:
        return {"held": False, "mine": False, "fresh": False, "runner": None,
                "holder": None, "age_s": None}
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
    holder = payload.get("holder")
    mine = my_holder is not None and holder == my_holder
    return {"held": True, "mine": mine, "fresh": fresh, "runner": runner,
            "holder": holder, "age_s": age, "ttl_s": ttl}


def is_live(d):
    return d["held"] and d["fresh"]


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


def push(commit, ref):
    """(ok, error). Origin rejects the push unless `ref` is still an ancestor."""
    pushed = git("push", "--quiet", "origin", f"{commit}:{ref}", check=False)
    return pushed.returncode == 0, last_line(pushed, "push rejected")


def out(obj, code=0):
    print(json.dumps(obj))
    return code


def refuse(me, reason):
    return out({"acquired": False, "written": False, "me": me, "reason": reason}, 4)


def held(d, me, ref, reason):
    return out(dict(d, acquired=False, me=me, ref=short(ref), reason=reason), 3)


def cmd_check(args):
    me = screen.runner_id()
    if not has_origin():
        return out(dict(describe({}, None), reason="no remote", me=me))
    try:
        main_sha, lease_sha = fetch()
    except RuntimeError as e:
        return out(dict(describe({}, None), reason=f"unreachable: {e}", me=me))
    ref, tip = where(main_sha, lease_sha)
    return out(dict(describe(read_lease(tip), read_holder()), me=me, ref=short(ref),
                    main=main_sha))


def cmd_acquire(args):
    me = screen.runner_id()
    if not has_origin():
        return out({"acquired": True, "written": False, "reason": "no remote", "me": me})
    try:
        main_sha, lease_sha = fetch()
    except RuntimeError as e:
        return refuse(me, f"origin unreachable: {e}")
    ref, tip = where(main_sha, lease_sha)
    d = describe(read_lease(tip), read_holder())
    if is_live(d):
        return held(d, me, ref, f"held by {d['holder'] or d['runner']} "
                                f"for {d['age_s']}s of {d['ttl_s']}s")
    if ref == LEASE_BRANCH:
        # A run that took the lease on main before the lease branch existed.
        on_main = describe(read_lease(main_sha), None)
        if is_live(on_main):
            return held(on_main, me, MAIN, f"held on main by "
                        f"{on_main['holder'] or on_main['runner']} "
                        f"for {on_main['age_s']}s of {on_main['ttl_s']}s")
    head = git("rev-parse", "HEAD").stdout.strip()
    if not is_ancestor(main_sha, head):
        state = "behind" if is_ancestor(head, main_sha) else "diverged from"
        return refuse(me, f"local HEAD is {state} origin/main {main_sha[:12]}; "
                          "a runner on a stale ledger must not cycle")
    if ref == MAIN and git("status", "--porcelain", "--", LEASE_FILE).stdout.strip():
        return refuse(me, f"{LEASE_FILE} has local changes")
    holder = screen.new_holder_id()
    payload = {"runner": me, "holder": holder, "started": screen.iso(now()), "ttl_s": args.ttl}
    try:
        # On main, build on HEAD so the cycle can start from this commit.
        commit = lease_commit(tip if ref == LEASE_BRANCH else head, payload,
                              f"lease: {me} acquired")
    except subprocess.CalledProcessError as e:
        return refuse(me, f"could not build the lease commit: {e.stderr.strip()}")
    # Saved before the push: a lease on origin always has its id on disk, and
    # an id whose push fails matches nothing.
    try:
        save_holder(holder)
    except (OSError, subprocess.SubprocessError) as e:
        return refuse(me, f"could not save the holder id: {e}")
    ok, err = push(commit, ref)
    if not ok:
        try:
            latest = read_lease(where(*fetch())[1])
        except RuntimeError:
            latest = {}
        # Our own id on origin means the push landed and only the answer was
        # lost. Otherwise another run's lease landed first (lost the race) or
        # origin refused the write. Re-read to say which; neither may cycle.
        if latest.get("holder") != holder:
            d2 = describe(latest, None)
            if is_live(d2):
                return held(d2, me, ref, f"lost the race: {err}")
            return refuse(me, f"push refused: {err}")
    result = {"acquired": True, "written": True, "me": me, "ref": short(ref),
              "holder": holder, "sha": commit, "started": payload["started"],
              "ttl_s": args.ttl, "replaced": d["holder"] or d["runner"]}
    if ref == MAIN:
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
    my_holder = read_holder()
    err = "push rejected"
    for _ in range(RELEASE_ATTEMPTS):
        try:
            main_sha, lease_sha = fetch()
        except RuntimeError as e:
            return out({"released": False, "me": me, "reason": f"unreachable: {e}"}, 1)
        spots = [where(main_sha, lease_sha)]
        if lease_sha:
            # This run may have taken its lease on main before the branch existed.
            spots.append((MAIN, main_sha))
        found = [(ref, tip, describe(read_lease(tip), my_holder)) for ref, tip in spots]
        ref, tip, d = next((f for f in found if f[2]["mine"]), found[0])
        if not d["held"]:
            return out({"released": False, "reason": "no lease held", "me": me,
                        "ref": short(ref)})
        if not d["mine"]:
            return out({"released": False,
                        "reason": f"held by {d['holder'] or d['runner']}, not ours",
                        "me": me, "ref": short(ref), "runner": d["runner"],
                        "holder": d["holder"], "age_s": d["age_s"]})
        payload = {"runner": None, "released_by": me, "released": screen.iso(now())}
        try:
            commit = lease_commit(tip, payload, f"lease: {me} released")
        except subprocess.CalledProcessError as e:
            return out({"released": False, "me": me,
                        "reason": f"could not build the release commit: {e.stderr.strip()}"}, 1)
        ok, err = push(commit, ref)
        if ok:
            return out({"released": True, "me": me, "ref": short(ref), "sha": commit,
                        "age_s": d["age_s"]})
        # The branch moved between the fetch and the push (on main: a
        # triggered cycle, the deep retro): rebuild on the new tip and retry.
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
