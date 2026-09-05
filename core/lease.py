#!/usr/bin/env python3
"""Runner lease: one FULL cycle at a time across Phil's runners.

PROTECTED CORE - the trading agent must not edit files under core/.

Why this exists (operator, 2026-09-06): two runners cycle on the same hours,
the cloud routine and the operator machine's loop.sh. CYCLE.md step 0's
collision guard reads origin/main's tip, so it only sees a cycle that has
already committed; two FULL cycles that start from the same tip inside the
same minute cannot see each other. On 2026-09-04 00:16Z both runners scanned,
both ran 15 Haiku batches, both researched the NFP bracket and both decided
to trade the same leg (journal/proposals.md, "collision-guard gap").

The lease is a ref on origin, refs/phil/lease, pointing at an empty commit
whose message is one JSON line: {"runner", "started", "ttl_s"}. It lives on
the remote and not in any working tree, so both runners see it within a
fetch. A runner that finds a fresh lease held by the other runner runs a
LIGHT tick (CYCLE.md step 0); the holder releases the lease after its push.
A run that dies mid-cycle leaves a lease that expires on its own after
`ttl_s`, so nothing can wedge the other runner for longer than one cycle.

Atomicity comes from git, not from us: `acquire` pushes with
--force-with-lease pinned to the exact sha it observed (or to "absent"), so
two runners racing for a free lease cannot both win - the second push is
rejected and reports "acquired": false. `release` deletes with the same
pin, so a runner can only release the lease it holds.

Runner identity is core/screen.py's runner_id(): $PHIL_RUNNER, else
"operator" when loop.sh's PHIL_PUSH_BY_LOOP is set, else "cloud". On the
operator machine loop.sh acquires and releases in the interactive shell
(the keyring is unlocked there; a push from inside `claude -p` hangs), and
tells the cycle agent the verdict through PHIL_LEASE. In the cloud the
cycle agent runs acquire and release itself.

Usage:
  python3 core/lease.py check                # never writes; prints JSON
  python3 core/lease.py acquire [--ttl S]    # exit 0 acquired, 3 held by other
  python3 core/lease.py release              # exit 0 released or not ours
Every subcommand prints one JSON object. No origin remote, or a fetch that
fails, reports "acquired": true with "reason": "no remote" - the lease
cannot protect a runner that cannot reach origin, and it must never block
one either. Nothing here touches journal/ or strategy/.
"""
import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import screen  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEASE_REF = "refs/phil/lease"
LOCAL_REF = "refs/phil/lease-remote"
DEFAULT_TTL_S = 50 * 60
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=check, timeout=120)


def has_origin():
    return git("remote", "get-url", "origin", check=False).returncode == 0


def now():
    return dt.datetime.now(dt.timezone.utc)


def read_remote():
    """(sha, payload) of the remote lease, (None, None) when free.

    Raises RuntimeError when origin cannot be reached, which callers turn
    into the fail-open verdict documented above.
    """
    ls = git("ls-remote", "--exit-code", "origin", LEASE_REF, check=False)
    if ls.returncode == 2:
        return None, None
    if ls.returncode != 0:
        raise RuntimeError(ls.stderr.strip() or "ls-remote failed")
    sha = ls.stdout.split()[0]
    fetched = git("fetch", "--no-tags", "origin", f"+{LEASE_REF}:{LOCAL_REF}",
                  check=False)
    if fetched.returncode != 0:
        raise RuntimeError(fetched.stderr.strip() or "fetch failed")
    body = git("log", "-1", "--format=%B", LOCAL_REF).stdout.strip()
    try:
        payload = json.loads(body.splitlines()[0])
    except (json.JSONDecodeError, IndexError):
        payload = {}
    return sha, payload


def describe(sha, payload, me):
    if sha is None:
        return {"held": False, "mine": False, "fresh": False, "runner": None,
                "age_s": None, "sha": None}
    try:
        started = dt.datetime.fromisoformat(str(payload.get("started")).replace("Z", "+00:00"))
        age = int((now() - started).total_seconds())
    except (TypeError, ValueError):
        age = None
    ttl = int(payload.get("ttl_s") or DEFAULT_TTL_S)
    fresh = age is not None and 0 <= age < ttl
    runner = payload.get("runner")
    return {"held": True, "mine": runner == me, "fresh": fresh,
            "runner": runner, "age_s": age, "ttl_s": ttl, "sha": sha}


def out(obj, code=0):
    print(json.dumps(obj))
    return code


def cmd_check(args):
    me = screen.runner_id()
    if not has_origin():
        return out({"held": False, "mine": False, "fresh": False, "runner": None,
                    "age_s": None, "sha": None, "reason": "no remote", "me": me})
    try:
        sha, payload = read_remote()
    except RuntimeError as e:
        return out({"held": False, "mine": False, "fresh": False, "runner": None,
                    "age_s": None, "sha": None, "reason": f"unreachable: {e}", "me": me})
    d = describe(sha, payload, me)
    d["me"] = me
    return out(d)


def cmd_acquire(args):
    me = screen.runner_id()
    if not has_origin():
        return out({"acquired": True, "reason": "no remote", "me": me})
    try:
        sha, payload = read_remote()
    except RuntimeError as e:
        return out({"acquired": True, "reason": f"unreachable: {e}", "me": me})
    d = describe(sha, payload, me)
    if d["held"] and d["fresh"] and not d["mine"]:
        d.update(acquired=False, me=me,
                 reason=f"held by {d['runner']} for {d['age_s']}s of {d['ttl_s']}s")
        return out(d, 3)
    payload = {"runner": me, "started": screen.iso(now()), "ttl_s": args.ttl}
    commit = git("commit-tree", EMPTY_TREE, "-m", json.dumps(payload)).stdout.strip()
    expect = f"{LEASE_REF}:{sha}" if sha else f"{LEASE_REF}:"
    pushed = git("push", "--quiet", f"--force-with-lease={expect}", "origin",
                 f"{commit}:{LEASE_REF}", check=False)
    if pushed.returncode != 0:
        # Someone took it between our read and our push. Report what is
        # there now; the caller treats this exactly like a fresh foreign lease.
        try:
            sha2, payload2 = read_remote()
            d2 = describe(sha2, payload2, me)
        except RuntimeError:
            d2 = {}
        d2.update(acquired=False, me=me, reason="lost the race: " +
                  (pushed.stderr.strip().splitlines() or ["push rejected"])[-1])
        return out(d2, 3)
    return out({"acquired": True, "me": me, "sha": commit, "started": payload["started"],
                "ttl_s": args.ttl, "replaced": d["runner"] if d["held"] else None})


def cmd_release(args):
    me = screen.runner_id()
    if not has_origin():
        return out({"released": False, "reason": "no remote", "me": me})
    try:
        sha, payload = read_remote()
    except RuntimeError as e:
        return out({"released": False, "reason": f"unreachable: {e}", "me": me})
    d = describe(sha, payload, me)
    if not d["held"]:
        return out({"released": False, "reason": "no lease held", "me": me})
    if not d["mine"]:
        return out({"released": False, "reason": f"held by {d['runner']}, not ours",
                    "me": me, "runner": d["runner"], "age_s": d["age_s"]})
    pushed = git("push", "--quiet", f"--force-with-lease={LEASE_REF}:{sha}", "origin",
                 f":{LEASE_REF}", check=False)
    if pushed.returncode != 0:
        return out({"released": False, "me": me, "reason":
                    (pushed.stderr.strip().splitlines() or ["push rejected"])[-1]}, 1)
    return out({"released": True, "me": me, "sha": sha, "age_s": d["age_s"]})


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
