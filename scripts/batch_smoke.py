"""Run and inspect a two-game batch CLI smoke check.

Run after installing the project in the existing environment:
    venv/bin/python scripts/batch_smoke.py

Artifacts are kept under work/batch-smoke/ for inspection.
"""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "work" / "batch-smoke"


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prior_runs = {path.name for path in OUTPUT_DIR.glob("run-*") if path.is_dir()}
    command = [
        sys.executable,
        "-m",
        "rig.cli",
        "--bot1",
        "bots.random_bot",
        "--bot2",
        "bots.random_bot",
        "--games",
        "2",
        "--seed",
        "12345",
        "--output-dir",
        str(OUTPUT_DIR),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    _check(completed.returncode == 0,
           f"batch CLI exited with status {completed.returncode}")

    new_runs = [
        path
        for path in OUTPUT_DIR.glob("run-*")
        if path.is_dir() and path.name not in prior_runs
    ]
    _check(len(new_runs) == 1, f"expected one new run directory, found {len(new_runs)}")
    run_dir = new_runs[0]
    metadata = _read_json(run_dir / "metadata.json")
    records_path = run_dir / "games.jsonl"
    with records_path.open(encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    summary_path = OUTPUT_DIR / "run-summary.txt"
    summary = summary_path.read_text(encoding="utf-8")

    _check(metadata["master_seed"] == 12345, "metadata master seed mismatch")
    _check(metadata["requested_games"] == 2, "metadata requested game count mismatch")
    _check(len(records) == 2, f"expected two game records, found {len(records)}")
    _check("state: completed" in summary, "summary does not report completed state")
    _check("completed games: 2" in summary, "summary does not report two completed games")

    seen_seeds = set()
    for index, record in enumerate(records):
        _check(record["game_index"] == index, f"unexpected game index at record {index}")
        _check(record["termination"] == "normal", f"game {index} did not terminate normally")
        _check(record["training_eligible"] is True,
               f"game {index} is not marked training eligible")
        bots = record["bots"]
        _check(bots["1"]["colour"] != bots["2"]["colour"],
               f"game {index} bot colours are not distinct")
        expected_black_bot = "1" if index == 0 else "2"
        _check(bots[expected_black_bot]["colour"] == 1,
               f"game {index} did not alternate the Black bot")
        _check(bots["1"]["seed"] != bots["2"]["seed"],
               f"game {index} bot seeds are not distinct")
        seen_seeds.update((bots["1"]["seed"], bots["2"]["seed"]))
        boards = [record["final_board"]]
        boards.extend(position["board"] for position in record["positions"])
        _check(all(len(board) == 64 and set(board) <= set("012") for board in boards),
               f"game {index} contains a malformed board")

    _check(len(seen_seeds) == 4, "expected four distinct recorded bot seeds")
    print(f"Batch smoke check passed; inspect records in {run_dir}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"Batch smoke check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
