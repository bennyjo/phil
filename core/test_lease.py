#!/usr/bin/env python3
"""Two simulated runners against a local bare remote, for core/lease.py.

PROTECTED CORE - the trading agent must not edit files under core/.

Each test seeds a bare "origin" with core/lease.py and what it imports, then
clones it twice: "cloud" and "operator", the two runners that share
origin/main. The shared cases run twice: with origin's `lease` branch (where
the lease lives) and without it (the lease stays on main). Offline and
self-contained; CI runs it on every push.

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
SEED = ("core/lease.py", "core/screen.py", "core/funnel.py", "config/protected.json")
LEASE_FILE = "journal/lease.json"
# The command core/lease.py's docstring gives for moving the lease to its
# branch; setUp runs it as written, so the documented command stays tested.
CREATE_BRANCH = ("git push origin \"$(git commit-tree \"$(git mktree </dev/null)\" "
                 "-m 'lease: branch created')\":refs/heads/lease")


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=check).stdout.strip()


class Shared:
    """Cases that hold wherever the lease lives; mixed into the two classes below."""
    on_branch = None

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
        git(seed, "remote", "add", "origin", str(self.origin))
        git(seed, "push", "--quiet", "origin", "main")
        self.seed = seed
        if self.on_branch:
            self.create_lease_branch()
        self.cloud = self.clone("cloud")
        self.operator = self.clone("operator")

    def create_lease_branch(self):
        subprocess.run(["sh", "-c", CREATE_BRANCH], cwd=self.seed, check=True,
                       capture_output=True)

    @property
    def lease_branch(self):
        return "lease" if git(self.origin, "branch", "--list", "lease") else "main"

    def clone(self, name):
        path = self.tmp / name
        git(self.tmp, "clone", "--quiet", str(self.origin), str(path))
        return path

    def lease(self, runner, *args, name=None):
        proc = subprocess.run([sys.executable, str(runner / "core" / "lease.py"), *args],
                              capture_output=True, text=True,
                              env={**os.environ, "PHIL_RUNNER": name or runner.name})
        try:
            return proc.returncode, json.loads(proc.stdout)
        except json.JSONDecodeError:
            self.fail(f"lease.py {' '.join(args)} printed no JSON: {proc.stderr}")

    def origin_lease(self, branch=None):
        shown = subprocess.run(["git", "show", f"{branch or self.lease_branch}:{LEASE_FILE}"],
                               cwd=self.origin, capture_output=True, text=True)
        return json.loads(shown.stdout) if shown.returncode == 0 else None

    def origin_main(self):
        return git(self.origin, "rev-parse", "main")

    def subjects(self, branch):
        return git(self.origin, "log", "--format=%s", branch).splitlines()

    def plant_lease(self, payload):
        """Commit `payload` as the lease, as an old core/lease.py would have."""
        branch = self.lease_branch
        path = self.tmp / "planter"
        git(self.tmp, "clone", "--quiet", "-b", branch, str(self.origin), str(path))
        (path / LEASE_FILE).parent.mkdir(exist_ok=True)
        (path / LEASE_FILE).write_text(json.dumps(payload) + "\n")
        git(path, "add", "-A")
        git(path, "commit", "--quiet", "-m", "lease: cloud acquired")
        git(path, "push", "--quiet", "origin", f"HEAD:{branch}")

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
        self.assertEqual(self.subjects(self.lease_branch)[:3],
                         ["lease: operator acquired", "lease: cloud released",
                          "lease: cloud acquired"] if self.on_branch else
                         ["lease: operator acquired", "lease: cloud released",
                          "cycle: 20261008-2100"])

    def test_lease_commits_change_only_the_lease_file(self):
        # The CI boundary guard holds every non-operator commit on main to this.
        self.lease(self.cloud, "acquire")
        self.lease(self.cloud, "release")
        for sha in git(self.origin, "rev-list", self.lease_branch, "-2").split():
            files = git(self.origin, "diff-tree", "--no-commit-id", "--name-only", "-r", sha)
            self.assertEqual(files, LEASE_FILE)

    def operator_module(self):
        """The operator clone's lease.py, loaded in-process so a test can wrap it."""
        spec = importlib.util.spec_from_file_location(
            "lease_operator", self.operator / "core" / "lease.py")
        mod = importlib.util.module_from_spec(spec)
        self.addCleanup(setattr, sys, "path", list(sys.path))
        self.addCleanup(sys.modules.pop, "screen", None)
        spec.loader.exec_module(mod)
        return mod

    def operator_acquire(self, mod):
        stdout = io.StringIO()
        with mock.patch.dict(os.environ, {"PHIL_RUNNER": "operator"}), \
                contextlib.redirect_stdout(stdout):
            rc = mod.cmd_acquire(argparse.Namespace(ttl=mod.DEFAULT_TTL_S))
        return rc, json.loads(stdout.getvalue())

    def test_racing_runners_exactly_one_wins(self):
        # Both runners read a free lease; the cloud's push lands between the
        # operator's read and its push. Deterministic: the operator's
        # lease.py runs in-process with push() wrapped to let the cloud in.
        mod = self.operator_module()
        real_push, cloud_result = mod.push, {}

        def push_after_the_cloud(commit, ref):
            cloud_result["rc"], cloud_result["out"] = self.lease(self.cloud, "acquire")
            return real_push(commit, ref)

        before = git(self.operator, "rev-parse", "HEAD")
        with mock.patch.object(mod, "push", push_after_the_cloud):
            rc, got = self.operator_acquire(mod)

        self.assertEqual(cloud_result["rc"], 0)
        self.assertEqual((rc, got["acquired"], got["runner"]), (3, False, "cloud"))
        self.assertIn("lost the race", got["reason"])
        self.assertEqual(self.origin_lease()["runner"], "cloud")
        self.assertEqual(git(self.operator, "rev-parse", "HEAD"), before,
                         "a lost race must leave the loser's branch alone")

    def test_a_push_that_landed_without_an_answer_is_still_ours(self):
        mod = self.operator_module()
        real_push = mod.push

        def landed_but_no_answer(commit, ref):
            real_push(commit, ref)
            return False, "connection lost"

        with mock.patch.object(mod, "push", landed_but_no_answer):
            rc, got = self.operator_acquire(mod)
        self.assertEqual((rc, got["acquired"]), (0, True))
        self.assertEqual(self.lease(self.operator, "release")[1]["released"], True)

    def test_an_unsaved_holder_id_takes_no_lease(self):
        mod = self.operator_module()
        with mock.patch.object(mod, "save_holder", side_effect=OSError("disk full")):
            rc, got = self.operator_acquire(mod)
        self.assertEqual((rc, got["acquired"], got["written"]), (4, False, False))
        self.assertIsNone(self.origin_lease())

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
        write_hook(self.origin, "echo 'HTTP 403' >&2\nexit 1\n")
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
        self.assertEqual((rc, got["acquired"]), (0, True))
        self.assertTrue(got["replaced"].startswith("cloud-"), got)
        self.assertEqual(self.origin_lease()["runner"], "operator")

    def test_a_crashed_run_waits_out_its_lease_unless_released(self):
        # A checkout cannot tell its crashed run from a live one, so a second
        # acquire there must not extend the lease.
        self.lease(self.cloud, "acquire")
        held = self.origin_lease()
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["mine"]), (3, False, True))
        self.assertEqual(self.origin_lease(), held)
        self.assertEqual(self.lease(self.cloud, "release")[1]["released"], True)
        self.sync(self.cloud)
        self.assertEqual(self.lease(self.cloud, "acquire")[0], 0)

    def test_release_leaves_the_other_runners_lease_alone(self):
        self.lease(self.cloud, "acquire")
        rc, got = self.lease(self.operator, "release")
        self.assertEqual((rc, got["released"]), (0, False))
        self.assertEqual(self.origin_lease()["runner"], "cloud")

    def second_cloud_run(self):
        """A second run under the name "cloud", in its own fresh clone."""
        path = self.clone("cloud-second-run")
        return lambda *args: self.lease(path, *args, name="cloud")

    def test_a_second_run_cannot_extend_a_live_lease_of_the_same_runner(self):
        # 2026-10-22 16:24Z: a second cloud session read a live "cloud" lease
        # as its own and overwrote it ("replaced": "cloud").
        self.lease(self.cloud, "acquire")
        held = self.origin_lease()
        second = self.second_cloud_run()
        rc, got = second("acquire")
        self.assertEqual((rc, got["acquired"], got["runner"]), (3, False, "cloud"))
        self.assertEqual(self.origin_lease(), held)

    def test_a_second_run_cannot_release_a_live_lease_of_the_same_runner(self):
        # 2026-10-22 16:25Z: the same session then released the lease, leaving
        # the first run's cycle unprotected for the rest of its time.
        self.lease(self.cloud, "acquire")
        held = self.origin_lease()
        second = self.second_cloud_run()
        rc, got = second("release")
        self.assertEqual((rc, got["released"]), (0, False))
        self.assertIn("not ours", got["reason"])
        self.assertEqual(self.origin_lease(), held)

        rc, got = second("check")
        self.assertEqual((rc, got["held"], got["fresh"], got["mine"]), (0, True, True, False))

    def test_a_run_past_its_ttl_cannot_release_its_successors_lease(self):
        # A slow run outlives its lease and the next run of the same runner
        # takes over; the slow run's release must not end the new lease.
        self.lease(self.cloud, "acquire", "--ttl", "0")
        second = self.second_cloud_run()
        rc, got = second("acquire")
        self.assertEqual((rc, got["acquired"]), (0, True))
        self.assertTrue(got["replaced"].startswith("cloud-"), got)
        held = self.origin_lease()
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"]), (0, False))
        self.assertEqual(self.origin_lease(), held)

    def test_each_acquire_gets_its_own_holder_and_keeps_the_runner_name(self):
        self.lease(self.cloud, "acquire")
        first = self.origin_lease()
        self.lease(self.cloud, "release")
        self.sync(self.cloud)
        self.lease(self.cloud, "acquire")
        second = self.origin_lease()
        self.assertEqual((first["runner"], second["runner"]), ("cloud", "cloud"))
        self.assertNotEqual(first["holder"], second["holder"])
        self.assertEqual((self.cloud / ".git" / "phil-lease-holder").read_text().strip(),
                         second["holder"], "the holder id must stay in the git directory")

    def test_a_lease_without_a_holder_is_nobodys_until_it_expires(self):
        # A lease written before holder ids existed: no run can prove it is
        # theirs, so it stays until its ttl runs out.
        self.plant_lease({"runner": "cloud", "started": "2999-01-01T00:00:00Z",
                          "ttl_s": 10 ** 12})
        self.sync(self.cloud)
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"]), (0, False))
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"]), (3, False))

    def test_release_lands_even_when_main_moved(self):
        # A triggered cycle or the deep retro pushes while the lease is held;
        # release must not need the holder's local main to be current.
        self.lease(self.cloud, "acquire")
        self.sync(self.operator)
        self.cycle(self.operator, "triggered")
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"]), (0, True))
        self.assertIsNone(self.origin_lease()["runner"])
        self.assertIn("cycle: triggered", self.subjects("main"))

    def test_unreachable_origin_fails_closed(self):
        git(self.cloud, "remote", "set-url", "origin", str(self.tmp / "missing.git"))
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"]), (4, False))
        self.assertIn("unreachable", got["reason"])

    def test_no_remote_has_nothing_to_protect(self):
        git(self.cloud, "remote", "remove", "origin")
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["written"]), (0, True, False))


