"""Shared observation/action definitions for bots.

These are simple typed data containers, not a validation framework. The
runner is responsible for constructing Observations with valid data:
the board is the immutable tuple produced by rig.engine, player is
rig.engine.BLACK or rig.engine.WHITE, and legal_moves is the tuple
returned by rig.engine.legal_moves for that board and player. No engine
validation is duplicated here.
"""

from dataclasses import dataclass
from typing import Literal

from rig.engine import Board


@dataclass(frozen=True)
class PreviousAction:
    """The action immediately preceding this observation.

    kind is 'start' (no action has been taken yet), 'move' (a disc was
    placed on the board), or 'pass' (the previous player had no legal
    move and passed). square is the move square 0..63 when kind is
    'move', and None when kind is 'start' or 'pass'.

    The acting colour is not stored: it is the opponent of
    observation.player for 'move' and 'pass', and undefined for 'start'.
    """

    kind: Literal['start', 'move', 'pass']
    square: int | None = None


@dataclass(frozen=True)
class Observation:
    """Everything a bot needs to choose an action.

    board: immutable 64-cell tuple from rig.engine (row-major, 0..63).
    player: the colour to move (rig.engine.BLACK or rig.engine.WHITE).
    legal_moves: tuple of legal move squares in ascending order; empty
        when the player has no legal move and must pass.
    previous_action: the action that produced this position.
    """

    board: Board
    player: int
    legal_moves: tuple[int, ...]
    previous_action: PreviousAction
