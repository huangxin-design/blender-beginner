"""Behavioral regression tests using synthetic, content-free usage logs."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/blender-beginner/scripts/token_usage.py"
spec = importlib.util.spec_from_file_location("token_usage", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def amount(i, o, cache=None, reason=None):
    return {"input_tokens": i, "output_tokens": o, "total_tokens": i + o,
            "cached_input_tokens": cache, "reasoning_output_tokens": reason}


def event(subtype, **values):
    return {"type": "event_msg", "timestamp": "2026-09-08T01:00:00Z",
            "payload": {"type": subtype, **values}}


def count(i, o, cache=None, reason=None):
    return event("token_count", info={"total_token_usage": amount(i, o, cache, reason)})


class TokensTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source.jsonl"
        self.ledger = self.root / "ledger.json"

    def tearDown(self):
        self.temporary.cleanup()

    def append(self, *events):
        with self.source.open("ab") as stream:
            for item in events:
                stream.write(json.dumps(item).encode() + b"\n")

    def rollout(self):
        self.append({"type": "session_meta", "payload": {"id": "s1"}},
                    event("task_started", turn_id="t1"), count(100, 10, 50, 2))
        return mod.begin("lamp", self.source)

    def exec_log(self):
        self.append({"type": "thread.started", "thread_id": "s1"})
        return mod.begin("lamp", self.source)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_rollout_is_delta_and_refresh_is_idempotent(self):
        state = self.rollout()
        self.append(count(150, 20, 75, 4), count(150, 20, 75, 4))
        mod.scan(state)
        self.assertEqual(state["usage"], amount(50, 10, 25, 2))
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 60)

    def test_equal_exec_turns_are_both_counted(self):
        state = self.exec_log()
        self.append({"type": "turn.completed", "usage": amount(50, 10)},
                    {"type": "turn.completed", "usage": amount(50, 10)})
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 120)
        self.assertEqual(state["usage_events"], 2)
        self.assertIsNone(state["observed_through"])
        self.assertIsNone(state["usage"]["cached_input_tokens"])

    def test_end_waits_for_final_usage_then_stops(self):
        state = self.rollout()
        self.append(count(130, 15, 60, 3))
        mod.scan(state)
        mod.close(state)
        self.assertEqual(state["status"], "close_requested_pending")
        self.append(count(160, 25, 70, 5), event("task_complete", turn_id="t1"),
                    event("task_started", turn_id="t2"), count(900, 90, 800, 40))
        mod.scan(state)
        self.assertEqual(state["status"], "closed_observed")
        self.assertEqual(state["usage"]["total_tokens"], 75)
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 75)

    def test_lost_end_boundary_excludes_next_turn(self):
        state = self.rollout()
        mod.close(state)
        self.append(event("task_started", turn_id="t2"), count(900, 90, 800, 40))
        mod.scan(state)
        self.assertEqual(state["status"], "closed_partial")
        self.assertEqual(state["usage"]["total_tokens"], 0)

    def test_abort_is_partial_and_unknown_not_zero_cost(self):
        state = self.rollout()
        mod.close(state)
        self.append(event("task_aborted", turn_id="t1"))
        mod.scan(state)
        summary = mod.report(state)
        self.assertEqual(summary["status"], "closed_partial")
        self.assertEqual(summary["coverage"]["missing_usage_events"], 1)
        self.assertIn("unknown, not zero", " ".join(summary["notes"]))

    def test_unknown_lifecycle_freezes_at_end(self):
        state = self.exec_log()
        mod.close(state)
        self.append({"type": "turn.completed", "usage": amount(100, 20)})
        mod.scan(state)
        self.assertEqual(state["status"], "closed_partial")
        self.assertEqual(state["usage"]["total_tokens"], 0)

    def test_rollout_abort_already_read_before_end_is_partial(self):
        state = self.rollout()
        self.append(count(150, 20, 75, 4), event("task_aborted", turn_id="t1"))
        mod.scan(state)
        self.assertIsNone(state["active_turn"])
        mod.close(state)
        self.assertEqual(state["status"], "closed_partial")
        self.assertEqual(state["usage"]["total_tokens"], 60)

    def test_exec_failure_already_read_before_end_is_partial(self):
        state = self.exec_log()
        self.append({"type": "turn.completed", "usage": amount(50, 10)},
                    {"type": "turn.started"}, {"type": "turn.failed"})
        mod.scan(state)
        self.assertIsNone(state["active_turn"])
        mod.close(state)
        self.assertEqual(state["status"], "closed_partial")
        self.assertEqual(state["usage"]["total_tokens"], 60)

    def test_missing_info_is_partial_even_with_later_complete_boundary(self):
        state = self.rollout()
        self.append(event("token_count", info=None))
        mod.scan(state)
        mod.close(state)
        self.append(count(150, 20, 75, 4), event("task_complete", turn_id="t1"))
        mod.scan(state)
        self.assertEqual(state["status"], "closed_partial")
        self.assertEqual(state["usage"]["total_tokens"], 60)

    def test_incomplete_tail_is_retained_then_read_once(self):
        state = self.rollout()
        tail = json.dumps(count(150, 20, 75, 4)).encode()
        with self.source.open("ab") as stream:
            stream.write(tail[:30])
        mod.scan(state)
        self.assertTrue(state["incomplete_tail"])
        self.assertEqual(state["usage"]["total_tokens"], 0)
        with self.source.open("ab") as stream:
            stream.write(tail[30:] + b"\n")
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 60)

    def test_regression_rejects_without_changing_disk_ledger(self):
        state = self.rollout()
        mod.atomic_write(self.ledger, state)
        original = self.ledger.read_bytes()
        self.append(count(50, 5, 20, 1))
        result = self.cli("update", "--ledger", str(self.ledger))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.ledger.read_bytes(), original)

    def test_malformed_middle_rejects_without_committing_partial_counts(self):
        state = self.rollout()
        mod.atomic_write(self.ledger, state)
        original = self.ledger.read_bytes()
        self.append(count(150, 20, 75, 4))
        with self.source.open("ab") as stream:
            stream.write(b"not-json\n")
        self.append(count(200, 30, 90, 5))
        self.assertNotEqual(self.cli("update", "--ledger", str(self.ledger)).returncode, 0)
        self.assertEqual(self.ledger.read_bytes(), original)

    def test_prefix_replacement_and_truncation_rejected(self):
        state = self.rollout()
        original = self.source.read_bytes()
        self.source.write_bytes(original.replace(b"s1", b"s2"))
        with self.assertRaises(ValueError):
            mod.scan(copy.deepcopy(state))
        self.source.write_bytes(original[:-1])
        with self.assertRaises(ValueError):
            mod.scan(copy.deepcopy(state))

    def test_changed_identity_rejected(self):
        state = self.rollout()
        self.append({"type": "session_meta", "payload": {"id": "different"}})
        with self.assertRaises(ValueError):
            mod.scan(state)

    def test_baseline_excludes_old_fork_or_reset_history(self):
        self.append({"type": "session_meta", "payload": {"id": "fork", "forked_from_id": "parent"}},
                    count(50000, 500), count(100, 10), event("task_started", turn_id="t1"))
        state = mod.begin("lamp", self.source)
        self.append(count(150, 20))
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 60)
        self.assertEqual(mod.report(state)["coverage"]["subagents"], "not_included")

    def test_unknown_subsets_remain_null_not_added_twice(self):
        state = self.exec_log()
        self.append({"type": "turn.completed", "usage": amount(8000, 2000, 6000, 1500)})
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 10000)
        self.append({"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 10}})
        mod.scan(state)
        self.assertEqual(state["usage"]["total_tokens"], 10110)
        self.assertIsNone(state["usage"]["cached_input_tokens"])
        self.assertIsNone(state["usage"]["reasoning_output_tokens"])

    def test_bad_usage_schema_and_totals_are_rejected(self):
        for value in ({"output_tokens": 1}, amount(1, 2, 9),
                      {"input_tokens": 1, "output_tokens": 2, "total_tokens": 10}):
            with self.assertRaises(ValueError):
                mod.usage(value)

    def test_no_rollout_baseline_is_not_assumed_zero(self):
        self.append({"type": "session_meta", "payload": {"id": "s1"}})
        with self.assertRaises(ValueError):
            mod.begin("lamp", self.source)

    def test_report_contains_no_source_path_or_chat(self):
        state = self.rollout()
        self.append({"type": "response_item", "payload": {"text": "PRIVATE-CHAT-SENTINEL"}},
                    count(150, 20, 75, 4))
        mod.scan(state)
        rendered = json.dumps(mod.report(state))
        self.assertNotIn(str(self.source), rendered)
        self.assertNotIn("PRIVATE-CHAT-SENTINEL", json.dumps(state))
        self.assertEqual(mod.report(state)["coverage"]["project_attribution"], "not_proven")

    def test_existing_ledger_report_and_lock_are_preserved(self):
        state = self.rollout()
        mod.atomic_write(self.ledger, state)
        before = self.ledger.read_bytes()
        result = self.cli("begin", "--ledger", str(self.ledger), "--project-id", "other", "--source", str(self.source))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.ledger.read_bytes(), before)
        output = self.root / "report.json"
        output.write_text("KEEP")
        self.assertNotEqual(self.cli("report", "--ledger", str(self.ledger), "--output", str(output)).returncode, 0)
        self.assertEqual(output.read_text(), "KEEP")
        lock = self.root / "ledger.json.lock"
        lock.write_text("busy")
        self.assertNotEqual(self.cli("update", "--ledger", str(self.ledger)).returncode, 0)
        self.assertEqual(lock.read_text(), "busy")


if __name__ == "__main__":
    unittest.main(verbosity=2)
