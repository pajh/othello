#!/usr/bin/env python3
"""Evaluate Edax best replies for an existing opening prefix file.

Reads comma-separated coordinate histories (a blank line is the empty history)
and writes one line per input history: ``<history>=<recommended move>``.  Each
input chunk is handled by one persistent Edax process (``-n-tasks 1``); the
per-query history is reached with ``undo`` and ``play`` only, never ``new`` or
``setboard``.  A raw log per worker and one JSONL metadata file are written
beside the output.  Standard library only.

A parameterised early-runtime policy reports per-worker progress and a
provisional total estimate, and can stop a run that is estimating too long.
Completed results are snapshotted to a partial JSONL file before any stop.
"""

import argparse
import json
import os
import re
import select
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from rig.engine import BLACK, apply_move, initial_board, legal_moves

ROOT = Path(__file__).resolve().parents[1]
EDAX_BINARY = ROOT / "tools" / "edax" / "lEdax-x86-64"
EDAX_EVAL = ROOT / "tools" / "edax" / "data" / "eval.dat"
EDAX_BOOK = ROOT / "tools" / "edax" / "data" / "book.dat"

_READ_TIMEOUT = 900.0   # seconds without any byte while a command is pending
_STOP_POLL = 0.5        # seconds between stop checks while waiting for output
_MOVE_TOKEN = re.compile(r"[a-hA-H][1-8]")
_DEPTH_TOKEN = re.compile(r"(\d+)(?:@(\d+)%)?")
_SCORE_TOKEN = re.compile(r"([<>?]?)([+-]\d+)")


class EvaluationError(RuntimeError):
    """A visible failure: bad input, protocol error or illegal Edax reply."""


def coordinate_to_square(token):
    col = ord(token[0]) - ord("a")
    row = int(token[1:]) - 1
    if not (0 <= col < 8 and 0 <= row < 8):
        raise EvaluationError("bad coordinate: %s" % token)
    return row * 8 + col


def square_to_coordinate(square):
    row, col = divmod(square, 8)
    return "%s%d" % (chr(ord("a") + col), row + 1)


def parse_row(line):
    """Return (history string, list of square indices) for one input line."""
    tokens = [token for token in line.split(",") if token != ""]
    actions = []
    for token in tokens:
        if token == "pass":
            raise EvaluationError(
                "unsupported input: forced pass in history %r" % line)
        actions.append(coordinate_to_square(token))
    return line, actions


def replay(actions):
    """Replay *actions* from the initial board; return (board, player)."""
    board = initial_board()
    player = BLACK
    for square in actions:
        board = apply_move(board, player, square)
        player = -player
    return board, player


def compute_lcp(current, target):
    """Length of the longest common prefix of two move lists."""
    limit = min(len(current), len(target))
    i = 0
    while i < limit and current[i] == target[i]:
        i += 1
    return i


def chunk_bounds(total, cores):
    """Contiguous near-equal (start, end) chunks preserving order."""
    base, remainder = divmod(total, cores)
    bounds = []
    start = 0
    for index in range(cores):
        size = base + (1 if index < remainder else 0)
        if size:
            bounds.append((start, start + size))
            start += size
    return bounds


def parse_result(text):
    """Return the final search result parsed from Edax output, or ``None``."""
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        tokens = line.split()
        depth_match = _DEPTH_TOKEN.fullmatch(tokens[0])
        if depth_match is None or len(tokens) < 3:
            continue
        score_match = _SCORE_TOKEN.fullmatch(tokens[1])
        if score_match is None:
            continue
        move = None
        move_index = None
        for index in range(2, len(tokens)):
            if _MOVE_TOKEN.fullmatch(tokens[index]):
                move = tokens[index].lower()
                move_index = index
                break
        if move is None:
            continue
        time_token = tokens[2] if move_index > 2 else None
        nodes_token = tokens[3] if move_index > 3 else None
        return {
            "depth": int(depth_match.group(1)),
            "selectivity": int(depth_match.group(2)) if depth_match.group(2)
            else 100,
            "score": int(score_match.group(2)),
            "time": time_token,
            "nodes": int(nodes_token) if nodes_token and nodes_token.isdigit()
            else None,
            "move": move,
        }
    return None