def write_hook(origin, body):
    hook = origin / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\n" + body)
    hook.chmod(0o755)


class OnTheLeaseBranch(Shared, unittest.TestCase):
    on_branch = True

    def test_the_lease_never_adds_a_commit_to_main(self):
        main, head = self.origin_main(), git(self.cloud, "rev-parse", "HEAD")
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["ref"]), (0, True, "lease"))
        self.assertEqual((self.origin_main(), git(self.cloud, "rev-parse", "HEAD")),
                         (main, head), "acquire must leave main and HEAD alone")
        self.cycle(self.cloud, "20261108-2213")
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"], got["ref"]), (0, True, "lease"))
        self.assertEqual(self.subjects("main"), ["cycle: 20261108-2213", "seed"])
        self.assertEqual(self.subjects("lease"), ["lease: cloud released",
                                                  "lease: cloud acquired",
                                                  "lease: branch created"])
        self.assertEqual(git(self.origin, "ls-tree", "-r", "--name-only", "lease"), LEASE_FILE,
                         "the lease branch holds the lease file and nothing else")

    def test_a_refused_branch_push_fails_closed(self):
        # A credential that may push main but not the lease branch.
        write_hook(self.origin, 'while read old new ref; do\n'
                   '  [ "$ref" = refs/heads/lease ] && echo "HTTP 403" >&2 && exit 1\n'
                   'done\nexit 0\n')
        main = self.origin_main()
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["written"]), (4, False, False))
        self.assertIn("push refused", got["reason"])
        self.assertEqual(self.origin_main(), main)

    def test_deleting_the_branch_moves_the_lease_back_to_main(self):
        self.lease(self.cloud, "acquire")
        self.lease(self.cloud, "release")
        git(self.origin, "branch", "-D", "lease")
        # The cloud still has a tracking ref for the deleted branch.
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["ref"]), (0, True, "main"))
        self.assertEqual(self.origin_lease("main")["runner"], "cloud")


