"""Run one seeded random-versus-random game as a minimal integration check."""

import sys

from bots.random_bot import play
from rig.runner import run_game


def main() -> int:
    result = run_game(play, play, black_seed=17, white_seed=29)
    if result.termination != "normal":
        print(
            f"Smoke game failed: {result.termination}; "
            f"forfeiting_player={result.forfeiting_player}; error={result.error}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Smoke game completed normally: winner={result.winner}, "
        f"black={result.black_count}, white={result.white_count}, "
        f"actions={len(result.actions)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
