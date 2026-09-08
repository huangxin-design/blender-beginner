"""Local progress from controlled worker events, with optional native sampling hints.

RenderProgress.feed(line, elapsed), snapshot(elapsed), finish(status, elapsed).
Only render_job.py events establish completed frame outputs. Native logs cannot.
"""
from datetime import datetime, timezone
import json
import math
import re
import time


EVENT_PREFIX = "BLENDER_RENDER_EVENT "
TERMINAL = {"completed", "failed", "timeout", "interrupted"}
FRAME = re.compile(r"\bFra:\s*(-?\d+)\b")
SAMPLE = re.compile(r"\bSample\s+(\d+)\s*/\s*(\d+)\b", re.IGNORECASE)
EEVEE_SAMPLE = re.compile(r"\bRendering\s+(\d+)\s*/\s*(\d+)\s+samples\b", re.IGNORECASE)
REMAINING = re.compile(r"\bRemaining:\s*([\d:.]+)")
LOG_TIME = re.compile(r"^\s*((?:\d+:)?\d+:\d+(?:\.\d+)?)\s+")


def seconds(value):
    try:
        result = 0.0
        for part in value.split(":"):
            result = result * 60 + float(part)
        return result if math.isfinite(result) and result >= 0 else None
    except ValueError:
        return None


