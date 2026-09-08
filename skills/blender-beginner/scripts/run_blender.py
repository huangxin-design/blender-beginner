"""Run a reviewed Blender script with an explicit time budget and fresh logs.

This controls only the launched process, not arbitrary script access or child processes.
A zero exit code is process success; inspect artifacts and appearance separately.
"""
import argparse
import codecs
import json
import math
import os
from pathlib import Path
import subprocess
import time


def write_progress(tracker, directory, elapsed, usage_path=None):
    from status_display import write_display
    status = tracker.snapshot(elapsed)
    usage = None
    if usage_path:
        try:
            usage = json.loads(usage_path.read_text(encoding="utf-8-sig"))
            if not isinstance(usage, dict):
                usage = None
        except (OSError, ValueError):
            pass  # Missing usage must not interrupt Blender or become a zero count.
    temporary = directory / "progress.json.tmp"
    temporary.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, directory / "progress.json")
    write_display(status, directory / "progress.html", usage)


def run_monitored(command, log, directory, env, timeout, started, tracker, usage_path, progress_errors=None):
    """Tail a regular file so quiet or partial lines cannot block the time limit."""
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    pending = ""
    last_write = -1.0
    progress_available = True
    try:
        with (directory / "blender.log").open("rb") as reader:
            while True:
                elapsed = time.perf_counter() - started
                if elapsed >= timeout and process.poll() is None:
                    raise subprocess.TimeoutExpired(command, timeout)
                chunk = reader.read(262144)
                pending += decoder.decode(chunk).replace("\r", "\n")
                lines = pending.split("\n")
                pending = lines.pop()
                for line in lines:
                    tracker.feed(line, elapsed)
                # Bound a malformed script's unterminated line in memory; the log is intact.
                if len(pending) > 1048576:
                    pending = pending[-1048576:]
                if progress_available and elapsed - last_write >= 1.0:
                    try:
                        write_progress(tracker, directory, elapsed, usage_path)
                    except (OSError, ValueError) as error:
                        progress_available = False
                        if progress_errors is not None:
                            progress_errors.append(str(error))
                    last_write = elapsed
                if process.poll() is not None and not chunk:
                    pending += decoder.decode(b"", final=True)
                    if pending:
                        tracker.feed(pending, elapsed)
                    return process.returncode
                if not chunk:
                    time.sleep(0.1)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--blend", type=Path)
    parser.add_argument("--log-dir", required=True, type=Path)
    parser.add_argument("--timeout", required=True, type=float, help="Positive wall-clock seconds, including startup.")
    parser.add_argument("--progress", action="store_true", help="Write local progress.json and an automatically refreshed progress.html.")
    parser.add_argument("--usage-report", type=Path, help="Optional local token report to display with --progress.")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Script arguments after --.")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number of seconds.")
    if args.usage_report and not args.progress:
        parser.error("--usage-report requires --progress.")
    try:
        executable = args.blender.expanduser().resolve(strict=True)
        script = args.script.expanduser().resolve(strict=True)
        source = args.blend.expanduser().resolve(strict=True) if args.blend else None
    except OSError as error:
        parser.error(str(error))
    if not executable.is_file() or not script.is_file() or script.suffix.lower() != ".py":
        parser.error("Provide an existing Blender executable and reviewed .py script.")
    if source and (not source.is_file() or source.suffix.lower() != ".blend"):
        parser.error("--blend must point to an existing .blend file.")
    directory = args.log_dir.expanduser()
    if not directory.is_absolute() or directory.exists() or directory.is_symlink():
        parser.error("--log-dir must be an absolute, previously nonexistent directory.")
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    temp = directory / "temp"
    temp.mkdir()
    env = os.environ.copy()
    env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    command = [str(executable), "--background", "--factory-startup", "--disable-autoexec"]
    tracker = None
    if args.progress:
        from render_progress import RenderProgress
        tracker = RenderProgress()
        command.extend(["--log", "render", "--log-level", "info"])
    if source:
        command.append(str(source))
    script_args = args.script_args[1:] if args.script_args[:1] == ["--"] else args.script_args
    command.extend(["--python-exit-code", "1", "--python", str(script), "--", *script_args])
    result = {"status": "not_started", "scope": "process_execution_only",
              "source": str(source) if source else None,
              "script": str(script), "script_args": script_args, "timeout_seconds": args.timeout,
              "exit_code": None, "log": str(directory / "blender.log"),
              "limitation": "Process success does not verify artifacts, visual quality or file portability. This is not a sandbox for untrusted scripts or .blend files."}
    started = time.perf_counter()
    progress_errors = []
    if tracker:
        result.update(progress=str(directory / "progress.json"), display=str(directory / "progress.html"))
    try:
        with (directory / "blender.log").open("x", encoding="utf-8") as log:
            if tracker:
                returncode = run_monitored(command, log, directory, env, args.timeout,
                                           started, tracker, args.usage_report, progress_errors)
            else:
                process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=args.timeout, env=env,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                returncode = process.returncode
        result.update(exit_code=returncode, status="completed" if returncode == 0 else "failed")
    except subprocess.TimeoutExpired:
        result.update(status="timeout", error="The launched Blender process was killed at the time limit; inspect partial artifacts before resuming.")
    except KeyboardInterrupt:
        result.update(status="interrupted", error="The caller interrupted this run; inspect partial artifacts before resuming.")
    except (OSError, ValueError) as error:
        result.update(status="failed", error=f"{type(error).__name__}: {error}")
    result["process_seconds"] = round(time.perf_counter() - started, 3)
    if tracker:
        tracker.finish(result["status"], result["process_seconds"])
        try:
            write_progress(tracker, directory, result["process_seconds"], args.usage_report)
        except (OSError, ValueError) as error:
            progress_errors.append(str(error))
        if progress_errors:
            result["progress_error"] = "; ".join(dict.fromkeys(progress_errors))
    with (directory / "run.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