def build_edax_command(level):
    command = [
        str(EDAX_BINARY),
        "-eval-file", str(EDAX_EVAL),
        "-book-file", str(EDAX_BOOK),
        "-book-usage", "off",
        "-level", str(level),
        "-n-tasks", "1",
        # Mode 3 is "human/human": Edax never plays on its own.  Mode 0 would
        # make Edax auto-play White and corrupt the board between queries.
        "-mode", "3",
        "-ponder", "off",
        "-auto-store", "off",
        "-verbose", "0",
    ]
    if shutil.which("stdbuf"):
        command = ["stdbuf", "-oL"] + command
    return command


def build_output_text(rows, results):
    lines = []
    for index, (history, _) in enumerate(rows):
        record = results[index]
        lines.append("%s=%s" % (history, record["move"]))
    return "\n".join(lines) + "\n"


def build_metadata_text(rows, results):
    """JSONL for every available record, in original index order."""
    lines = []
    for index, (history, _) in enumerate(rows):
        record = results[index]
        if record is None:
            continue
        lines.append(json.dumps({
            "index": index,
            "history": history,
            "move": record["move"],
            "depth": record["depth"],
            "selectivity": record["selectivity"],
            "score": record["score"],
            "nodes": record["nodes"],
            "time": record["time"],
            "seconds": record["seconds"],
            "worker": record["worker"],
        }, sort_keys=True))
    return ("\n".join(lines) + "\n") if lines else ""


def build_runtime_summary(level, cores, total, completed, elapsed, reason,
                          last_estimate_hours, worker_counts):
    lines = [
        "level: %d" % level,
        "cores: %d" % cores,
        "total: %d" % total,
        "completed: %d" % completed,
        "elapsed_seconds: %.1f" % elapsed,
        "reason: %s" % reason,
        "last_estimate_hours: %s" % (
            "%.2f" % last_estimate_hours if last_estimate_hours is not None
            else "unknown"),
    ]
    for worker_id, (done, assigned) in enumerate(worker_counts):
        lines.append("worker %d: %d/%d" % (worker_id, done, assigned))
    return "\n".join(lines) + "\n"


def write_atomic(path, text):
    """Write *text* to *path* via a sibling temporary file."""
    temporary = Path(str(path) + ".part")
    with temporary.open("w") as handle:
        handle.write(text)
    os.replace(temporary, path)


class RuntimePolicy:
    """Provisional runtime estimate and stopping rule.

    The caller supplies ``now`` so behaviour can be simulated without waiting.
    Edax's analysis level is never consulted or changed here.
    """

    def __init__(self, start, check_after, check_interval,
                 max_estimated_seconds, max_seconds):
        self.start = start
        self.check_after = check_after
        self.check_interval = check_interval
        self.max_estimated_seconds = max_estimated_seconds
        self.max_seconds = max_seconds
        self.next_check = start + check_after
        self.streak = 0
        self.last_estimate_hours = None
        self.reason = None

    def hard_limit_reached(self, now):
        return (now - self.start) >= self.max_seconds

    def due(self, now):
        return now >= self.next_check

    def check(self, now, workers):
        """``workers`` is a list of ``(completed, assigned)`` pairs."""
        elapsed = now - self.start
        worker_reports = []
        max_remaining = 0.0
        unknown = False
        for worker_id, (completed, assigned) in enumerate(workers):
            remaining = assigned - completed
            if remaining <= 0:
                worker_reports.append({
                    "worker": worker_id, "completed": completed,
                    "assigned": assigned, "rate": None,
                    "remaining_seconds": 0.0})
                continue
            if completed <= 0 or elapsed <= 0:
                unknown = True
                worker_reports.append({
                    "worker": worker_id, "completed": completed,
                    "assigned": assigned, "rate": 0.0,
                    "remaining_seconds": None})
                continue
            rate = completed / elapsed
            remaining_seconds = remaining / rate
            max_remaining = max(max_remaining, remaining_seconds)
            worker_reports.append({
                "worker": worker_id, "completed": completed,
                "assigned": assigned, "rate": rate,
                "remaining_seconds": remaining_seconds})

        if unknown:
            estimate_seconds = None
            self.streak = 0
        else:
            estimate_seconds = elapsed + max_remaining
            self.last_estimate_hours = estimate_seconds / 3600.0
            if estimate_seconds > self.max_estimated_seconds:
                self.streak += 1
            else:
                self.streak = 0
        self.next_check = now + self.check_interval
        if self.streak >= 3:
            self.reason = "STOPPED_ESTIMATE"
        return {
            "elapsed": elapsed,
            "workers": worker_reports,
            "estimate_seconds": estimate_seconds,
            "estimate_hours": (estimate_seconds / 3600.0)
            if estimate_seconds is not None else None,
            "streak": self.streak,
            "limit_hours": self.max_estimated_seconds / 3600.0,
        }