class OnMainUntilTheBranchExists(Shared, unittest.TestCase):
    on_branch = False

    def test_acquire_starts_the_cycle_from_the_lease_commit(self):
        rc, got = self.lease(self.cloud, "acquire")
        self.assertEqual((rc, got["acquired"], got["ref"]), (0, True, "main"))
        self.assertEqual(git(self.cloud, "rev-parse", "HEAD"), self.origin_main(),
                         "the cycle must start from the commit that took the lease")

    def test_a_lease_taken_on_main_holds_once_the_branch_appears(self):
        # The branch is created while a cycle that took its lease on main is
        # in flight: the other runner must still wait, and the holder's
        # release must still clear its lease.
        self.lease(self.cloud, "acquire")
        self.create_lease_branch()
        self.sync(self.operator)
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual((rc, got["acquired"], got["ref"]), (3, False, "main"))
        self.assertIn("held on main", got["reason"])
        rc, got = self.lease(self.cloud, "release")
        self.assertEqual((rc, got["released"], got["ref"]), (0, True, "main"))
        self.assertIsNone(self.origin_lease("main")["runner"])
        self.sync(self.operator)
        rc, got = self.lease(self.operator, "acquire")
        self.assertEqual((rc, got["acquired"], got["ref"]), (0, True, "lease"))


if __name__ == "__main__":
    unittest.main()