class RenderProgress:
    def __init__(self, stale_after=30.0):
        if not math.isfinite(stale_after) or stale_after <= 0:
            raise ValueError("stale_after must be finite and positive")
        self.stale_after = float(stale_after)
        self.status = "starting"
        self.phase = "initializing"
        self.run_id = None
        self.seen_run_ids = set()
        self.frames = None
        self.settings = None
        self.completed = {}
        self.current_frame = None
        self.frame_started_elapsed = None
        self.progress_updated_elapsed = None
        self.sample_updated_elapsed = None
        self.sample = self.samples_total = self.sample_remaining = None
        self.frames_complete = False

    def _touch(self, elapsed):
        self.progress_updated_elapsed = max(self.progress_updated_elapsed or 0, elapsed)
        self.status = "running"

    def _clear_sample(self):
        self.sample = self.samples_total = self.sample_remaining = None
        self.sample_updated_elapsed = None

    def _event(self, data, now):
        if not isinstance(data, dict) or data.get("v") != 1:
            return False
        run_id = data.get("run_id")
        emitted = data.get("emitted_at_unix")
        if not isinstance(run_id, str) or not run_id or not isinstance(emitted, (int, float)):
            return False
        if not math.isfinite(emitted):
            return False
        elapsed = max(0.0, now - max(0.0, time.time() - emitted))
        event = data.get("event")
        if event == "plan":
            frames = data.get("frames")
            if not isinstance(frames, list) or not frames or any(type(f) is not int for f in frames):
                return False
            if len(frames) != len(set(frames)):
                return False
            if run_id in self.seen_run_ids:
                return False  # Replayed plans do not reset already counted output.
            self.run_id, self.frames = run_id, frames
            self.seen_run_ids.add(run_id)
            self.settings = data.get("settings")
            self.completed = {}
            self.current_frame = self.frame_started_elapsed = None
            self.frames_complete = False
            self._clear_sample()
            self.phase = "waiting_for_frame"
        elif run_id != self.run_id or self.frames is None or self.frames_complete:
            return False
        elif event == "frame_started":
            frame = data.get("frame")
            if type(frame) is not int or frame not in self.frames or frame in self.completed:
                return False
            if self.current_frame == frame:
                return False
            self.current_frame, self.frame_started_elapsed = frame, elapsed
            self._clear_sample()
            self.phase = "preparing_frame"
        elif event == "frame_completed":
            frame, duration = data.get("frame"), data.get("duration_seconds")
            if type(frame) is not int or frame != self.current_frame or frame in self.completed:
                return False
            if type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0:
                return False
            if not isinstance(data.get("output"), str) or not data["output"] or type(data.get("bytes")) is not int or data["bytes"] <= 0:
                return False
            self.completed[frame] = float(duration)
            self.current_frame = self.frame_started_elapsed = None
            self._clear_sample()
            self.phase = "waiting_for_frame"
        elif event == "job_frames_complete":
            if len(self.completed) != len(self.frames) or data.get("output_count") != len(self.frames):
                return False
            self.frames_complete = True
            self.phase = "frame_outputs_complete"
        else:
            return False
        self._touch(elapsed)
        return True

    def feed(self, line, now_elapsed):
        if self.status in TERMINAL:
            return False
        if line.startswith(EVENT_PREFIX):
            try:
                return self._event(json.loads(line[len(EVENT_PREFIX):]), now_elapsed)
            except (ValueError, TypeError):
                return False
        # A native frame number helps label sampling, but cannot establish a plan.
        frame_match = FRAME.search(line)
        sample_match = SAMPLE.search(line) or EEVEE_SAMPLE.search(line)
        if not frame_match or not sample_match:
            return False
        frame = int(frame_match.group(1))
        if self.frames is not None and (frame != self.current_frame or frame in self.completed):
            return False
        sample, total = map(int, sample_match.groups())
        if total <= 0 or sample > total:
            return False
        self.sample, self.samples_total = sample, total
        if self.frames is None:
            self.current_frame = frame
        native_time = LOG_TIME.match(line)
        stamp = seconds(native_time.group(1)) if native_time else None
        elapsed = min(now_elapsed, stamp) if stamp is not None else now_elapsed
        remaining = REMAINING.search(line)
        self.sample_remaining = seconds(remaining.group(1)) if remaining else None
        self.sample_updated_elapsed = elapsed
        self.phase = "rendering_or_saving" if sample == total else "sampling"
        if sample == total:
            self.sample_remaining = None
        self._touch(elapsed)
        return True

    def snapshot(self, now_elapsed):
        terminal = self.status in TERMINAL
        stale = self.progress_updated_elapsed is None or now_elapsed - self.progress_updated_elapsed > self.stale_after
        values = list(self.completed.values())
        recent = values[1:][-8:]
        eta, sample_eta = None, None
        if terminal:
            basis = "terminal"
        elif self.frames_complete:
            basis = "frame_outputs_complete"
        elif stale:
            basis = "stale_progress" if self.progress_updated_elapsed is not None else "no_verified_plan"
        elif self.frames is None:
            basis = "no_verified_plan"
        elif len(recent) < 3:
            basis = "collecting_complete_frames"
        else:
            remaining = len(self.frames) - len(self.completed)
            low, high = min(recent), max(recent)
            active = 0.0 if self.frame_started_elapsed is None else max(0.0, now_elapsed - self.frame_started_elapsed)
            if remaining == 0:
                basis = "collecting_complete_frames"  # Wait for the explicit final event.
            elif self.current_frame is not None and active >= high:
                basis = "current_frame_exceeded_observed_range"
            else:
                extra = remaining - (1 if self.current_frame is not None else 0)
                eta = [extra * low, extra * high]
                if self.current_frame is not None:
                    eta[0] += max(0, low - active)
                    eta[1] += max(0, high - active)
                basis = "empirical_recent_frames_low_confidence"
        if not terminal and not stale and not self.frames_complete and self.sample_remaining is not None and self.sample_updated_elapsed is not None:
            sample_eta = self.sample_remaining - max(0, now_elapsed - self.sample_updated_elapsed)
            if sample_eta <= 0:
                sample_eta = None
        messages = {
            "terminal": "执行已结束；进程状态、帧输出存在性和画面验收分别记录。",
            "frame_outputs_complete": "计划帧已输出，正在等待进程结束；画面尚未验收。",
            "stale_progress": "暂未收到新进度，剩余时间未知；日志静默不代表卡死。",
            "no_verified_plan": "正在准备或尚无可核验帧计划；不推算整段剩余时间。",
            "collecting_complete_frames": "正在收集完整帧耗时；首帧单列，至少需要三个后续帧。",
            "current_frame_exceeded_observed_range": "本帧已超出此前经验范围，正在重新估计。",
            "empirical_recent_frames_low_confidence": "基于最近同计划完整帧的低可信经验范围，可能上升；不含编码与验收。",
        }
        return {
            "status": self.status, "phase": self.phase, "run_id": self.run_id,
            "elapsed_seconds": round(max(0, now_elapsed), 3),
            "sample_eta_seconds": round(sample_eta, 3) if sample_eta is not None else None,
            "eta_range_seconds": [round(value, 3) for value in eta] if eta is not None else None,
            "eta_basis": basis, "completed_frames": len(self.completed) if self.frames is not None else None,
            "total_frames": len(self.frames) if self.frames is not None else None,
            "current_frame": self.current_frame, "sample": self.sample, "samples_total": self.samples_total,
            "progress_updated_elapsed": self.progress_updated_elapsed,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "frames_complete": self.frames_complete, "scope": "frame_outputs_only",
            "first_frame_seconds": values[0] if values else None, "recent_frame_seconds": recent,
            "output_verification": "presence_only" if self.frames_complete else "unverified",
            "visual_verification": "unverified", "message": messages[basis],
        }

    def finish(self, status, now_elapsed):
        if status not in TERMINAL:
            raise ValueError("finish status must be completed, failed, timeout or interrupted")
        self.status = status
        self.phase = "process_completed" if status == "completed" else status
        self.sample_remaining = None
        return self.snapshot(now_elapsed)
