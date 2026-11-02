#!/usr/bin/env python3
"""Offline tests for core/real.py: real orders and settle reconciliation.

PROTECTED CORE - the trading agent must not edit files under core/.

The connect skill scripts and the signer healthcheck are stubbed, and the
real ledger points at a temporary file, so nothing touches funds or the
network. V2 tests replay core/fixtures/polymarket_v2.json: recorded Gamma
records, and what Pearl Connect v0.1.13's scripts print for them. CI runs it
on every push.

Usage: python3 core/test_real.py
"""
import contextlib
import datetime as dt
import importlib.util
import io
import json
import pathlib
import shutil
import signal
import stat
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = json.loads((REPO / "core" / "fixtures" / "polymarket_v2.json").read_text())
GAMMA, IDS, CONNECT = FIXTURE["gamma"], FIXTURE["ids"], FIXTURE["connect"]
CAPS = {"max_stake_usd": 1, "allowed_edge_classes": ["info-race"],
        "max_open_positions": 5, "daily_stake_cap_usd": 5}


def load_real():
    spec = importlib.util.spec_from_file_location("real", REPO / "core" / "real.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Place(unittest.TestCase):
    """V1 twins place as before; a market Phil can't trade is refused before
    any money moves."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = load_real()
        self.real.REAL_LEDGER = self.tmp / "real-ledger.jsonl"
        self.real.PAPER_LEDGER = self.tmp / "ledger.jsonl"
        self.real.PAPER_LEDGER.write_text(json.dumps(
            {"id": "p1", "market_id": "7", "token_id": "9", "edge_class": "info-race"}) + "\n")

    def place(self, gamma_market):
        scripts = []

        def run_script(store, name, *args, timeout=180):
            scripts.append(name)
            return 0, {"ok": True}, ""

        args = mock.Mock(paper_id="p1", usd=None)
        out = io.StringIO()
        with mock.patch.object(self.real, "load_protected", return_value=({}, CAPS)), \
             mock.patch.object(self.real, "store_path", return_value=self.tmp), \
             mock.patch.object(self.real, "healthy", return_value=True), \
             mock.patch.object(self.real, "run_script", side_effect=run_script), \
             mock.patch.object(self.real.pmapi, "gamma_market", gamma_market), \
             contextlib.redirect_stdout(out):
            try:
                self.real.cmd_place(args)
                code = 0
            except SystemExit as e:
                code = e.code
        return code, scripts, out.getvalue()

    def assert_refused(self, code, scripts):
        self.assertNotEqual(code, 0)
        self.assertEqual(scripts, [])
        self.assertFalse(self.real.REAL_LEDGER.exists())

    def test_v2_market_without_position_ids_is_refused_before_any_money_moves(self):
        code, scripts, out = self.place(lambda _id: {"version": "v2"})
        self.assert_refused(code, scripts)
        self.assertIn("read-only", out)

    def test_untagged_market_is_refused(self):
        code, scripts, _out = self.place(lambda _id: {})
        self.assert_refused(code, scripts)

    def test_unreadable_version_fails_closed(self):
        def down(_id):
            raise RuntimeError("gamma down")
        code, scripts, out = self.place(down)
        self.assert_refused(code, scripts)
        self.assertIn("gamma down", out)

    def test_v1_market_still_places(self):
        code, scripts, _out = self.place(lambda _id: {"version": "v1"})
        self.assertEqual(code, 0)
        self.assertEqual(scripts, ["funds.py", "trade.py"])


class ConnectStub(unittest.TestCase):
    """A temp real ledger and Connect scripts that answer from the fixture."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = load_real()
        self.real.REAL_LEDGER = self.tmp / "real-ledger.jsonl"
        self.real.PAPER_LEDGER = self.tmp / "ledger.jsonl"
        self.calls = []

    def run_cmd(self, fn, args, replies, gamma, caps=CAPS):
        """Run one real.py command; `replies` maps a script name to its fixture."""
        def run_script(store, name, *script_args, timeout=180):
            self.calls.append((name, *map(str, script_args)))
            reply = replies[name]
            return tuple(reply() if callable(reply) else reply)

        out = io.StringIO()
        with mock.patch.object(self.real, "load_protected", return_value=({}, caps)), \
             mock.patch.object(self.real, "store_path", return_value=self.tmp), \
             mock.patch.object(self.real, "healthy", return_value=True), \
             mock.patch.object(self.real, "run_script", side_effect=run_script), \
             mock.patch.object(self.real.pmapi, "gamma_market", gamma), \
             contextlib.redirect_stdout(out):
            try:
                fn(args)
                code = 0
            except SystemExit as e:
                code = e.code
        return code, out.getvalue()

    def scripts(self):
        return [call[0] for call in self.calls]

    def rows(self):
        return {r["id"]: r for r in self.real.real_rows()}

    def history(self):
        return self.real.read_jsonl(self.real.REAL_LEDGER)


class PlaceV2(ConnectStub):
    """Binary V2 twins trade through Connect under every existing real-mode cap."""

    OUTCOME = json.loads(GAMMA["binary_open"]["outcomes"])[0]

    def setUp(self):
        super().setUp()
        self.twin()

    def twin(self, market=GAMMA["binary_open"], token=IDS["open"], outcome=OUTCOME,
             paper_id="p1"):
        with self.real.PAPER_LEDGER.open("a") as f:
            f.write(json.dumps({"id": paper_id, "market_id": market["id"], "token_id": token,
                                "outcome": outcome, "question": market["question"],
                                "edge_class": "info-race"}) + "\n")

    def place(self, market=GAMMA["binary_open"], paper_id="p1", usd=None, caps=CAPS,
              status="status_v2_ready", buy="buy_matched"):
        replies = {"deposit_wallet.py": CONNECT[status], "funds.py": CONNECT["top_up"],
                   "trade.py": CONNECT[buy] if isinstance(buy, str) else buy}
        args = mock.Mock(paper_id=paper_id, usd=usd)
        return self.run_cmd(self.real.cmd_place, args, replies, lambda _id: market, caps)

    def assert_no_money_moved(self):
        self.assertNotIn("funds.py", self.scripts())
        self.assertNotIn("trade.py", self.scripts())
        self.assertFalse(self.real.REAL_LEDGER.exists())

    def test_binary_market_places_through_connect_with_its_position_id(self):
        code, _out = self.place()
        self.assertEqual(code, 0)
        # Stake from config, top-up with fee headroom, and a fresh order on the
        # position id: nothing about the order is cached or carried over.
        self.assertEqual(self.calls, [
            ("deposit_wallet.py", "status"),
            ("funds.py", "top-up", "--amount", "1.15"),
            ("trade.py", "buy", "--token-id", IDS["open"], "--usd", "1"),
        ])
        statuses = [r["status"] for r in self.history()]
        self.assertEqual(statuses, ["pending", "placed"])
        self.assertEqual(self.history()[-1]["version"], "v2")
        self.assertEqual(self.history()[-1]["order"]["status"], "matched")

    def test_neg_risk_market_is_refused_before_any_money_moves(self):
        market = GAMMA["neg_risk_open"]
        self.twin(market, market["positionIds"][0], paper_id="neg")
        code, out = self.place(market, "neg")
        self.assertNotEqual(code, 0)
        self.assertIn("read-only", out)
        self.assert_no_money_moved()

    def test_neg_risk_id_is_refused_even_when_gamma_leaves_the_flag_off(self):
        market = dict(GAMMA["neg_risk_open"], negRisk=None)
        self.twin(market, market["positionIds"][0], paper_id="neg")
        code, _out = self.place(market, "neg")
        self.assertNotEqual(code, 0)
        self.assert_no_money_moved()

    def test_combinatorial_market_is_refused_before_any_money_moves(self):
        ids = [str((3 << 248) + i) for i in (0, 1)]
        market = dict(GAMMA["binary_open"], positionIds=ids)
        self.twin(market, ids[0], paper_id="combo")
        code, _out = self.place(market, "combo")
        self.assertNotEqual(code, 0)
        self.assert_no_money_moved()

    def test_unknown_version_is_refused_before_any_money_moves(self):
        for version in ("v3", None):
            with self.subTest(version=version):
                code, _out = self.place(dict(GAMMA["binary_open"], version=version))
                self.assertNotEqual(code, 0)
                self.assert_no_money_moved()

    def test_v1_token_id_is_never_ordered_on_a_v2_market(self):
        # A twin recorded while the market traded on V1 carries a CTF token id.
        self.twin(token="1234567", paper_id="old")
        code, out = self.place(paper_id="old")
        self.assertNotEqual(code, 0)
        self.assertIn("position id", out)
        self.assert_no_money_moved()

    def test_token_of_the_other_outcome_is_refused(self):
        self.twin(token=GAMMA["binary_open"]["positionIds"][1], paper_id="swap")
        code, _out = self.place(paper_id="swap")
        self.assertNotEqual(code, 0)
        self.assert_no_money_moved()

    def test_unreconciled_v1_order_blocks_a_v2_bet_and_is_not_reused(self):
        self.real.append_real({"id": "v1", "market_id": "7", "token_id": "111",
                               "status": "unknown", "usd": 1})
        code, out = self.place()
        self.assertNotEqual(code, 0)
        self.assertIn("unreconciled", out)
        self.assertEqual(self.calls, [])
        self.assertEqual(list(self.rows()), ["v1"])

    def test_wallet_without_v2_approvals_is_refused_before_any_top_up(self):
        code, out = self.place(status="status_pre_v2")
        self.assertNotEqual(code, 0)
        self.assertIn("operator", out)
        self.assertEqual(self.scripts(), ["deposit_wallet.py"])
        self.assertEqual(self.history(), [])

    def test_connect_without_v2_support_is_refused_before_any_top_up(self):
        reply = json.loads(json.dumps(CONNECT["status_v2_ready"]))
        del reply[1]["approvals"]["position_manager_operators"]
        replies = {"deposit_wallet.py": reply}
        code, _out = self.run_cmd(self.real.cmd_place, mock.Mock(paper_id="p1", usd=None),
                                  replies, lambda _id: GAMMA["binary_open"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.scripts(), ["deposit_wallet.py"])
        self.assertEqual(self.history(), [])

    def test_partly_approved_wallet_is_refused(self):
        reply = json.loads(json.dumps(CONNECT["status_v2_ready"]))
        spender = next(iter(reply[1]["approvals"]["pusd_allowances"]))
        reply[1]["approvals"]["pusd_allowances"][spender] = False
        code, _out = self.run_cmd(self.real.cmd_place, mock.Mock(paper_id="p1", usd=None),
                                  {"deposit_wallet.py": reply},
                                  lambda _id: GAMMA["binary_open"])
        self.assertNotEqual(code, 0)
        self.assertEqual(self.scripts(), ["deposit_wallet.py"])

    def test_a_pending_row_blocks_the_next_bet(self):
        # What a crash between the pending row and the buy leaves behind.
        self.real.append_real({"id": "crashed", "market_id": "other", "token_id": "1",
                               "status": "pending", "usd": 1})
        code, out = self.place()
        self.assertNotEqual(code, 0)
        self.assertIn("unreconciled", out)
        self.assertEqual(self.calls, [])

    def test_failed_top_up_stops_before_the_buy(self):
        replies = {"deposit_wallet.py": CONNECT["status_v2_ready"],
                   "funds.py": (1, None, "top-up did not confirm on-chain"),
                   "trade.py": CONNECT["buy_matched"]}
        code, _out = self.run_cmd(self.real.cmd_place, mock.Mock(paper_id="p1", usd=None),
                                  replies, lambda _id: GAMMA["binary_open"])
        self.assertNotEqual(code, 0)
        self.assertNotIn("trade.py", self.scripts())
        self.assertEqual(self.history()[-1]["status"], "failed")

    def test_parallel_place_calls_make_one_buy(self):
        buys, codes = [], []

        def run_script(store, name, *script_args, timeout=180):
            if name == "trade.py":
                buys.append(script_args)
                return tuple(CONNECT["buy_matched"])
            if name == "deposit_wallet.py":
                # Long enough for an unlocked second call to pass every gate too.
                time.sleep(0.2)
                return tuple(CONNECT["status_v2_ready"])
            return tuple(CONNECT["top_up"])

        def place():
            try:
                self.real.cmd_place(mock.Mock(paper_id="p1", usd=None))
                codes.append(0)
            except SystemExit as e:
                codes.append(e.code)

        with mock.patch.object(self.real, "load_protected", return_value=({}, CAPS)), \
             mock.patch.object(self.real, "store_path", return_value=self.tmp), \
             mock.patch.object(self.real, "healthy", return_value=True), \
             mock.patch.object(self.real, "run_script", side_effect=run_script), \
             mock.patch.object(self.real.pmapi, "gamma_market",
                               lambda _id: GAMMA["binary_open"]), \
             contextlib.redirect_stdout(io.StringIO()):
            threads = [threading.Thread(target=place) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual(len(buys), 1)
        self.assertEqual(sorted(codes), [0, 1])

    def test_every_real_cap_still_applies(self):
        token = {"token_id": IDS["open"], "status": "placed", "usd": 1}
        market_id = GAMMA["binary_open"]["id"]
        cases = {
            "stake": ({"usd": 2}, []),
            "one bet per market": ({}, [{"id": "a", "market_id": market_id, **token}]),
            "open positions": ({"caps": dict(CAPS, max_open_positions=1)},
                               [{"id": "b", "market_id": "other", **token}]),
            "daily cap": ({"caps": dict(CAPS, daily_stake_cap_usd=1)},
                          [{"id": "c", "market_id": "other", "ts": self.real.now_iso(),
                            **token}]),
        }
        for name, (kwargs, rows) in cases.items():
            with self.subTest(cap=name):
                self.real.REAL_LEDGER.unlink(missing_ok=True)
                self.calls.clear()
                for row in rows:
                    self.real.append_real(row)
                code, _out = self.place(**kwargs)
                self.assertNotEqual(code, 0)
                self.assertNotIn("funds.py", self.scripts())
                self.assertEqual(len(self.history()), len(rows))

    def assert_unknown_and_blocking(self, code):
        self.assertNotEqual(code, 0)
        self.assertEqual(self.history()[-1]["status"], "unknown")
        self.calls.clear()
        code, out = self.place()
        self.assertNotEqual(code, 0)
        self.assertIn("unreconciled", out)
        self.assertEqual(self.calls, [])

    def test_uncertain_placement_blocks_until_settle_reconciles(self):
        code, _out = self.place(buy="buy_uncertain")
        self.assert_unknown_and_blocking(code)

    def test_buy_timeout_blocks_until_settle_reconciles(self):
        code, _out = self.place(buy=(None, None, "trade.py timed out after 180s"))
        self.assert_unknown_and_blocking(code)

    def test_delayed_order_blocks_until_settle_reconciles(self):
        # Accepted but not matched yet: a delayed FOK can still be killed.
        code, _out = self.place(buy="buy_delayed")
        self.assert_unknown_and_blocking(code)

    def test_auth_failure_that_may_have_submitted_blocks(self):
        reply = (1, {"error": "stream closed", "retry": "not attempted automatically",
                     "warning": "submission outcome may be ambiguous; reconcile before retrying"},
                 "")
        code, _out = self.place(buy=reply)
        self.assert_unknown_and_blocking(code)

    def test_crash_inside_the_buy_blocks(self):
        reply = (1, None, 'File "trade.py", line 249, in op\nKeyError: \'order_id\'')
        code, _out = self.place(buy=reply)
        self.assert_unknown_and_blocking(code)

    def test_killed_order_fails_without_blocking(self):
        code, _out = self.place(buy="buy_killed")
        self.assertNotEqual(code, 0)
        self.assertEqual(self.history()[-1]["status"], "failed")
        self.calls.clear()
        self.assertEqual(self.place()[0], 0)

    def test_failures_that_prove_no_order_stay_failed(self):
        for name in ("buy_no_wallet", "buy_no_market", "buy_no_pusd", "buy_under_minimum",
                     "buy_not_enough_balance", "buy_market_not_ready", "buy_invalid_nonce",
                     "buy_invalid_expiration"):
            with self.subTest(failure=name):
                self.real.REAL_LEDGER.unlink(missing_ok=True)
                code, _out = self.place(buy=name)
                self.assertNotEqual(code, 0)
                self.assertEqual(self.history()[-1]["status"], "failed")

    def test_an_api_error_reply_is_not_proof_that_no_order_was_placed(self):
        # Connect's _post_buy_with_recovery_hint: "only a refusal code or a 401
        # drops its pending marker". Its JSON error reply covers every other API
        # error, which may arrive after the CLOB has the order. A 401 looks the
        # same from here, so it blocks too, which is the safe direction.
        v1 = {"id": GAMMA["binary_open"]["id"], "version": "v1"}
        for market in (GAMMA["binary_open"], v1):
            for name in ("buy_timeout_408", "buy_rate_limited", "buy_region_restricted",
                         "buy_request_rejected", "buy_http_400_quoting_a_refusal",
                         "buy_auth_rejected"):
                with self.subTest(failure=name, version=market["version"]):
                    self.real.REAL_LEDGER.unlink(missing_ok=True)
                    self.calls.clear()
                    code, _out = self.place(market=market, buy=name)
                    self.assertNotEqual(code, 0)
                    self.assertIn("error", CONNECT[name][1])
                    self.assertEqual(self.history()[-1]["status"], "unknown")
                    code, out = self.place(market=market)
                    self.assertNotEqual(code, 0)
                    self.assertIn("unreconciled", out)

    def test_every_other_failure_blocks_until_settle_reconciles(self):
        uncertain = CONNECT["buy_uncertain"][2]
        cases = {
            "recorded: unrecognised reply": CONNECT["buy_unrecognised_reply"],
            "recorded: server error": CONNECT["buy_server_error"],
            "recorded: ambiguous auth failure": CONNECT["buy_auth_ambiguous"],
            "killed by SIGKILL": (-signal.SIGKILL, None, ""),
            "killed by SIGTERM": (-signal.SIGTERM, None, ""),
            "killed after printing a refusal": (-signal.SIGKILL, None, "invalid nonce"),
            "Connect rewords its message": (1, None, "order outcome could not be established"),
            "no message at all": (1, None, ""),
            "unreadable stdout": (1, {"raw": "partial output"}, ""),
            "long error, frames cut from the tail": (1, None, "x" * 2000),
            "crash naming a refusal": (1, None, 'File "trade.py"\nError: invalid nonce'),
            "uncertain, quoting a refusal": (1, None, uncertain + " not enough balance"),
        }
        for name, reply in cases.items():
            with self.subTest(failure=name):
                self.real.REAL_LEDGER.unlink(missing_ok=True)
                self.calls.clear()
                code, _out = self.place(buy=tuple(reply))
                self.assert_unknown_and_blocking(code)

    def test_v1_market_blocks_on_the_same_failures(self):
        v1 = {"id": GAMMA["binary_open"]["id"], "version": "v1"}
        code, _out = self.place(market=v1, buy=(-signal.SIGKILL, None, ""))
        self.assertNotEqual(code, 0)
        row = self.history()[-1]
        self.assertEqual((row["status"], row["version"]), ("unknown", "v1"))
        self.assertNotIn("deposit_wallet.py", self.scripts())
        code, out = self.place(market=v1)
        self.assertNotEqual(code, 0)
        self.assertIn("unreconciled", out)

    def test_unknown_row_is_stamped_after_the_buy_so_settle_waits_for_the_chain(self):
        # The top-up and buy can outlast settle's grace, so the stamp from before
        # them would let settle call the order unfilled too early.
        cases = {"timeout": (None, None, "trade.py timed out"),
                 "unrecognised failure": (1, None, "order outcome could not be established"),
                 "delayed": CONNECT["buy_delayed"]}
        for name, reply in cases.items():
            with self.subTest(case=name):
                self.real.REAL_LEDGER.unlink(missing_ok=True)
                clock = {"now": "2026-11-02T00:00:00Z"}

                def buy(reply=reply, clock=clock):
                    clock["now"] = "2026-11-02T00:07:00Z"
                    return reply

                with mock.patch.object(self.real, "now_iso", lambda clock=clock: clock["now"]):
                    self.place(buy=buy)
                self.assertEqual(self.history()[-1]["status"], "unknown")
                self.assertEqual(self.history()[-1]["ts"], "2026-11-02T00:07:00Z")


class SettleV2(ConnectStub):
    """Sweep, claim, and reconcile V2 positions, with the chain as the authority."""

    WON, LOST = json.loads(GAMMA["binary_closed"]["outcomes"])

    def settle(self, positions, redeem="redeem_nothing", sweep="sweep_empty",
               market=GAMMA["binary_closed"]):
        gamma = market if callable(market) else (lambda _id: market)
        replies = {"funds.py": CONNECT[sweep], "redeem.py": CONNECT[redeem],
                   "positions.py": positions if isinstance(positions, tuple)
                   else CONNECT[positions]}
        return self.run_cmd(self.real.cmd_settle, None, replies, gamma)

    def row(self, token, status="placed", outcome=None, **over):
        row = {"id": "r1", "market_id": GAMMA["binary_closed"]["id"], "token_id": token,
               "status": status, "outcome": outcome, "version": "v2", "usd": 1,
               "ts": "2026-11-02T00:00:00Z", **over}
        self.real.append_real(row)

    def test_sweep_then_on_chain_read_confirms_a_fill_the_indexer_has_not_seen(self):
        self.row(IDS["open"], "unknown")
        code, _out = self.settle("positions_indexer_lag", sweep="sweep_position")
        self.assertEqual(code, 0)
        self.assertEqual(self.rows()["r1"]["status"], "placed")
        self.assertTrue(self.rows()["r1"]["reconciled"])
        self.assertEqual(self.scripts(), ["funds.py", "redeem.py", "positions.py"])
        self.assertIn(("positions.py", "positions", "--token-ids", IDS["open"]), self.calls)

    def test_every_tracked_token_is_checked_on_chain(self):
        self.row(IDS["win"])
        self.row(IDS["open"], "unknown", id="r2")
        self.row("5", "failed", id="r3")
        self.row("6", settled=True, id="r4")
        self.settle("positions_win_unclaimed")
        self.assertIn(("positions.py", "positions", "--token-ids",
                       ",".join(sorted([IDS["win"], IDS["open"]]))), self.calls)

    def test_swept_token_is_a_fill_even_when_a_claim_already_burned_it(self):
        self.row(IDS["open"], "pending")
        code, _out = self.settle("positions_ambiguous_no_fill", sweep="sweep_position")
        self.assertEqual(code, 0)
        self.assertEqual(self.rows()["r1"]["status"], "placed")

    def test_win_is_claimed_through_the_router_then_settled(self):
        self.row(IDS["win"], outcome=self.WON)
        code, _out = self.settle("positions_win_claimed", redeem="redeem_win")
        self.assertEqual(code, 0)
        self.assertTrue(self.rows()["r1"]["settled"])
        settle = self.history()[-1]
        self.assertEqual(settle["type"], "settle")
        claim = settle["redeem"]["redeemed"][0]
        self.assertEqual(claim["adapter"], "0x12121212006e4CD160D18e3f00711DA5c3372600")
        self.assertEqual(claim["status"], 1)

    def test_claimed_win_settles_while_the_indexer_still_lists_it(self):
        self.row(IDS["win"], outcome=self.WON)
        code, _out = self.settle("positions_win_claimed_stale_listing", redeem="redeem_win")
        self.assertEqual(code, 0)
        self.assertTrue(self.rows()["r1"]["settled"])

    def test_win_whose_claim_reverted_stays_open_for_the_next_settle(self):
        self.row(IDS["win"], outcome=self.WON)
        code, _out = self.settle("positions_win_unclaimed", redeem="redeem_win_reverted")
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])
        settle = self.history()[-1]
        self.assertEqual(settle["redeem"]["rc"], 1)

    def test_resolved_winner_the_data_api_does_not_list_is_reported(self):
        self.row(IDS["win"], outcome=self.WON)
        code, out = self.settle("positions_win_unlisted")
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])
        reported = json.loads(out)["unclaimed"]
        self.assertEqual([(r["id"], r["token_id"], r["payout_per_share"]) for r in reported],
                         [("r1", IDS["win"], 1.0)])
        self.assertEqual(self.history()[-1]["unclaimed"], reported)

    def test_win_whose_claim_reverted_is_reported_too(self):
        self.row(IDS["win"], outcome=self.WON)
        _code, out = self.settle("positions_win_unclaimed", redeem="redeem_win_reverted")
        self.assertEqual(json.loads(out)["unclaimed"][0]["token_id"], IDS["win"])

    def test_even_split_with_value_left_is_reported(self):
        market = dict(GAMMA["binary_closed"], outcomePrices=json.dumps(["0.5", "0.5"]))
        self.row(IDS["win"], outcome=self.WON)
        _code, out = self.settle("positions_win_unlisted", market=market)
        self.assertEqual(json.loads(out)["unclaimed"][0]["payout_per_share"], 0.5)

    def test_only_a_held_resolved_position_with_value_is_reported(self):
        def down(_id):
            raise RuntimeError("gamma down")
        cases = {
            "claimed win": (IDS["win"], self.WON, "positions_win_claimed", GAMMA["binary_closed"]),
            "loss": (IDS["loss"], self.LOST, "positions_loss_listed", GAMMA["binary_closed"]),
            "unresolved": (IDS["open"], PlaceV2.OUTCOME, "positions_indexer_lag",
                           GAMMA["binary_open"]),
            "unreadable Gamma": (IDS["win"], self.WON, "positions_win_unlisted", down),
        }
        for name, (token, outcome, positions, market) in cases.items():
            with self.subTest(case=name):
                self.real.REAL_LEDGER.unlink(missing_ok=True)
                self.row(token, outcome=outcome)
                code, out = self.settle(positions, market=market)
                self.assertEqual(code, 0)
                self.assertNotIn("unclaimed", json.loads(out))

    def test_loss_is_not_claimed_and_settles_while_it_stays_in_the_safe(self):
        # The Data API may list the loser as redeemable or leave it out; either
        # way the chain still shows the shares and nothing burns them.
        for positions in ("positions_loss_listed", "positions_loss_unlisted"):
            with self.subTest(positions=positions):
                self.real.REAL_LEDGER.unlink(missing_ok=True)
                self.row(IDS["loss"], outcome=self.LOST)
                code, _out = self.settle(positions, redeem="redeem_loss")
                self.assertEqual(code, 0)
                row = self.rows()["r1"]
                self.assertTrue(row["settled"])
                self.assertIn("no value", row["note"])
                settle = self.history()[-1]
                self.assertEqual(settle["redeem"]["redeemed"], [])
                self.assertEqual(settle["redeem"]["skipped"][0]["reason"], "no_value")

    def test_settled_loss_frees_its_open_position_slot(self):
        self.row(IDS["loss"], outcome=self.LOST, market_id="other")
        self.settle("positions_loss_listed", redeem="redeem_loss")
        with self.real.PAPER_LEDGER.open("a") as f:
            f.write(json.dumps({"id": "p1", "market_id": GAMMA["binary_open"]["id"],
                                "token_id": IDS["open"], "edge_class": "info-race",
                                "outcome": PlaceV2.OUTCOME}) + "\n")
        replies = {"deposit_wallet.py": CONNECT["status_v2_ready"],
                   "funds.py": CONNECT["top_up"], "trade.py": CONNECT["buy_matched"]}
        code, _out = self.run_cmd(self.real.cmd_place, mock.Mock(paper_id="p1", usd=None),
                                  replies, lambda _id: GAMMA["binary_open"],
                                  dict(CAPS, max_open_positions=1))
        self.assertEqual(code, 0)

    def test_position_on_an_unresolved_market_stays_open(self):
        self.row(IDS["open"], outcome=PlaceV2.OUTCOME)
        code, _out = self.settle("positions_indexer_lag", market=GAMMA["binary_open"])
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])

    def test_closed_market_not_yet_resolved_stays_open(self):
        market = dict(GAMMA["binary_closed"], resolutionStatus="active")
        self.row(IDS["loss"], outcome=self.LOST)
        code, _out = self.settle("positions_loss_listed", market=market)
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])

    def test_even_split_is_not_a_loss(self):
        market = dict(GAMMA["binary_closed"], outcomePrices=json.dumps(["0.5", "0.5"]))
        self.row(IDS["loss"], outcome=self.LOST)
        code, _out = self.settle("positions_loss_listed", market=market)
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])

    def test_unreadable_gamma_leaves_the_position_open(self):
        def down(_id):
            raise RuntimeError("gamma down")
        self.row(IDS["loss"], outcome=self.LOST)
        code, _out = self.settle("positions_loss_listed", market=down)
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])

    def test_fresh_ambiguous_order_waits_for_its_fill_to_reach_the_chain(self):
        self.row(IDS["open"], "unknown", ts=self.real.now_iso())
        code, _out = self.settle("positions_ambiguous_no_fill")
        self.assertEqual(code, 0)
        self.assertEqual(self.rows()["r1"]["status"], "unknown")

    def test_fresh_fill_not_on_chain_yet_is_not_settled(self):
        self.row(IDS["open"], ts=self.real.now_iso())
        code, _out = self.settle("positions_ambiguous_no_fill")
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])

    def test_old_ambiguous_order_with_nothing_on_chain_is_failed(self):
        old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=10)
        self.row(IDS["open"], "unknown", ts=old.strftime("%Y-%m-%dT%H:%M:%SZ"))
        code, _out = self.settle("positions_ambiguous_no_fill")
        self.assertEqual(code, 0)
        self.assertEqual(self.rows()["r1"]["status"], "failed")

    def test_failed_on_chain_read_leaves_the_ledger_unchanged(self):
        self.row(IDS["open"], "unknown")
        self.row(IDS["win"], id="r2")
        reply = (0, {"positions": [], "onchain_check": {"error": "could not confirm on-chain"}},
                 "")
        code, _out = self.settle(reply)
        self.assertNotEqual(code, 0)
        self.assertEqual(self.rows()["r1"]["status"], "unknown")
        self.assertNotIn("settled", self.rows()["r2"])
        self.assertIn("reconcile_skipped", self.history()[-1])

    def test_v1_row_never_asks_gamma_about_a_loss(self):
        # A V1 claim burns both sides, so held V1 shares are simply still open.
        def unexpected(_id):
            raise AssertionError("V1 settle reads no Gamma market")
        self.row("111", version="v1", outcome="Yes")
        reply = (0, {"positions": [], "onchain_check": {"checked_token_ids": ["111"],
                                                       "held": [{"token_id": "111"}]}}, "")
        code, _out = self.settle(reply, market=unexpected)
        self.assertEqual(code, 0)
        self.assertNotIn("settled", self.rows()["r1"])


