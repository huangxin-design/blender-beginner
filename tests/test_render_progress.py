"""Portable progress counterexamples; run with Python 3.10+ unittest.

Uses only the standard library. No Blender installation, model calls, network,
private logs or artwork files are accessed. Times and output names in events
are synthetic; the small native log excerpts below contain no machine paths.
"""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/blender-beginner/scripts"))
from render_progress import EVENT_PREFIX, RenderProgress

BASE = 1800000000


def feed(progress, event, now, run_id="one", **fields):
    data = {"v": 1, "run_id": run_id, "emitted_at_unix": BASE + now, "event": event, **fields}
    with patch("render_progress.time.time", return_value=BASE + now):
        return progress.feed(EVENT_PREFIX + json.dumps(data), now)


def complete(progress, frame, start, duration, run_id="one"):
    feed(progress, "frame_started", start, run_id, frame=frame)
    feed(progress, "frame_completed", start + duration, run_id, frame=frame,
         duration_seconds=duration, output=f"frame_{frame}.png", bytes=64)
    return start + duration


class ProgressTests(unittest.TestCase):
    def test_native_replay_cannot_complete_a_job(self):
        # Path-free excerpts of observed Blender 5.2.1 64x64 test logs.
        logs = (
            (
                "00:00.422 render | Fra: 1 | Remaining: 00:00.00 | Mem: 1M | Sample 1/8",
                "00:00.437 render | Fra: 1 | Mem: 1M | Sample 8/8",
                "00:00.437 render | Fra: 1 | Mem: 1M | Finished",
                "00:00.547 render | Fra: 2 | Mem: 1M | Sample 0/8",
                "00:00.547 render | Fra: 2 | Remaining: 00:00.00 | Mem: 1M | Sample 1/8",
                "00:00.547 render | Fra: 2 | Mem: 1M | Sample 8/8",
            ),
            (
                "00:11.562 render | Fra: 1 | Rendering 1 / 64 samples",
                "00:11.765 render | Fra: 1 | Rendering 25 / 64 samples",
                "00:11.890 render | Fra: 1 | Rendering 64 / 64 samples",
                "00:12.062 render | Fra: 2 | Rendering 1 / 64 samples",
                "00:12.125 render | Fra: 2 | Rendering 64 / 64 samples",
            ),
        )
        for lines in logs:
            progress = RenderProgress()
            for line in lines:
                progress.feed(line, 13)
                self.assertFalse(progress.snapshot(13)["frames_complete"])
            self.assertIsNotNone(progress.snapshot(13)["sample"])
            result = progress.finish("completed", 14)
            self.assertIsNone(result["completed_frames"])
            self.assertIsNone(result["eta_range_seconds"])
            self.assertEqual(result["visual_verification"], "unverified")

    def test_zero_remaining_and_full_sample_are_not_completion(self):
        progress = RenderProgress()
        feed(progress, "plan", 0, frames=[1])
        feed(progress, "frame_started", .1, frame=1)
        progress.feed("00:00.422 render | Fra: 1 | Remaining: 00:00.00 | Sample 1/8", .5)
        self.assertIsNone(progress.snapshot(.5)["sample_eta_seconds"])
        progress.feed("00:00.437 render | Fra: 1 | Sample 8/8", .5)
        progress.feed("00:00.437 render | Fra: 1 | Finished", .5)
        progress.feed("00:00.547 render | Saved: 'x.png'", .6)
        self.assertEqual(progress.snapshot(.6)["completed_frames"], 0)
        self.assertFalse(progress.snapshot(.6)["frames_complete"])

    def test_noncontinuous_plan_and_duplicate_events(self):
        progress = RenderProgress()
        feed(progress, "plan", 0, frames=[1, 11, 21])
        now = 0
        for frame in (1, 11, 21):
            now = complete(progress, frame, now, 1)
            for _ in range(3):
                progress.feed("Saved: 'extra.png'", now)
                feed(progress, "frame_completed", now, frame=frame, duration_seconds=1, output="x", bytes=64)
        self.assertEqual(progress.snapshot(now)["completed_frames"], 3)
        self.assertFalse(progress.snapshot(now)["frames_complete"])
        feed(progress, "job_frames_complete", now, output_count=3)
        self.assertTrue(progress.snapshot(now)["frames_complete"])
        self.assertEqual(progress.snapshot(now)["status"], "running")
        self.assertEqual(progress.finish("failed", now)["status"], "failed")

    def test_first_frame_excluded_and_later_slow_frame_preserved(self):
        progress = RenderProgress()
        feed(progress, "plan", 0, frames=list(range(1, 7)))
        now = complete(progress, 1, 0, 11.59)
        now = complete(progress, 2, now, .1)
        self.assertIsNone(progress.snapshot(now)["eta_range_seconds"])
        now = complete(progress, 3, now, .1)
        self.assertIsNone(progress.snapshot(now)["eta_range_seconds"])
        now = complete(progress, 4, now, .1)
        self.assertEqual(progress.snapshot(now)["eta_range_seconds"], [.2, .2])
        feed(progress, "frame_started", now, frame=5)
        self.assertEqual(progress.snapshot(now + 1)["eta_basis"], "current_frame_exceeded_observed_range")
        self.assertIsNone(progress.snapshot(now + 1)["eta_range_seconds"])
        feed(progress, "frame_completed", now + 8, frame=5, duration_seconds=8, output="slow.png", bytes=64)
        result = progress.snapshot(now + 8)
        self.assertEqual(result["first_frame_seconds"], 11.59)
        self.assertEqual(result["recent_frame_seconds"], [.1, .1, .1, 8])
        self.assertEqual(result["eta_range_seconds"], [.1, 8])

    def test_new_plan_resets_history_and_old_replay_cannot_reset_new_plan(self):
        progress = RenderProgress()
        feed(progress, "plan", 0, frames=[1])
        complete(progress, 1, 0, 1)
        feed(progress, "job_frames_complete", 1, output_count=1)
        feed(progress, "plan", 2, "two", frames=[1, 3])
        self.assertEqual(progress.snapshot(2)["completed_frames"], 0)
        feed(progress, "plan", 3, frames=[1])
        self.assertEqual(progress.snapshot(3)["run_id"], "two")
        self.assertIsNone(progress.snapshot(3)["first_frame_seconds"])

    def test_unknown_malformed_incomplete_and_unplanned_events(self):
        progress = RenderProgress()
        self.assertFalse(progress.feed("Unknown Blender 9 format 99 percent", 1))
        self.assertFalse(progress.feed(EVENT_PREFIX + '{"v":', 2))
        feed(progress, "plan", 3, frames=[101, 102])
        feed(progress, "frame_started", 4, frame=999)
        feed(progress, "frame_completed", 5, frame=101, duration_seconds=1, output="x", bytes=64)
        feed(progress, "job_frames_complete", 6, output_count=2)
        self.assertEqual(progress.snapshot(6)["completed_frames"], 0)
        self.assertFalse(progress.snapshot(6)["frames_complete"])

    def test_stale_progress_and_batched_event_ages(self):
        progress = RenderProgress()
        feed(progress, "plan", 0, frames=[1, 2, 3, 4, 5])
        for frame in range(1, 5):
            complete(progress, frame, frame - 1, 1)
        self.assertEqual(progress.snapshot(4)["eta_range_seconds"], [1, 1])
        self.assertIsNone(progress.snapshot(35)["eta_range_seconds"])
        self.assertEqual(progress.snapshot(35)["eta_basis"], "stale_progress")
        data = {"v": 1, "run_id": "one", "event": "frame_started", "frame": 5, "emitted_at_unix": BASE + 5}
        with patch("render_progress.time.time", return_value=BASE + 50):
            progress.feed(EVENT_PREFIX + json.dumps(data), 50)
        self.assertEqual(progress.snapshot(50)["progress_updated_elapsed"], 5)
        self.assertIsNone(progress.snapshot(50)["eta_range_seconds"])

    def test_interruption_timeout_and_missing_plan_output_remain_distinct(self):
        for status in ("interrupted", "timeout", "failed", "completed"):
            progress = RenderProgress()
            feed(progress, "plan", 0, frames=[1, 2])
            complete(progress, 1, 0, 1)
            result = progress.finish(status, 2)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["completed_frames"], 1)
            self.assertFalse(result["frames_complete"])
            self.assertIsNone(result["eta_range_seconds"])
            self.assertIsNone(result["sample_eta_seconds"])
            self.assertFalse(progress.feed("Fra: 2 | Sample 1/8", 3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
