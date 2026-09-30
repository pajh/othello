"""Stateless random bot: uniform choice among legal moves."""

import random

from rig.types import Observation

# ===================================================================
# SETTINGS — bot identity. Edit these constants, then increment VERSION
# by one per completed saved edit revision of this file (not per
# keystroke). The ID is what run reports and metadata display.
# ===================================================================
VERSION = '001'
BOTNAME = 'RAND'
ID = f'{BOTNAME}-{VERSION}'
# ===================================================================


def get_id() -> str:
    """Return this bot's ID, e.g. ``RAND-001``.

    The calling convention for every bot: run tooling reads the ID from the
    module so a report or metadata record says which bot produced a game,
    independent of the module path it was imported under.
    """
    return ID


def play(observation: Observation, *, rng: random.Random) -> int | None:
    """Return a uniformly random legal move, or None if there are none.

    The runner supplies a separate random.Random to each seat, so both
    seats can share this stateless function. This function keeps no
    per-game state and needs no reset or factory.
    """
    if not observation.legal_moves:
        return None
    return rng.choice(observation.legal_moves)
