"""Learned bot: greedy one-move evaluation scored by the trained OutcomeMLP.

Separate from :mod:`bots.max_bot`, which stays unchanged and keeps its
deterministic placeholder score. This module has the same move-selection
structure — iterate the legal moves the observation supplies, apply each with
``rig.engine.apply_move``, score the resulting board from the acting player's
perspective, keep the highest — but :func:`board_score` is real model
inference instead of a hash.

The checkpoint is selected by the **required** environment variable
``OTHELLO_NN_CHECKPOINT``, resolved and loaded once when this module is
imported. There is no hardcoded run, no implicit "newest run" scan and no
silent fallback, so a missing variable, missing file or incompatible
checkpoint becomes a setup error before any match starts rather than a
forfeit part-way through one. A user-run helper sets the variable, for
example::

    OTHELLO_NN_CHECKPOINT=checkpoints/first-model/run-<uuid>/best.pt \\
        venv/bin/python -m rig.cli --bot1 bots.nn_bot --bot2 bots.random_bot ...

Loading once per process also means the read-only network is shared by both
colours and every game in a batch without reloading the file, and no state is
mutated during play, so no reset hook or factory is needed.

The stored checkpoint also carries optimizer and resume metadata from
training; inference ignores all of that and uses only the model weights.
Every candidate board for a position is scored in a **single batched
forward call** (see :func:`board_scores`), with no search, thread tuning,
device selection or gradient graph. Scores are the model's expected-outcome
estimate, not a proven game value, and this bot's playing strength is a
separate measurement from its prediction loss.

Batching the same weights over a wider input can differ from separate
single-board forwards in the last floating-point bits, so games are not
promised to be byte-identical across revisions that change this; the
calculation and the sampling rules are the same.

Two ways to play are available. The module-level :func:`play` is the plain
stateless greedy primitive and is unchanged, so existing callers and greedy
evaluations keep working. :func:`create_player` is the configured form: it
returns a fresh per-game, per-seat callable that plays the first
``RANDOM_MOVES`` of *its own* moves uniformly at random and then picks among
the scored moves using ``TEMPERATURE``. A runner that wants that behaviour
must call the factory once per seat per game. ``TEMPERATURE = 0`` makes the
factory greedy too, matching :func:`play`; 0.05 is a starting value rather
than a tuned one, and a lower value keeps choices closer to the model's
favourite move.
"""

import math
import os
import random

import torch

from rig import engine
from rig.types import Observation
from training.model import MODEL_VERSION, OutcomeMLP

# ===================================================================
# SETTINGS — bot identity, opening and sampling. Edit these constants,
# then increment VERSION by one per completed saved edit revision of this
# file (not per keystroke). The ID is what run reports and metadata
# display, and it includes the random-opening count and the sampling
# temperature. This is the code version of the bot, not a
# model-training generation.
# ===================================================================
VERSION = '004'
BOTNAME = 'NN'
RANDOM_MOVES = 2
# Temperature for choosing among scored moves after the random opening.
# 0.05 is a starting value, not a tuned one: a higher value spreads
# choices more, 0 means greedy (the first tied best move), which is what
# the module-level play() always does.
TEMPERATURE = 0.05
# Plain decimal rather than exponent, so the ID stays unambiguous in
# reports and filenames.
ID = f'{BOTNAME}-{VERSION}-R{RANDOM_MOVES}-T{TEMPERATURE:g}'
# ===================================================================


def _validate_settings():
    """Reject unusable SETTINGS once, at import, with a clear message.

    Bools are rejected wherever a number is required, since ``True`` would
    otherwise pass as 1.
    """
    if isinstance(RANDOM_MOVES, bool) or not isinstance(RANDOM_MOVES, int):
        raise ValueError('nn_bot SETTINGS: RANDOM_MOVES must be an integer, '
                         'got %r' % (RANDOM_MOVES,))
    if RANDOM_MOVES < 0:
        raise ValueError('nn_bot SETTINGS: RANDOM_MOVES must be 0 or greater, '
                         'got %r' % (RANDOM_MOVES,))
    if isinstance(TEMPERATURE, bool) or not isinstance(TEMPERATURE, (int, float)):
        raise ValueError('nn_bot SETTINGS: TEMPERATURE must be a number, got '
                         '%r' % (TEMPERATURE,))
    if not math.isfinite(TEMPERATURE) or TEMPERATURE < 0:
        raise ValueError('nn_bot SETTINGS: TEMPERATURE must be finite and 0 '
                         'or greater, got %r' % (TEMPERATURE,))


