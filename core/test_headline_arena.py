#!/usr/bin/env python3
"""Offline tests for core/headline_arena.py: the API is mocked.

PROTECTED CORE - the trading agent must not edit files under core/.

What they pin: the step is off without credentials, only open daily
questions are listed or accepted, a submission needs a forecast row from
today, and the request body carries the probability vector and nothing
else. CI runs this on every push.

Usage: python3 core/test_headline_arena.py
"""
import contextlib
import datetime as dt
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("headline_arena", HERE / "headline_arena.py")
ha = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ha)

NOW = dt.datetime(2026, 10, 13, 12, 0, tzinfo=dt.timezone.utc)
CREDS = {"HEADLINE_ARENA_AGENT_ID": "agt_test", "HEADLINE_ARENA_CLIENT_SECRET": "s3cret"}


def challenge(cid="c-gc", ctype="daily", status="open", deadline="2026-10-13T14:00:00Z"):
    return {"id": cid, "asset": "GC", "challenge_type": ctype, "status": status,
            "deadline": deadline, "resolve_at": "2026-10-13T21:00:00Z",
            "open_price": 4195.5, "dead_zone_pct": 0.3, "question": "...",
            "resolution_criteria": "..."}


class FakeAPI:
    """Stands in for ha.request; records every call."""

    def __init__(self, challenges):
        self.challenges = {c["id"]: c for c in challenges}
        self.calls = []

    def __call__(self, method, path, body=None, token=None, agent_id=None):
        self.calls.append((method, path, body, token, agent_id))
        if path.startswith("/eval/challenges?"):
            return {"items": list(self.challenges.values())}
        if path == "/agent/auth/token":
            return {"access_token": "tok"}
        if method == "POST" and path.endswith("/predict"):
            return {"prediction_id": "p1", "counts_for_score": True, "note": None}
        if path.startswith("/eval/challenges/"):
            return self.challenges[path.rsplit("/", 1)[1]]
        if path.startswith("/eval/agents/"):
            return {"path": path}
        raise AssertionError(f"unexpected call {method} {path}")


class HeadlineArena(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.forecasts = pathlib.Path(tmp.name) / "forecasts.jsonl"
        self.forecasts.write_text(
            json.dumps({"id": "f-today", "ts": "2026-10-13T11:30:00Z"}) + "\n"
            + json.dumps({"id": "f-old", "ts": "2026-10-12T11:30:00Z"}) + "\n")
        for name, value in (("FORECASTS", self.forecasts),
                            ("CRED_FILE", pathlib.Path(tmp.name) / "none.json"),
                            ("now_utc", lambda: NOW)):
            p = mock.patch.object(ha, name, value)
            p.start()
            self.addCleanup(p.stop)

    def run_cli(self, argv, api, env=CREDS):
        out = io.StringIO()
        with mock.patch.dict("os.environ", env, clear=True), \
                mock.patch.object(ha, "request", api), contextlib.redirect_stdout(out):
            ha.main(argv)
        return json.loads(out.getvalue())

    def submit_argv(self, cid="c-gc", fid="f-today", p=(0.2, 0.5, 0.3)):
        return ["submit", "--challenge", cid, "--forecast-id", fid,
                "--bearish", str(p[0]), "--neutral", str(p[1]), "--bullish", str(p[2])]

    def test_off_without_credentials(self):
        api = FakeAPI([challenge()])
        for argv in (["open"], ["score"], self.submit_argv()):
            self.assertEqual(self.run_cli(argv, api, env={})["enabled"], False)
        self.assertEqual(api.calls, [])

    def test_open_lists_only_open_daily_questions(self):
        api = FakeAPI([challenge("c-gc"), challenge("c-flash", ctype="flash"),
                       challenge("c-late", deadline="2026-10-13T11:00:00Z")])
        out = self.run_cli(["open"], api)
        self.assertEqual([c["id"] for c in out["challenges"]], ["c-gc"])

    def test_submit_sends_the_vector_and_nothing_else(self):
        api = FakeAPI([challenge()])
        out = self.run_cli(self.submit_argv(), api)
        self.assertTrue(out["counts_for_score"])
        posts = [c for c in api.calls if c[1].endswith("/predict")]
        self.assertEqual(len(posts), 1)
        _, path, body, token, agent_id = posts[0]
        self.assertEqual(path, "/eval/challenges/c-gc/predict")
        self.assertEqual(set(body), {"probabilities", "idempotency_key"})
        self.assertEqual(body["probabilities"], {"bearish": 0.2, "neutral": 0.5, "bullish": 0.3})
        self.assertEqual((token, agent_id), ("tok", "agt_test"))

    def test_submit_refuses_non_daily_or_closed(self):
        for c in (challenge(ctype="flash"), challenge(status="resolved"),
                  challenge(deadline="2026-10-13T11:59:00Z")):
            api = FakeAPI([c])
            with self.assertRaises(SystemExit):
                self.run_cli(self.submit_argv(), api)
            self.assertFalse(any(x[1].endswith("/predict") for x in api.calls))

    def test_submit_needs_a_forecast_row_from_today(self):
        for fid in ("f-old", "f-missing"):
            api = FakeAPI([challenge()])
            with self.assertRaises(SystemExit):
                self.run_cli(self.submit_argv(fid=fid), api)
            self.assertEqual(api.calls, [])

    def test_vector_sums_to_exactly_one(self):
        p = ha.vector(1 / 3, 1 / 3, 1 / 3)
        self.assertEqual(round(sum(p.values()), 10), 1)
        with self.assertRaises(SystemExit):
            ha.vector(0.5, 0.5, 0.5)
        with self.assertRaises(SystemExit):
            ha.vector(-0.1, 0.6, 0.5)


if __name__ == "__main__":
    unittest.main()