def print_runtime_report(report):
    estimate = report["estimate_hours"]
    print("runtime check: elapsed=%.1fs streak=%d/3 estimate=%s limit=%.2fh"
          % (report["elapsed"], report["streak"],
             ("%.2fh" % estimate) if estimate is not None else "unknown",
             report["limit_hours"]), flush=True)
    for worker in report["workers"]:
        rate = ("%.3f/s" % worker["rate"]) if worker["rate"] else "unknown"
        remaining = ("%.0fs" % worker["remaining_seconds"]) \
            if worker["remaining_seconds"] is not None else "unknown"
        print("  worker %d: %d/%d rate=%s remaining=%s"
              % (worker["worker"], worker["completed"], worker["assigned"],
                 rate, remaining), flush=True)


class EdaxWorker:
    def __init__(self, worker_id, assignments, level, results, progress, stop,
                 log_path):
        self.worker_id = worker_id
        self.assignments = assignments
        self.level = level
        self.results = results
        self.progress = progress
        self.stop = stop
        self.log_path = log_path
        self.error = None
        self.process = None
        self.buffer = b""
        self.log = None

    def _drain(self, timeout):
        ready, _, _ = select.select([self.process.stdout.fileno()], [], [], timeout)
        if not ready:
            return False
        data = os.read(self.process.stdout.fileno(), 65536)
        if not data:
            raise EvaluationError(
                "Edax stdout closed unexpectedly (worker %d)" % self.worker_id)
        self.buffer += data
        self.log.write(data)
        self.log.flush()
        return True

    def _at_prompt(self):
        # The command prompt is a bare ">" at the very end of the output.  With
        # -verbose 0 it follows the previous line's newline (or is the first
        # output).  A score bound ">" is preceded by a space and followed by
        # digits, so it is never mistaken for completion.
        return self.buffer == b">" or self.buffer.endswith(b"\n>")

    def read_until_prompt(self):
        # A completed prompt returns immediately.  While still waiting, stop is
        # polled every _STOP_POLL seconds; the 900 s no-byte timeout is kept via
        # a monotonic deadline so the poll adds no delay on normal output.
        deadline = time.monotonic() + _READ_TIMEOUT
        while True:
            if self._at_prompt():
                text = self.buffer.decode("latin-1")
                self.buffer = b""
                return text
            if self.stop.is_set():
                raise EvaluationError("cancelled (worker %d)" % self.worker_id)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EvaluationError(
                    "timed out waiting for an Edax prompt (worker %d)"
                    % self.worker_id)
            if self._drain(min(_STOP_POLL, remaining)):
                deadline = time.monotonic() + _READ_TIMEOUT

    def command(self, text):
        self.process.stdin.write((text + "\n").encode("ascii"))
        self.process.stdin.flush()
        return self.read_until_prompt()

    def _start(self):
        before = (EDAX_BOOK.stat().st_size, EDAX_BOOK.stat().st_mtime_ns)
        self.log = open(self.log_path, "wb")
        self.process = subprocess.Popen(
            build_edax_command(self.level),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0)
        startup = self.read_until_prompt()
        if "New book" in startup:
            raise EvaluationError(
                "Edax created a new opening book at startup; provide a valid "
                "read-only %s before running (worker %d)"
                % (EDAX_BOOK, self.worker_id))
        after = (EDAX_BOOK.stat().st_size, EDAX_BOOK.stat().st_mtime_ns)
        if after != before:
            raise EvaluationError(
                "Edax modified %s at startup; refusing to continue (worker %d)"
                % (EDAX_BOOK, self.worker_id))

    def run(self):
        try:
            self._start()
            current = []
            for index, actions, history in self.assignments:
                if self.stop.is_set():
                    raise EvaluationError("cancelled (worker %d)" % self.worker_id)
                started = time.monotonic()
                common = compute_lcp(current, actions)
                for _ in range(len(current) - common):
                    self.command("undo")
                if common < len(actions):
                    suffix = "".join(
                        square_to_coordinate(square) for square in actions[common:])
                    self.command("play " + suffix)
                current = actions

                output = self.command("hint 1")
                parsed = parse_result(output)
                if parsed is None:
                    raise EvaluationError(
                        "no search result for history %r (worker %d, row %d)"
                        % (history, self.worker_id, index))

                board, player = replay(actions)
                if coordinate_to_square(parsed["move"]) not in legal_moves(board, player):
                    raise EvaluationError(
                        "illegal Edax reply %s for history %r (worker %d, row %d)"
                        % (parsed["move"], history, self.worker_id, index))

                parsed["seconds"] = time.monotonic() - started
                parsed["worker"] = self.worker_id
                self.results[index] = parsed
                self.progress()
        except BaseException as exc:  # noqa: BLE001 - reported by the main thread
            self.error = exc
            self.stop.set()
        finally:
            self._finish()

    def _finish(self):
        if self.process is not None:
            try:
                if self.process.poll() is None:
                    try:
                        self.process.stdin.write(b"quit\n")
                        self.process.stdin.flush()
                    except Exception:
                        pass
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        if self.log is not None:
            self.log.close()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="existing comma-separated prefix file")
    parser.add_argument("--output", required=True, type=Path,
                        help="output file; parent directory is created")
    parser.add_argument("--cores", type=int, default=4,
                        help="number of independent Edax processes (default 4)")
    parser.add_argument("--depth", type=int, default=10,
                        help="Edax search level, not a full-width guarantee "
                             "(default 10)")
    parser.add_argument("--eta-check-after", type=float, default=600.0,
                        help="seconds before the first runtime check (default 600)")
    parser.add_argument("--eta-check-interval", type=float, default=150.0,
                        help="seconds between runtime checks (default 150)")
    parser.add_argument("--max-estimated-hours", type=float, default=5.0,
                        help="stop after 3 checks estimating above this "
                             "(default 5)")
    parser.add_argument("--max-hours", type=float, default=5.0,
                        help="hard elapsed limit in hours (default 5)")
    return parser.parse_args()