_validate_settings()

_SIZE = 8
_CELLS = _SIZE * _SIZE
_PLANES = 2

#: Environment variable naming the checkpoint to load. Required.
CHECKPOINT_ENV = 'OTHELLO_NN_CHECKPOINT'


def get_id() -> str:
    """Return this bot's ID, e.g. ``NN-003-R2-T0.05``.

    The calling convention for every bot: run tooling reads the ID from the
    module so a report or metadata record says which bot produced a game,
    independent of the module path it was imported under. The ID embeds this
    file's ``VERSION``, ``RANDOM_MOVES`` and ``TEMPERATURE``, so a change to
    any of them is visible in run reports. It is the code version of the bot,
    not a model-training generation; the checkpoint itself is still selected
    by :data:`CHECKPOINT_ENV`.
    """
    return ID

_EXPECTED_CHECKPOINT_VERSION = 1
_EXPECTED_ENCODING_VERSION = 1


def _load_model():
    """Load the checkpoint named by the environment and return the model.

    Called once at import time. Errors name the environment variable and the
    path, so a setup mistake is obvious before any game starts.
    """
    raw_path = '/home/paul/dev/othello/checkpoints/second-model/run-selfplay-5000/best.pt'  # THROWAWAY evaluation clone; develop only nn_bot.py.
    if not raw_path or not raw_path.strip():
        raise RuntimeError(
            '%s is not set: name the checkpoint to play with, for example '
            'OTHELLO_NN_CHECKPOINT=checkpoints/first-model/run-<uuid>/best.pt'
            % CHECKPOINT_ENV
        )
    path = os.path.abspath(os.path.expanduser(raw_path.strip()))
    if not os.path.exists(path):
        raise RuntimeError(
            '%s=%r does not exist (resolved to %s)'
            % (CHECKPOINT_ENV, raw_path.strip(), path)
        )
    if not os.path.isfile(path):
        raise RuntimeError(
            '%s=%r is not a file (resolved to %s)'
            % (CHECKPOINT_ENV, raw_path.strip(), path)
        )

    try:
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    except Exception as exc:
        raise RuntimeError('%s=%r could not be loaded as a weights-only '
                           'checkpoint: %s: %s'
                           % (CHECKPOINT_ENV, raw_path.strip(),
                              type(exc).__name__, exc)) from exc
    if not isinstance(checkpoint, dict):
        raise RuntimeError('%s=%r does not contain a checkpoint dictionary '
                           '(got %s)' % (CHECKPOINT_ENV, raw_path.strip(),
                                         type(checkpoint).__name__))

    def version(field, expected):
        value = checkpoint.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise RuntimeError('%s=%r field %r must be the integer %d, got %r'
                               % (CHECKPOINT_ENV, raw_path.strip(), field,
                                  expected, value))
        if value != expected:
            raise RuntimeError('%s=%r is incompatible: %s is %d, this bot '
                               'requires %d'
                               % (CHECKPOINT_ENV, raw_path.strip(), field,
                                  value, expected))

    version('checkpoint_version', _EXPECTED_CHECKPOINT_VERSION)
    version('model_version', MODEL_VERSION)
    version('encoding_version', _EXPECTED_ENCODING_VERSION)

    state = checkpoint.get('model_state_dict')
    if state is None:
        raise RuntimeError('%s=%r has no model_state_dict'
                           % (CHECKPOINT_ENV, raw_path.strip()))

    model = OutcomeMLP()
    try:
        model.load_state_dict(state, strict=True)
    except Exception as exc:
        raise RuntimeError('%s=%r weights do not fit OutcomeMLP: %s: %s'
                           % (CHECKPOINT_ENV, raw_path.strip(),
                              type(exc).__name__, exc)) from exc
    for name, parameter in model.named_parameters():
        if not bool(torch.isfinite(parameter).all()):
            raise RuntimeError('%s=%r has nonfinite weights in %r'
                               % (CHECKPOINT_ENV, raw_path.strip(), name))
    model.eval()
    return model


