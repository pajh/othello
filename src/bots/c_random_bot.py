"""Random C bot: drives the compiled ``c/bot.c`` over pipes for one game.

This is a thin adapter, not an implementation. Every decision is made inside
the C process: this module only translates one rig observation into the
CodinGame ordinary-mode text protocol, writes it to the child's stdin, and
translates the returned coordinate back into a rig square. The C source is the
single file that gets submitted to CodinGame; this module exists so the
existing rig can play it locally.

Process lifetime
----------------
The child is started **lazily**, on the first move this seat actually makes,
so a game where this seat never moves costs no process. It then stays alive for
the rest of that game: one child per seat per game, never one per move. Its
seed is drawn once from the runner's per-seat seeded ``rng``, which makes a
local run reproducible in the way the rest of the rig is.

A player is closed and reaped when it is released. The runner and the CLI build
the two seat players per game and drop them afterwards, so the ordinary
``create_player`` path relies on garbage collection to end the child; :meth:`close`
also runs from a finalizer for the same reason. Nothing here holds a reference
back to the bot module, so the player is not part of a reference cycle and
cleanup does not depend on the cyclic collector.

Scope: this bot has no state beyond its child process. There is no
configuration, retry, resume, watchdog or subprocess framework here.
"""

import random
import subprocess
from pathlib import Path

from rig import engine
from rig.types import Observation

# ===================================================================
# SETTINGS — bot identity. Edit these constants, then increment VERSION
# by one per completed saved edit revision of this file (not per
# keystroke). The ID is what run reports and metadata display. It names
# this file's code version, not the C program's own version, which it
# prints on stderr at startup.
# ===================================================================
VERSION = '001'
BOTNAME = 'C-RAND'
ID = f'{BOTNAME}-{VERSION}'
# ===================================================================

#: Executable built by ``make bot``, resolved from the repository root rather
#: than the working directory so the bot works from anywhere.
_EXECUTABLE = (Path(__file__).resolve().parents[2] / 'build' / 'c-random-bot')

_SIZE = 8

#: Rig cell values translated to the protocol's board characters. The engine
#: uses 0/1/-1; CodinGame sends '.'/'0'/'1'.
_CELL_CHARS = {engine.EMPTY: '.', engine.BLACK: '0', engine.WHITE: '1'}

#: Rig square -> coordinate string, and back. Column first, then row, with a1
#: the top-left square: square = row * 8 + column. This mirrors the mapping in
#: c/bot.c; see docs/c-random-bot.md, which records that it is unconfirmed
#: against the official statement.
_ALPHABET = 'abcdefgh'