def snapshot_counts(results, bounds, lock):
    with lock:
        return [(sum(1 for record in results[start:end] if record is not None),
                 end - start) for start, end in bounds]


def main():
    args = parse_args()
    source = args.input.expanduser()
    output = args.output.expanduser()

    if args.cores < 1:
        raise SystemExit("--cores must be at least 1")
    if args.depth < 1:
        raise SystemExit("--depth must be at least 1")
    if args.eta_check_after <= 0:
        raise SystemExit("--eta-check-after must be positive")
    if args.eta_check_interval <= 0:
        raise SystemExit("--eta-check-interval must be positive")
    if args.max_estimated_hours <= 0:
        raise SystemExit("--max-estimated-hours must be positive")
    if args.max_hours <= 0:
        raise SystemExit("--max-hours must be positive")
    if not source.is_file():
        raise SystemExit("input file not found: %s" % source)
    if output.exists():
        raise SystemExit("refusing to overwrite existing output: %s" % output)
    for required in (EDAX_BINARY, EDAX_EVAL, EDAX_BOOK):
        if not required.is_file():
            raise SystemExit("required Edax asset missing: %s" % required)

    with source.open("r") as handle:
        raw_lines = handle.read().split("\n")
    if raw_lines and raw_lines[-1] == "":
        raw_lines.pop()
    rows = [parse_row(line) for line in raw_lines]
    if not rows:
        raise SystemExit("input file has no rows: %s" % source)

    total = len(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    stem = output.with_suffix("").name
    meta_path = output.parent / (stem + ".results.jsonl")
    partial_path = output.parent / (stem + ".partial.results.jsonl")
    summary_path = output.parent / (stem + ".runtime-summary.txt")
    log_template = str(output.parent / (stem + ".worker%d.log"))
    temp_path = output.with_name(output.name + ".part")

    results = [None] * total
    lock = threading.Lock()
    completed = [0]

    def progress():
        with lock:
            completed[0] += 1

    stop = threading.Event()
    bounds = chunk_bounds(total, args.cores)
    threads = []
    workers = []
    started = time.monotonic()
    for worker_id, (start, end) in enumerate(bounds):
        assignments = [
            (index, rows[index][1], rows[index][0])
            for index in range(start, end)
        ]
        worker = EdaxWorker(worker_id, assignments, args.depth, results,
                            progress, stop, log_template % worker_id)
        thread = threading.Thread(target=worker.run, name="edax-%d" % worker_id)
        thread.worker = worker
        workers.append(worker)
        threads.append(thread)
        thread.start()

    policy = RuntimePolicy(
        started, args.eta_check_after, args.eta_check_interval,
        args.max_estimated_hours * 3600.0, args.max_hours * 3600.0)
    reason = None
    last_time = started
    last_count = 0
    last_snapshot = started
    while any(thread.is_alive() for thread in threads):
        time.sleep(0.5)
        now = time.monotonic()
        with lock:
            done = completed[0]
        if done != last_count and (now - last_time >= 5.0 or done - last_count >= 25):
            elapsed = now - started
            rate = done / elapsed if elapsed > 0 else 0.0
            eta = (" eta=%.1fs" % ((total - done) / rate)) if rate > 0 else " eta=unknown"
            print("progress: %d/%d elapsed=%.1fs%s" % (done, total, elapsed, eta),
                  flush=True)
            last_time = now
            last_count = done
        if policy.hard_limit_reached(now):
            reason = "STOPPED_TIME"
            print("hard time limit reached: %.1fs" % (now - started), flush=True)
            stop.set()
            break
        if policy.due(now):
            report = policy.check(now, snapshot_counts(results, bounds, lock))
            print_runtime_report(report)
            if policy.reason:
                reason = policy.reason
                print("runtime policy stop: %s" % reason, flush=True)
                stop.set()
                break
        if now - last_snapshot >= 5.0:
            write_atomic(partial_path, build_metadata_text(rows, results))
            last_snapshot = now

    stop.set()
    for thread in threads:
        thread.join()

    counts = snapshot_counts(results, bounds, lock)
    done = sum(count for count, _ in counts)
    write_atomic(partial_path, build_metadata_text(rows, results))

    errors = [worker.error for worker in workers if worker.error]
    real_errors = [error for error in errors
                   if "cancelled (worker" not in str(error)]
    failure = None
    if real_errors:
        reason = "FAILED"
        failure = real_errors[0]
    elif reason is None:
        if done == total:
            reason = "COMPLETE"
        else:
            reason = "FAILED"
            failure = "incomplete without a stop reason"

    elapsed = time.monotonic() - started
    write_atomic(summary_path, build_runtime_summary(
        args.depth, args.cores, total, done, elapsed, reason,
        policy.last_estimate_hours, counts))

    if reason != "COMPLETE":
        if temp_path.exists():
            temp_path.unlink()
        print("run did not complete: reason=%s completed=%d/%d elapsed=%.1fs"
              % (reason, done, total, elapsed), flush=True)
        print("partial results: %s" % partial_path)
        print("runtime summary: %s" % summary_path)
        raise SystemExit("evaluation stopped: %s%s"
                         % (reason, (": %s" % failure) if failure else ""))

    with temp_path.open("w") as handle:
        handle.write(build_output_text(rows, results))
    os.replace(temp_path, output)
    write_atomic(meta_path, build_metadata_text(rows, results))

    print("completed %d/%d in %.1fs cores=%d depth=%d"
          % (total, total, elapsed, args.cores, args.depth))
    print("output: %s" % output)
    print("metadata: %s" % meta_path)
    print("runtime summary: %s" % summary_path)
    print("worker logs: %s" % (log_template % 0) + " ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
