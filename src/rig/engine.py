"""Othello rules engine: immutable board operations.

Board representation
--------------------
- A ``Board`` is an immutable ``tuple`` of 64 ``int`` cells.
- Square numbering is row-major: ``square = row * 8 + column``, with 0 at the
  top-left corner and 63 at the bottom-right.
- Cell values: ``EMPTY`` (0), ``BLACK`` (1), ``WHITE`` (-1).
- Initial position: White at squares 27 and 36; Black at squares 28 and 35.

All public functions validate their inputs and raise ``ValueError`` on
invalid boards, players, or moves.  Booleans are rejected wherever an ``int``
is expected.  No function mutates its inputs.
"""

from typing import Tuple

EMPTY = 0
BLACK = 1
WHITE = -1

Board = Tuple[int, ...]

_SIZE = 8
_CELLS = _SIZE * _SIZE

# Eight directions as (row_delta, col_delta).
_DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def _validate_board(board):
    """Raise ValueError unless *board* is a tuple of 64 valid cell ints."""
    if not isinstance(board, tuple):
        raise ValueError("board must be a tuple")
    if len(board) != _CELLS:
        raise ValueError("board must have exactly %d cells" % _CELLS)
    for cell in board:
        if isinstance(cell, bool) or not isinstance(cell, int):
            raise ValueError("board cells must be ints (bools rejected)")
        if cell not in (EMPTY, BLACK, WHITE):
            raise ValueError("board cells must be EMPTY, BLACK, or WHITE")


def _validate_player(player):
    """Raise ValueError unless *player* is BLACK or WHITE (bools rejected)."""
    if isinstance(player, bool) or not isinstance(player, int):
        raise ValueError("player must be an int (bools rejected)")
    if player not in (BLACK, WHITE):
        raise ValueError("player must be BLACK or WHITE")


def initial_board():
    """Return the standard initial board as an immutable tuple."""
    board = [EMPTY] * _CELLS
    board[27] = WHITE
    board[36] = WHITE
    board[28] = BLACK
    board[35] = BLACK
    return tuple(board)


def _captures_in_direction(board, player, square, dr, dc):
    """Return a list of opponent squares flipped from *square* in direction
    (dr, dc).  Returns an empty list when the ray is not a valid capture
    (hits an empty square, the board edge, or no opponent discs)."""
    row, col = divmod(square, _SIZE)
    row += dr
    col += dc
    captured = []
    while 0 <= row < _SIZE and 0 <= col < _SIZE:
        cell = board[row * _SIZE + col]
        if cell == EMPTY:
            return []
        if cell == player:
            return captured
        captured.append(row * _SIZE + col)
        row += dr
        col += dc
    return []


def legal_moves(board, player):
    """Return a tuple of legal move squares in ascending order.

    A move is legal when the square is empty and placing a disc there captures
    at least one opponent disc in any of the eight directions.
    """
    _validate_board(board)
    _validate_player(player)
    moves = []
    for square in range(_CELLS):
        if board[square] != EMPTY:
            continue
        for dr, dc in _DIRECTIONS:
            if _captures_in_direction(board, player, square, dr, dc):
                moves.append(square)
                break
    return tuple(moves)


def apply_move(board, player, move):
    """Return a new board after *player* places a disc at *move*.

    *move* may be ``None`` only when the player has no legal moves (forced
    pass); in that case the board is returned unchanged.

    Raises ``ValueError`` for invalid boards, players, or moves (out-of-range,
    occupied, non-capturing, or illegal passes).  The input board is never
    mutated.
    """
    _validate_board(board)
    _validate_player(player)
    legal = legal_moves(board, player)
    if move is None:
        if legal:
            raise ValueError(
                "pass is only allowed when the player has no legal moves"
            )
        return board
    if isinstance(move, bool) or not isinstance(move, int):
        raise ValueError("move must be an int or None (bools rejected)")
    if not 0 <= move < _CELLS:
        raise ValueError("move out of range")
    if move not in legal:
        raise ValueError("illegal move")
    new_board = list(board)
    new_board[move] = player
    for dr, dc in _DIRECTIONS:
        for sq in _captures_in_direction(board, player, move, dr, dc):
            new_board[sq] = player
    return tuple(new_board)


def is_terminal(board):
    """Return True when neither player has any legal move."""
    _validate_board(board)
    return not legal_moves(board, BLACK) and not legal_moves(board, WHITE)


def disc_counts(board):
    """Return ``(black_count, white_count)``."""
    _validate_board(board)
    black = sum(1 for c in board if c == BLACK)
    white = sum(1 for c in board if c == WHITE)
    return (black, white)


def winner(board):
    """Return ``BLACK``, ``WHITE``, or ``EMPTY`` (draw) for a terminal board.

    Raises ``ValueError`` if the board is not terminal.
    """
    _validate_board(board)
    if not is_terminal(board):
        raise ValueError("winner is only defined for terminal boards")
    black, white = disc_counts(board)
    if black > white:
        return BLACK
    if white > black:
        return WHITE
    return EMPTY