def square_to_coord(square: int) -> str:
    """Return the coordinate for a rig square, e.g. 19 -> ``'d3'``."""
    return _ALPHABET[square % _SIZE] + str(square // _SIZE + 1)


def coord_to_square(coord: str) -> int | None:
    """Return the rig square for a coordinate, or None if it is malformed."""
    if len(coord) != 2 or coord[0] not in _ALPHABET or coord[1] not in '12345678':
        return None
    column = _ALPHABET.index(coord[0])
    row = int(coord[1]) - 1
    return row * _SIZE + column


def get_id() -> str:
    """Return this bot's ID, e.g. ``C-RAND-001``.

    The calling convention for every bot: run tooling reads the ID from the
    module so a report or metadata record says which bot produced a game,
    independent of the module path it was imported under.
    """
    return ID


class _CProcessPlayer:
    """One seat's C child process for one game.

    Not shared between seats or games: a runner must create one per seat per
    game, exactly as for any stateful bot. All state is the child process and
    the seeded value it was started with.
    """

    def __init__(self):
        self._process = None
        self._player_id = None
        # Kept so close() is idempotent and __del__ cannot raise during
        # interpreter shutdown.
        self._closed = False

    # -- child process ------------------------------------------------
    def _ensure_started(self, observation, rng):
        """Start the child on first use and send the one-time header."""
        if self._process is not None:
            return
        if not _EXECUTABLE.is_file():
            raise RuntimeError(
                'C bot executable not found at %s: build it first with '
                '"make bot" from the repository root' % _EXECUTABLE
            )
        # The C program prints its ID and seed on stderr; keep stderr on this
        # process's stderr so those diagnostics stay visible in a batch log.
        self._process = subprocess.Popen(
            [str(_EXECUTABLE), str(rng.getrandbits(63))],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            bufsize=1,
            cwd=str(_EXECUTABLE.parent),
        )
        self._player_id = 0 if observation.player == engine.BLACK else 1
        self._write('%d\n%d\n' % (self._player_id, _SIZE))

    def _write(self, text):
        """Write one turn's input, raising if the child has gone away."""
        stdin = self._process.stdin
        if stdin is None:
            raise RuntimeError('C bot process has no stdin pipe')
        try:
            stdin.write(text)
            stdin.flush()
        except (BrokenPipeError, ValueError) as exc:
            raise RuntimeError('C bot process stopped accepting input: %s' % exc) from exc

    def _read_move(self):
        """Return the coordinate the child printed, or None at end of output."""
        stdout = self._process.stdout
        if stdout is None:
            raise RuntimeError('C bot process has no stdout pipe')
        line = stdout.readline()
        if not line:
            return None
        return line.strip()

    # -- bot interface ------------------------------------------------
    def play(self, observation: Observation, *, rng: random.Random) -> int | None:
        """Return this seat's move for *observation*.

        The engine's own legal moves are authoritative: this method sends them
        to the child as the protocol's action list, expects one of them back,
        and refuses anything else rather than letting the engine record a
        forfeit. A position with no legal move is a forced pass, answered
        locally with None and no input sent, because the child is never asked
        to move when it cannot.
        """
        if not observation.legal_moves:
            return None
        self._ensure_started(observation, rng)
        rows = []
        for row in range(_SIZE):
            cells = observation.board[row * _SIZE:(row + 1) * _SIZE]
            rows.append(''.join(_CELL_CHARS[cell] for cell in cells))
        moves = [square_to_coord(square) for square in observation.legal_moves]
        self._write('%s\n%d\n%s\n'
                    % ('\n'.join(rows), len(moves), ' '.join(moves)))

        coord = self._read_move()
        if coord is None:
            raise RuntimeError('C bot closed its output before choosing a move')
        square = coord_to_square(coord)
        if square is None:
            raise RuntimeError(
                'C bot answered %r, which is not a coordinate' % coord)
        if square not in observation.legal_moves:
            raise RuntimeError(
                'C bot answered %s (square %d), which is not one of the legal '
                'moves %s' % (coord, square, moves))
        return square

    # -- cleanup ------------------------------------------------------
    def close(self):
        """Close the child's pipes and reap it. Safe to call more than once."""
        if self._closed:
            return
        self._closed = True
        process = self._process
        self._process = None
        if process is None:
            return
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass
        # Closing stdin is the child's EOF signal, so wait() returns promptly
        # instead of blocking on a process still waiting for input.
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass

    def __del__(self):
        # Reached when the runner drops the seat player at the end of a game,
        # including when the game ended on the opponent's move. Errors are
        # swallowed because an interpreter shutting down may already have
        # closed the pipes.
        try:
            self.close()
        except Exception:
            pass


def create_player():
    """Return a fresh callable that plays one seat of one game via C.

    The returned object keeps its own child process, so the runner must call
    this once per seat per game. Nothing is started here: the child begins on
    the first actual move.
    """
    return _CProcessPlayer().play


def play(observation: Observation, *, rng: random.Random) -> int | None:
    """Play one move with a temporary C process, closed immediately after.

    This exists only for direct legacy calls that use the module-level
    stateless form. It starts and reaps a process per call, which is
    wasteful and slower than :func:`create_player`; the runner and the CLI use
    the factory instead, so the normal path keeps one child per game.
    """
    player = _CProcessPlayer()
    try:
        return player.play(observation, rng=rng)
    finally:
        player.close()
