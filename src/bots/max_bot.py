"""Greedy one-move-evaluation bot with a deterministic placeholder score.

Framework for the user's requested greedy evaluation: for every legal move
the existing engine applies the move, the resulting board is scored from the
acting player's perspective, and the highest-scoring move is played. There is
no search beyond that single ply, no opponent modelling, no move ordering
heuristic and no learned model.

``board_score`` is deliberately a **placeholder**: a SHA-256 digest of the
resulting position, so the evaluation machinery can be exercised end to end
before any neural network exists. It is a clearly marked replacement point:
when a trained model is available, replace the body of ``board_score`` with
a model call and leave ``play`` unchanged. The placeholder's values carry no
strategic meaning, so this bot plays no better than chance in expectation;
its only current value is exercising the interface.

The module holds no state and needs no reset or factory, so the same
function can serve both seats. The ``rng`` argument exists for the shared bot
contract and is deliberately unused: the score is deterministic in the
position, so the same board and player always give the same value.
"""

import hashlib
import random

from rig import engine
from rig.types import Observation

# ===================================================================
# SETTINGS — bot identity. Edit these constants, then increment VERSION
# by one per completed saved edit revision of this file (not per
# keystroke). The ID is what run reports and metadata display.
# ===================================================================
VERSION = '001'
BOTNAME = 'MAX'
ID = f'{BOTNAME}-{VERSION}'
# ===================================================================

_SIZE = 8
_CELLS = _SIZE * _SIZE
_TWO_TO_64 = 2 ** 64

# Own disc, opponent disc and empty, in this bot's byte encoding.
_EMPTY_BYTE = 0
_OWN_BYTE = 1
_OPPONENT_BYTE = 2


def get_id() -> str:
    """Return this bot's ID, e.g. ``MAX-001``.

    The calling convention for every bot: run tooling reads the ID from the
    module so a report or metadata record says which bot produced a game,
    independent of the module path it was imported under. This is the code
    version of the bot, not a model-training generation.
    """
    return ID


def board_score(board: engine.Board, player: int) -> float:
    """Return a deterministic pseudo-random value in ``[0, 1]`` for *board*.

    The position is encoded from *player*'s perspective — 0 for an empty
    square, 1 for one of *player*'s discs, 2 for an opponent disc — hashed
    with SHA-256, and the first eight digest bytes are read big-endian and
    divided by ``2 ** 64``. The value is therefore stable across processes
    and runs, unlike a built-in hash or an RNG draw.

    Only ``[0, 1)`` is mathematically intended; the largest digest rounds to
    exactly 1.0 in float, so ``[0, 1]`` is accepted.

    This is a placeholder, not a quality measure. Replace this function with
    a model call when one exists; :func:`play` need not change.
    """
    opponent = engine.WHITE if player == engine.BLACK else engine.BLACK
    encoded = bytearray(_CELLS)
    for square, cell in enumerate(board):
        if cell == player:
            encoded[square] = _OWN_BYTE
        elif cell == opponent:
            encoded[square] = _OPPONENT_BYTE
        else:
            encoded[square] = _EMPTY_BYTE
    digest = hashlib.sha256(bytes(encoded)).digest()
    return int.from_bytes(digest[:8], 'big') / _TWO_TO_64


def play(observation: Observation, *, rng: random.Random) -> int | None:
    """Return the legal move whose resulting board scores highest, or None.

    Every legal move supplied by the observation is applied with
    ``rig.engine.apply_move`` and the resulting board is scored from this
    player's perspective. A move is kept only on a strictly greater score, so
    ties resolve to the first supplied move. No move is invented, legal
    moves are never recalculated, the input is not mutated, and the
    perspective is never swapped to the opponent.

    ``rng`` is accepted for the shared bot contract and deliberately unused,
    because the score depends only on the position.

    Returns None when the observation supplies no legal move, which is the
    required forced-pass answer.
    """
    if not observation.legal_moves:
        return None
    best_move = None
    best_score = float('-inf')
    for move in observation.legal_moves:
        resulting = engine.apply_move(observation.board, observation.player, move)
        score = board_score(resulting, observation.player)
        if score > best_score:
            best_move = move
            best_score = score
    return best_move
