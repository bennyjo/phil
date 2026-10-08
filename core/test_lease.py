#!/usr/bin/env python3
"""Two simulated runners against a local bare remote, for core/lease.py.

PROTECTED CORE - the trading agent must not edit files under core/.

Each test seeds a bare "origin" with core/lease.py and what it imports, then
clones it twice: "cloud" and "operator", the two runners that share
origin/main. Offline and self-contained; CI runs it on every push.

Usage: python3 core/test_lease.py
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent
SEED = ("core/lease.py", "core/screen.py", "config/protected.json")
LEASE_FILE = "journal/lease.json"


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=check).stdout.strip()


class TwoRunners(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-lease-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        env = {k: v for k, v in os.environ.items()
               if k not in ("PHIL_RUNNER", "PHIL_PUSH_BY_LOOP")}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                   GIT_AUTHOR_NAME="runner", GIT_AUTHOR_EMAIL="runner@example.com",
                   GIT_COMMITTER_NAME="runner", GIT_COMMITTER_EMAIL="runner@example.com")
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.origin = self.tmp / "origin.git"
        git(self.tmp, "init", "--quiet", "--bare", "-b", "main", str(self.origin))
        seed = self.tmp / "seed"
        git(self.tmp, "init", "--quiet", "-b", "main", str(seed))
        for rel in SEED:
            (seed / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / rel, seed / rel)
        git(seed, "add", "-A")
        git(seed, "commit", "--quiet", "-m", "seed")
        git(seed, "push", "--quiet", str(self.origin), "main")
        self.cloud = self.clone("cloud")
        self.operator = self.clone("operator")

    def clone(self, name):
        path = self.tmp / name
        git(self.tmp, "clone", "--quiet", str(self.origin), str(path))
        return path

    def lease(self, runner, *args):
        proc = subprocess.run([sys.executable, str(runner / "core" / "lease.py"), *args],
                              capture_output=True, text=True,
                              env={**os.environ, "PHIL_RUNNER": runner.name})
        try:
            return proc.returncode, json.loads(proc.stdout)
        except json.JSONDecodeError:
            self.fail(f"lease.py {' '.join(args)} printed no JSON: {proc.stderr}")

    def origin_lease(self):
        shown = subprocess.run(["git", "show", f"main:{LEASE_FILE}"], cwd=self.origin,
                               capture_output=True, text=True)
        return json.loads(shown.stdout) if shown.returncode == 0 else None

    def origin_main(self):
        return git(self.origin, "rev-parse", "main")

    def sync(self, runner):
        git(runner, "fetch", "--quiet", "origin")
        git(runner, "merge", "--quiet", "--ff-only", "origin/main")

    def cycle(self, runner, name):
        """What a tick leaves behind: a cycle commit pushed to main."""
        log = runner / "journal" / "cycles.log"
        log.parent.mkdir(exist_ok=True)
        with log.open("a") as f:
            f.write(f"{name} cycle done\n")
        git(runner, "add", "-A")
        git(runner, "commit", "--quiet", "-m", f"cycle: {name}")
        git(runner, "push", "--quiet", "origin", "HEAD:main")

    def test_second_runner_skips_while_the_first_holds(self):
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["written"]), (0, True, True))
        self.assertEqual(self.origin_lease()["runner"], "cloud")
        self.assertEqual(git(self.cloud, "rev-parse", "HEAD"), self.origin_main(),
                         "the cycle must start from the commit that took the lease")

        self.sync(self.operator)
        before = self.origin_main()
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual((rc, got["acquired"], got["runner"]), (3, False, "cloud"))
        self.assertEqual(self.origin_main(), before)

        rc, got = self.lease(self.operator, "check")
        self.assertEqual((rc, got["held"], got["fresh"], got["mine"]), (0, True, True, False))

    def test_release_after_the_push_hands_the_lease_over(self):
        self.lease(self.cloud, "acquire")
        self.cycle(self.cloud, "20261008-2100")
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"]), (0, True))
        self.assertIsNone(self.origin_lease()["runner"])

        self.sync(self.operator)
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual((rc, got["acquired"]), (0, True))
        self.assertEqual(self.origin_lease()["runner"], "operator")
        subjects = git(self.origin, "log", "--format=%s", "main").splitlines()
        self.assertEqual(subjects[:4], ["lease: operator acquired", "lease: cloud released",
                                        "cycle: 20261008-2100", "lease: cloud acquired"])

    def test_lease_commits_change_only_the_lease_file(self):
        # The CI boundary guard holds every non-operator commit to this.
        self.lease(self.cloud, "acquire")
        self.lease(self.cloud, "release")
        for sha in git(self.origin, "rev-list", "main", "-2").split():
            files = git(self.origin, "diff-tree", "--no-commit-id", "--name-only", "-r", sha)
            self.assertEqual(files, LEASE_FILE)

    def test_racing_runners_exactly_one_wins(self):
        # Both runners read a free lease; the cloud's push lands between the
        # operator's read and its push. Deterministic: the operator's
        # lease.py runs in-process with push() wrapped to let the cloud in.
        spec = importlib.util.spec_from_file_location(
            "lease_operator", self.operator / "core" / "lease.py")
        mod = importlib.util.module_from_spec(spec)
        self.addCleanup(setattr, sys, "path", list(sys.path))
        self.addCleanup(sys.modules.pop, "screen", None)
        spec.loader.exec_module(mod)

        real_push, cloud_result = mod.push, {}

        def push_after_the_cloud(commit):
            cloud_result["rc"], cloud_result["out"] = self.lease(self.cloud, "acquire")
            return real_push(commit)

        before = git(self.operator, "rev-parse", "HEAD")
        stdout = io.StringIO()
        with mock.patch.object(mod, "push", push_after_the_cloud), \
                mock.patch.dict(os.environ, {"PHIL_RUNNER": "operator"}), \
                contextlib.redirect_stdout(stdout):
            rc = mod.cmd_acquire(argparse.Namespace(ttl=mod.DEFAULT_TTL_S))
        got = json.loads(stdout.getvalue())

        self.assertEqual(cloud_result["rc"], 0)
        self.assertEqual((rc, got["acquired"], got["runner"]), (3, False, "cloud"))
        self.assertIn("lost the race", got["reason"])
        self.assertEqual(self.origin_lease()["runner"], "cloud")
        self.assertEqual(git(self.operator, "rev-parse", "HEAD"), before,
                         "a lost race must leave the loser's branch alone")

    def test_concurrent_acquires_never_both_win(self):
        for _ in range(5):
            self.sync(self.cloud)
            self.sync(self.operator)
            results = {}
            start = threading.Barrier(2)

            def run(runner):
                start.wait()
                results[runner.name] = self.lease(runner, "acquire")

            threads = [threading.Thread(target=run, args=(r,)) for r in (self.cloud, self.operator)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            winners = [name for name, (rc, _) in results.items() if rc == 0]
            self.assertEqual(len(winners), 1, results)
            loser = "operator" if winners == ["cloud"] else "cloud"
            self.assertIn(results[loser][0], (3, 4), results)
            self.assertEqual(self.origin_lease()["runner"], winners[0])
            winner = self.cloud if winners == ["cloud"] else self.operator
            self.assertEqual(self.lease(winner, "release")[0], 0)

    def test_a_refused_write_fails_closed(self):
        # The cloud credential's HTTP 403 on refs/phil/lease, as a remote
        # that refuses every push. The old lease proceeded "unprotected".
        hook = self.origin / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho 'HTTP 403' >&2\nexit 1\n")
        hook.chmod(0o755)
        before = git(self.cloud, "rev-parse", "HEAD")
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["written"]), (4, False, False))
        self.assertIn("push refused", got["reason"])
        self.assertIsNone(self.origin_lease())
        self.assertEqual(git(self.cloud, "rev-parse", "HEAD"), before)

    def test_a_runner_on_a_stale_main_cannot_take_the_lease(self):
        # d5cfa982fa21: the operator runner traded on a diverged main whose
        # ledger lacked the cloud's open position on the same market.
        self.cycle(self.cloud, "20261004-0035")
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual(rc, 4)
        self.assertIn("behind", got["reason"])

        (self.operator / "local.txt").write_text("unpushed\n")
        git(self.operator, "add", "-A")
        git(self.operator, "commit", "--quiet", "-m", "cycle: 20261004-0136")
        git(self.operator, "fetch", "--quiet", "origin")
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual(rc, 4)
        self.assertIn("diverged", got["reason"])
        self.assertIsNone(self.origin_lease())

    def test_an_expired_lease_is_taken_over(self):
        self.lease(self.cloud, "acquire", "--ttl", "0")
        self.sync(self.operator)
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual((rc, got["acquired"], got["replaced"]), (0, True, "cloud"))
        self.assertEqual(self.origin_lease()["runner"], "operator")

    def test_a_runner_retakes_its_own_lease_after_a_crash(self):
        self.lease(self.cloud, "acquire")
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["replaced"]), (0, "cloud"))

    def test_release_leaves_the_other_runners_lease_alone(self):
        self.lease(self.cloud, "acquire")
        rc, got = self.lease(self.operator, "release")
        self.assertEqual((rc, got["released"]), (0, False))
        self.assertEqual(self.origin_lease()["runner"], "cloud")

    def test_release_lands_even_when_main_moved(self):
        # A triggered cycle or the deep retro pushes while the lease is held;
        # release must not need the holder's local main to be current.
        self.lease(self.cloud, "acquire")
        self.sync(self.operator)
        self.cycle(self.operator, "triggered")
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"]), (0, True))
        self.assertIsNone(self.origin_lease()["runner"])
        self.assertIn("cycle: triggered", git(self.origin, "log", "--format=%s", "main"))

    def test_unreachable_origin_fails_closed(self):
        git(self.cloud, "remote", "set-url", "origin", str(self.tmp / "missing.git"))
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"]), (4, False))
        self.assertIn("unreachable", got["reason"])

    def test_no_remote_has_nothing_to_protect(self):
        git(self.cloud, "remote", "remove", "origin")
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["written"]), (0, True, False))


if __name__ == "__main__":
    unittest.main()
