"""Record observed project token usage from one explicitly supplied Codex JSONL.

No API calls, transcript export, account quota conversion or cross-source merging.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile


FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
          "reasoning_output_tokens", "total_tokens")
CLOSED = {"closed_observed", "closed_partial"}


def now():
    return datetime.now(timezone.utc).isoformat()


def usage(value):
    if not isinstance(value, dict):
        raise ValueError("Missing usage object; refusing to assume zero.")
    result = {key: value.get(key) for key in FIELDS}
    for key, count in result.items():
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError(f"Invalid usage field: {key}.")
    if any(result[key] is None for key in ("input_tokens", "output_tokens")):
        raise ValueError("Input/output token fields are required.")
    total = result["input_tokens"] + result["output_tokens"]
    if result["total_tokens"] is not None and result["total_tokens"] != total:
        raise ValueError("Source total differs from input + output.")
    result["total_tokens"] = total
    for subset, parent in (("cached_input_tokens", "input_tokens"),
                           ("reasoning_output_tokens", "output_tokens")):
        if result[subset] is not None and result[subset] > result[parent]:
            raise ValueError(f"{subset} exceeds its parent count.")
    return result


def add(left, right):
    return {key: None if left[key] is None or right[key] is None
            else left[key] + right[key] for key in FIELDS}


def difference(current, previous):
    delta = {key: None if current[key] is None or previous[key] is None
             else current[key] - previous[key] for key in FIELDS}
    if any(count is not None and count < 0 for count in delta.values()):
        raise ValueError("Cumulative usage regressed; ledger was not changed.")
    return usage(delta)


def session(state, identifier):
    if not isinstance(identifier, str) or not identifier:
        raise ValueError("Missing source session identifier.")
    if state["session_id"] and state["session_id"] != identifier:
        raise ValueError("Source contains a different session; merging is unsupported.")
    state["session_id"] = identifier


def process(state, event, offset, baseline=False):
    kind = event.get("type")
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}
    if kind in ("session_meta", "thread.started"):
        detected = "rollout" if kind == "session_meta" else "exec"
        if state["source_format"] and state["source_format"] != detected:
            raise ValueError("Mixed source formats are unsupported.")
        state["source_format"] = detected
        session(state, payload.get("id", payload.get("session_id"))
                if detected == "rollout" else event.get("thread_id"))
    subtype = payload.get("type") if kind == "event_msg" else kind
    if subtype in ("task_started", "turn.started"):
        turn_id = payload.get("turn_id") if subtype == "task_started" else f"exec:{offset}"
        if not turn_id:
            raise ValueError("Turn start is missing its identifier.")
        if state.get("close_turn") and turn_id != state["close_turn"]:
            state["status"] = "closed_partial"
            state["boundary_note"] = "A new turn started before the requested closing boundary. Later events were excluded."
            return False
        state["active_turn"] = turn_id
        state["has_lifecycle"] = True
    count = None
    if subtype == "token_count":
        if state["source_format"] != "rollout":
            raise ValueError("Token count event has no supported rollout identity.")
        info = payload.get("info")
        if info is None:
            state["missing_usage_events"] += 1
        elif not isinstance(info, dict):
            raise ValueError("Unrecognized token-count schema.")
        else:
            count = usage(info.get("total_token_usage"))
    elif subtype == "turn.completed":
        if state["source_format"] != "exec":
            raise ValueError("Turn usage has no supported exec identity.")
        count = usage(event.get("usage"))
    if count is not None:
        if state["source_format"] == "rollout":
            if not baseline:
                increment = difference(count, state["latest_usage"])
                state["usage"] = add(state["usage"], increment)
            state["latest_usage"] = count
        elif not baseline:
            state["usage"] = add(state["usage"], count)
        state["observed_through"] = event.get("timestamp")
        state["usage_events"] += 1
    if subtype in ("task_complete", "task_aborted", "turn.completed", "turn.failed"):
        turn_id = payload.get("turn_id") if subtype.startswith("task_") else state["active_turn"]
        aborted = subtype in ("task_aborted", "turn.failed")
        if aborted:
            state["missing_usage_events"] += 1
        if state.get("close_turn") and turn_id == state["close_turn"]:
            state["status"] = "closed_partial" if state["missing_usage_events"] else "closed_observed"
            state["boundary_note"] = "The requested turn boundary was observed; this is not proof of complete project attribution."
        if turn_id and turn_id == state["active_turn"]:
            state["active_turn"] = None
    return True


def scan(state, baseline=False):
    """Read a snapshot; persist only counters, lifecycle IDs and prefix metadata."""
    source = Path(state["source_path"])
    data = source.read_bytes()
    cursor = state["cursor"]["bytes"]
    if len(data) < cursor or hashlib.sha256(data[:cursor]).hexdigest() != state["cursor"]["sha256"]:
        raise ValueError("Source was truncated or its recorded prefix changed; ledger was not changed.")
    if state["status"] in CLOSED:
        return state
    end = data.rfind(b"\n") + 1
    position = cursor
    for raw in data[cursor:end].splitlines(keepends=True):
        next_position = position + len(raw)
        if raw.strip():
            try:
                event = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValueError(f"Malformed complete JSONL record at byte {position}; ledger was not changed.") from None
            if not isinstance(event, dict):
                raise ValueError("JSONL records must be objects.")
            if not process(state, event, position, baseline):
                break
        position = next_position
        if state["status"] in CLOSED:
            break
    state["cursor"] = {"bytes": position, "sha256": hashlib.sha256(data[:position]).hexdigest()}
    state["incomplete_tail"] = end < len(data) and state["status"] not in CLOSED
    state["read_at"] = now()
    return state


def begin(project_id, source):
    state = {
        "schema_version": 1, "project_id": project_id,
        "source_path": str(source.resolve(strict=True)), "source_format": None,
        "session_id": None, "status": "observed_pending", "started_at": now(),
        "cursor": {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()},
        "latest_usage": None, "usage": dict.fromkeys(FIELDS, 0),
        "observed_through": None, "usage_events": 0, "missing_usage_events": 0,
        "active_turn": None, "has_lifecycle": False, "close_turn": None,
    }
    scan(state, baseline=True)
    if not state["source_format"] or not state["session_id"]:
        raise ValueError("No supported source identity found; supply an explicit rollout or codex exec JSONL.")
    if state["source_format"] == "rollout" and state["latest_usage"] is None:
        raise ValueError("No cumulative baseline is available yet; retry after a usage event is recorded.")
    state["baseline_usage"] = copy.deepcopy(state["latest_usage"])
    state["baseline_cursor"] = copy.deepcopy(state["cursor"])
    state["baseline_observed_through"] = state["observed_through"]
    if state["source_format"] == "rollout":
        state["usage"] = {key: 0 if value is not None else None
                          for key, value in state["latest_usage"].items()}
    state["usage_events"] = 0
    state["missing_usage_events"] = 0
    return state


def close(state):
    if state["status"] in CLOSED:
        return
    state["close_requested_at"] = now()
    if state["active_turn"]:
        state["status"] = "close_requested_pending"
        state["close_turn"] = state["active_turn"]
    else:
        state["status"] = "closed_observed" if state["has_lifecycle"] and not state["missing_usage_events"] else "closed_partial"
        state["boundary_note"] = "Stopped at the current recorded position; no later events will be imported."


def report(state):
    notes = [
        "Observed source interval only; an in-flight request can cross the begin boundary.",
        "A mixed-project turn cannot be split accurately. Use a dedicated source and one ledger per source interval.",
        "Subagents, fork inheritance, other sources and historical .blend-only work are not covered or merged.",
        "Cached input is included in input; reasoning output is included in output. Unknown details are null.",
        "Local rendering consumes no model tokens by itself. No fees or account quotas are inferred.",
    ]
    if state["status"] not in CLOSED:
        notes.append("Current/future final usage can be delayed; this report is pending, not a settled project total.")
    if state.get("boundary_note"):
        notes.append(state["boundary_note"])
    if state.get("incomplete_tail"):
        notes.append("An incomplete trailing record was left unread for the next update.")
    if state["missing_usage_events"]:
        notes.append("Some usage/lifecycle records did not provide final usage; missing amounts are unknown, not zero.")
    if state["observed_through"] is None:
        notes.append("The source supplied no usage timestamp; read_at is not the usage timestamp.")
    return {"project_id": state["project_id"], "status": state["status"],
            "usage": state["usage"], "observed_through": state["observed_through"],
            "read_at": state.get("read_at"), "started_at": state["started_at"],
            "coverage": {"kind": "observed_interval", "sources": 1,
                         "source_format": state["source_format"], "session_id": state["session_id"],
                         "usage_events_since_baseline": state["usage_events"],
                         "missing_usage_events": state["missing_usage_events"],
                         "pending": state["status"] not in CLOSED,
                         "project_attribution": "not_proven", "subagents": "not_included"},
            "notes": notes}


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("begin", "update", "end", "report"):
        command = commands.add_parser(name)
        command.add_argument("--ledger", required=True, type=Path)
        command.add_argument("--output", type=Path, help="New sanitized report file; never overwrites an existing file.")
        if name == "begin":
            command.add_argument("--project-id", required=True)
            command.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    ledger = args.ledger.expanduser().resolve()
    lock = ledger.with_name(ledger.name + ".lock")
    locked = False
    try:
        if args.output and args.output.expanduser().exists():
            raise ValueError("--output must be a new report file.")
        if args.output and args.output.expanduser().resolve() in (ledger, lock):
            raise ValueError("Report path must differ from the ledger and its lock.")
        if args.command != "report":
            ledger.parent.mkdir(parents=True, exist_ok=True)
            with lock.open("x", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
            locked = True
        if args.command == "begin":
            if ledger.exists():
                raise ValueError("Ledger already exists; use update instead of importing again.")
            state = begin(args.project_id, args.source.expanduser())
        else:
            state = json.loads(ledger.read_text(encoding="utf-8"))
            if state.get("schema_version") != 1:
                raise ValueError("Unsupported ledger version.")
            if args.command != "report":
                scan(state)
        if args.command == "end":
            close(state)
        if args.command != "report":
            atomic_write(ledger, state)
        result = report(state)
        if args.output:
            output = args.output.expanduser()
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False))
        return 1
    finally:
        if locked:
            lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
