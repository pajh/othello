"""Single-game runner: drives one Othello game between two bots.

The runner owns the turn loop, per-seat RNGs, action validation and
forfeit handling.  Bots are plain callables implementing
``play(observation, *, rng) -> int | None``; see rig.types for the
observation contract.  No loader, registry or framework is involved.
"""

import random
from dataclasses import dataclass
from typing import Callable, Literal

from rig import engine
from rig.engine import Board
from rig.types import Observation, PreviousAction

# A bot callable: play(observation, *, rng) -> int | None.
Bot = Callable[..., int | None]


@dataclass(frozen=True)
class GameResult:
    """Outcome of one game.

    board: final board, or the board at the moment of forfeit.
    black_count / white_count: disc counts on that board; for a forfeit
        they are informational only and do not determine the winner.
    winner: engine.BLACK, engine.WHITE, or EMPTY (draw).
    termination: 'normal' (terminal position reached) or 'forfeit'.
    forfeiting_player: the colour that forfeited, or None for a normal
        game.
    error: "<ExceptionType>: <message>" for a bot exception, an
        invalid-action explanation for a rejected move, or None.
    actions: accepted (colour, action) pairs in order; action is a move
        square 0..63 or None for a pass.  Rejected actions never appear
        and never change the board.
    training_eligible: True only for normal games.
    """

    board: Board
    black_count: int
    white_count: int
    winner: int
    termination: Literal['normal', 'forfeit']
    forfeiting_player: int | None
    error: str | None
    actions: tuple[tuple[int, int | None], ...]
    training_eligible: bool


def _forfeit_result(
    board: Board,
    forfeiting_player: int,
    error: str,
    actions: list[tuple[int, int | None]],
) -> GameResult:
    """Build a GameResult for a forfeit by *forfeiting_player*."""
    black_count, white_count = engine.disc_counts(board)
    winner = engine.WHITE if forfeiting_player == engine.BLACK else engine.BLACK
    return GameResult(
        board=board,
        black_count=black_count,
        white_count=white_count,
        winner=winner,
        termination='forfeit',
        forfeiting_player=forfeiting_player,
        error=error,
        actions=tuple(actions),
        training_eligible=False,
    )


def run_game(
    black_play: Bot,
    white_play: Bot,
    *,
    black_seed: int = 0,
    white_seed: int = 1,
) -> GameResult:
    """Play one game from the initial position and return its result.

    black_play / white_play are callables implementing
    ``play(observation, *, rng) -> int | None``.  Each seat receives a
    fresh random.Random built from its seed, so a stateless bot may be
    shared by both seats.  Black moves first.
    """
    board = engine.initial_board()
    plays = {engine.BLACK: black_play, engine.WHITE: white_play}
    rngs = {
        engine.BLACK: random.Random(black_seed),
        engine.WHITE: random.Random(white_seed),
    }
    actions: list[tuple[int, int | None]] = []
    previous_action = PreviousAction(kind='start')
    player = engine.BLACK

    while not engine.is_terminal(board):
        legal_moves = engine.legal_moves(board, player)
        observation = Observation(
            board=board,
            player=player,
            legal_moves=legal_moves,
            previous_action=previous_action,
        )
        try:
            action = plays[player](observation, rng=rngs[player])
        except Exception as exc:
            # Bot failure: forfeit to the opponent.  BaseException (e.g.
            # KeyboardInterrupt) is deliberately not caught.
            return _forfeit_result(
                board, player, f"{type(exc).__name__}: {exc}", actions
            )
        try:
            board = engine.apply_move(board, player, action)
        except ValueError as exc:
            # Invalid action (illegal move or improper pass): forfeit.
            # The board is unchanged and the action is not recorded.
            return _forfeit_result(
                board, player, f"invalid action: {exc}", actions
            )
        actions.append((player, action))
        if action is None:
            previous_action = PreviousAction(kind='pass')
        else:
            previous_action = PreviousAction(kind='move', square=action)
        player = engine.WHITE if player == engine.BLACK else engine.BLACK

    black_count, white_count = engine.disc_counts(board)
    return GameResult(
        board=board,
        black_count=black_count,
        white_count=white_count,
        winner=engine.winner(board),
        termination='normal',
        forfeiting_player=None,
        error=None,
        actions=tuple(actions),
        training_eligible=True,
    )