# Loaded once per process; read-only afterwards and shared by both seats.
_MODEL = _load_model()


def encode_board(board: engine.Board, player: int) -> torch.Tensor:
    """Return *board* as a float32 CPU tensor ``(1, 2, 8, 8)`` for *player*.

    Encoding version 1, matching the dataset: the position is taken from
    *player*'s own perspective, plane 0 marks that player's discs, plane 1
    the opponent's, and empty squares are 0 in both. Square *n* maps to row
    ``n // 8`` and column ``n % 8``. There is no absolute-colour channel, no
    flip, no scaling and no opponent perspective, so the same position
    produces swapped planes when the other player is scored.
    """
    opponent = engine.WHITE if player == engine.BLACK else engine.BLACK
    own_plane = torch.zeros((_SIZE, _SIZE), dtype=torch.float32)
    opponent_plane = torch.zeros((_SIZE, _SIZE), dtype=torch.float32)
    for square in range(_CELLS):
        cell = board[square]
        if cell == player:
            own_plane[square // _SIZE, square % _SIZE] = 1.0
        elif cell == opponent:
            opponent_plane[square // _SIZE, square % _SIZE] = 1.0
    return torch.stack((own_plane, opponent_plane), dim=0).unsqueeze(0)


def board_score(board: engine.Board, player: int) -> float:
    """Return the model's expected-outcome score in ``[0, 1]`` for *board*.

    One forward pass on the after-action position from *player*'s
    perspective, under ``torch.inference_mode`` so no gradient graph is
    built. The score is read from the first (and only) output, and a
    nonfinite or out-of-range result is rejected rather than returned.
    """
    encoded = encode_board(board, player)
    with torch.inference_mode():
        scores = _MODEL(encoded)
    score = float(scores[0])
    if not (score == score) or score in (float('inf'), float('-inf')):
        raise ValueError('model produced a nonfinite score %r' % score)
    if not 0.0 <= score <= 1.0:
        raise ValueError('model score %r is outside [0, 1]' % score)
    return score


def _check_score(value, position):
    """Return *value* as a float after checking it is finite and in ``[0, 1]``."""
    score = float(value)
    if not (score == score) or score in (float('inf'), float('-inf')):
        raise ValueError('model produced a nonfinite score %r' % score)
    if not 0.0 <= score <= 1.0:
        raise ValueError('model score %r is outside [0, 1]' % score)
    return score


def board_scores(boards, player: int) -> list:
    """Return one score per board in *boards*, all in a single forward call.

    *boards* is a sequence of engine boards for the same ``player``, in the
    order the caller wants scored. They are encoded from that player's
    perspective, stacked into one float32 CPU tensor shaped
    ``(len(boards), 2, 8, 8)`` and passed to the model in one call under
    ``torch.inference_mode``, so the returned list follows the same order as
    the input. Every score is range-checked before being returned.

    :func:`board_score` is this function for a single board and is kept
    compatible. Batched inference can differ from separate single-board
    forwards in the last floating-point bits, since the same weights are
    applied to a wider input; the difference is far below any effect on move
    choice.
    """
    if len(boards) == 0:
        return []
    encoded = [encode_board(board, player) for board in boards]
    batch = torch.cat(encoded, dim=0)
    with torch.inference_mode():
        raw = _MODEL(batch)
    return [_check_score(value, index) for index, value in enumerate(raw)]


def _candidate_boards(observation: Observation) -> list:
    """Return each legal move's resulting board, in supplied-move order."""
    return [
        engine.apply_move(observation.board, observation.player, move)
        for move in observation.legal_moves
    ]


def play(observation: Observation, *, rng: random.Random) -> int | None:
    """Return the legal move whose resulting board scores highest, or None.

    The candidate boards are built with ``rig.engine.apply_move`` in the order
    the observation supplies the legal moves, then scored in one batched
    forward call. The best move is kept, initialised from the first legal move
    with ``best_score = -inf`` and updated only on a strictly greater score,
    so ties still resolve to the first supplied move. No move is invented,
    legal moves are never recalculated, the input is not mutated and the
    perspective is never swapped to the opponent.

    ``rng`` is accepted for the shared bot contract and deliberately unused;
    the score depends only on the position. Returns None when the
    observation supplies no legal move, the required forced-pass answer.
    """
    if not observation.legal_moves:
        return None
    scores = board_scores(_candidate_boards(observation), observation.player)
    best_move = None
    best_score = float('-inf')
    for move, score in zip(observation.legal_moves, scores):
        if score > best_score:
            best_move = move
            best_score = score
    return best_move


def select_scored_move(observation: Observation, scores, rng: random.Random) -> int:
    """Return one legal move, sampled with probability from *scores*.

    *scores* holds one model score per entry of ``observation.legal_moves``,
    already in that order. Three cases:

    - a single legal move is returned directly, without drawing a random
      number, since there is nothing to choose between;
    - ``TEMPERATURE == 0`` returns the first move holding the best score,
      which is exactly the greedy behaviour of :func:`play` and avoids
      dividing by zero;
    - otherwise weights are ``exp((score - best) / TEMPERATURE)``. Subtracting
      the best score keeps the largest exponent at 0, so the largest weight is
      1 and the total is never zero. Normalising is unnecessary because
      ``random.choices`` accepts unnormalised weights.

    The draw uses only the *rng* passed in, so the runner's per-bot,
    per-game seeded RNG keeps a run reproducible. No clipping, cutoff,
    top-k, search or extra heuristic is applied.
    """
    moves = observation.legal_moves
    if len(moves) == 1:
        return moves[0]
    if TEMPERATURE == 0:
        best = max(scores)
        return moves[scores.index(best)]
    best = max(scores)
    weights = [math.exp((score - best) / TEMPERATURE) for score in scores]
    return rng.choices(moves, weights=weights, k=1)[0]


def create_player():
    """Return a fresh callable that opens randomly, then plays by temperature.

    The returned closure keeps this seat's own move counter, so it must be
    created once per seat per game; sharing one across games or seats would
    carry the opening into the wrong game. The model is **not** reloaded:
    :func:`board_score` and the module-level network stay shared and
    read-only.

    For the first ``RANDOM_MOVES`` actual moves the closure returns
    ``rng.choice(observation.legal_moves)``, uniform over the supplied legal
    moves, and those moves are neither scored nor chosen by score. A position
    with no legal moves returns None and does **not** consume part of the
    opening, since a forced pass is not a move. After the opening is spent,
    every legal move is scored from this player's perspective and
    :func:`select_scored_move` picks one using ``TEMPERATURE``.

    The counter is closure state only. There is no global counter, no
    dictionary keyed by rng, no reset heuristic and no class. The module-level
    :func:`play` remains the stateless greedy primitive, so an evaluation that
    wants purely greedy play can still call it directly.
    """
    remaining_random_moves = RANDOM_MOVES

    def play_with_opening_then_temperature(observation: Observation, *,
                                           rng: random.Random) -> int | None:
        nonlocal remaining_random_moves
        if not observation.legal_moves:
            return None
        if remaining_random_moves > 0:
            remaining_random_moves -= 1
            return rng.choice(observation.legal_moves)
        moves = observation.legal_moves
        if len(moves) == 1:
            # Nothing to choose between, so do not score or draw randomness.
            return moves[0]
        scores = board_scores(_candidate_boards(observation), observation.player)
        return select_scored_move(observation, scores, rng)

    return play_with_opening_then_temperature