class Doctor(ConnectStub):
    def doctor(self, status):
        replies = {"deposit_wallet.py": CONNECT[status], "funds.py": (0, {"safe": {}}, "")}
        code, out = self.run_cmd(self.real.cmd_doctor, mock.Mock(setup=False), replies, None)
        self.assertEqual(code, 0)
        return json.loads(out)

    def test_v2_ready_needs_the_v2_approvals(self):
        ready = self.doctor("status_v2_ready")
        self.assertTrue(ready["ready"])
        self.assertTrue(ready["v2_ready"])

    def test_wallet_without_v2_approvals_stays_ready_for_v1(self):
        ready = self.doctor("status_pre_v2")
        self.assertTrue(ready["ready"])
        self.assertFalse(ready["v2_ready"])


class SkillEnv(unittest.TestCase):
    """Scripts run in the venv Connect's own bootstrap_env.sh builds, so its SDK
    pin always matches the scripts it provisioned."""

    def setUp(self):
        self.store = pathlib.Path(tempfile.mkdtemp(prefix="phil-store-"))
        self.addCleanup(shutil.rmtree, self.store, ignore_errors=True)
        self.real = load_real()
        self.dir = self.store / self.real.SKILL_SCRIPTS
        self.dir.mkdir(parents=True)
        (self.dir / "probe.py").write_text(
            "import json, os, pathlib, sys\n"
            "print(json.dumps({'args': sys.argv[1:], 'cwd': pathlib.Path.cwd().name,\n"
            "                  'cert': os.environ['SSL_CERT_FILE'],\n"
            "                  'bundle': os.environ['REQUESTS_CA_BUNDLE']}))\n")

    def bootstrap(self, body):
        path = self.dir / "bootstrap_env.sh"
        path.write_text(body)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def test_script_runs_with_the_python_and_trust_store_connect_exports(self):
        self.bootstrap(f"echo 'export PY={sys.executable}'\n"
                       "echo 'export SSL_CERT_FILE=/certs/a.pem'\n"
                       "echo 'export REQUESTS_CA_BUNDLE=/certs/a.pem'\n")
        rc, out, _err = self.real.run_script(self.store, "probe.py", "--x", 1)
        self.assertEqual(rc, 0)
        self.assertEqual(out, {"args": ["--x", "1"], "cwd": self.store.name,
                               "cert": "/certs/a.pem", "bundle": "/certs/a.pem"})

    def test_signal_killed_script_reports_a_negative_exit(self):
        self.bootstrap(f"echo 'export PY={sys.executable}'\n"
                       "echo 'export SSL_CERT_FILE=/certs/a.pem'\n"
                       "echo 'export REQUESTS_CA_BUNDLE=/certs/a.pem'\n")
        (self.dir / "killed.py").write_text(
            "import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n")
        rc, _out, _err = self.real.run_script(self.store, "killed.py")
        self.assertEqual(rc, -signal.SIGKILL)

    def test_failed_bootstrap_stops_before_any_script_runs(self):
        # bootstrap_env.sh reports failure as a failing command for the eval.
        self.bootstrap("echo 'echo needs Python 3.11+ >&2; false'\nexit 1\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            self.real.run_script(self.store, "probe.py")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("needs Python 3.11+", out.getvalue())

    def test_missing_bootstrap_names_the_connect_release(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            self.real.run_script(self.store, "probe.py")
        self.assertIn("bootstrap_env.sh", out.getvalue())


class Settle(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = load_real()
        self.real.REAL_LEDGER = self.tmp / "real-ledger.jsonl"
        self.real.append_real({"id": "r-pending", "token_id": "111",
                               "status": "pending"})
        self.real.append_real({"id": "r-placed", "token_id": "222",
                               "status": "placed"})

    def settle(self, positions_result):
        def run_script(store, name, *args, timeout=180):
            if name == "positions.py":
                return positions_result
            return 0, {"ok": True}, ""
        with mock.patch.object(self.real, "load_protected", return_value=({}, {})), \
             mock.patch.object(self.real, "store_path", return_value=self.tmp), \
             mock.patch.object(self.real, "healthy", return_value=True), \
             mock.patch.object(self.real, "run_script", side_effect=run_script), \
             contextlib.redirect_stdout(io.StringIO()):
            try:
                self.real.cmd_settle(None)
                code = 0
            except SystemExit as e:
                code = e.code
        return code, {r["id"]: r for r in self.real.real_rows()}

    def assert_untouched(self, code, rows):
        self.assertNotEqual(code, 0)
        self.assertEqual(rows["r-pending"]["status"], "pending")
        self.assertNotIn("settled", rows["r-placed"])
        settles = [r for r in rows.values() if r.get("type") == "settle"]
        self.assertEqual(len(settles), 1, "the sweep/redeem result is still logged")
        self.assertIn("reconcile_skipped", settles[0])

    def test_positions_script_fails_closed(self):
        self.assert_untouched(*self.settle((1, None, "data-api 410 Gone")))

    def test_positions_timeout_fails_closed(self):
        self.assert_untouched(*self.settle((None, None, "positions.py timed out")))

    def test_unrecognised_positions_shape_fails_closed(self):
        self.assert_untouched(*self.settle((0, {"raw": "not json"}, "")))

    def test_live_positions_reconcile(self):
        code, rows = self.settle((0, [{"token_id": "111"}], ""))
        self.assertEqual(code, 0)
        self.assertEqual(rows["r-pending"]["status"], "placed")
        self.assertTrue(rows["r-placed"]["settled"])

    def test_empty_positions_list_reconciles(self):
        code, rows = self.settle((0, {"positions": []}, ""))
        self.assertEqual(code, 0)
        self.assertEqual(rows["r-pending"]["status"], "failed")
        self.assertTrue(rows["r-placed"]["settled"])


if __name__ == "__main__":
    unittest.main()
