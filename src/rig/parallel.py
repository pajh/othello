"""Spawned worker processes for multi-core batch collection (T009).

Bounded by the local-execution section of docs/parallel-and-github-design.md.
This module only runs games on worker processes and hands finished records
back to ``rig.cli``; the parent still creates the run directory, writes
``metadata.json``, is the only writer of ``games.jsonl`` and owns the tally,
progress and summary. Nothing here loads a model in the parent, edits bot
code or SETTINGS, retries, reschedules or resumes.

Process model
-------------
A standard-library :class:`~concurrent.futures.ProcessPoolExecutor` with an
explicit ``spawn`` context. The worker initializer limits CPU thread use and
imports each requested bot module **once** per process, so a learned bot holds
one read-only model copy per worker for the whole batch. The thread limits are
applied in this order, which is why the imports below are inside the
initializer:

1. ``OMP_NUM_THREADS`` and ``MKL_NUM_THREADS`` are set as environment variables
   before any bot module, and so before any numerical library, is imported in
   this process;
2. the bot modules are imported, which is what loads an NN checkpoint;
3. torch intra-op and inter-op threads are pinned to 1, only if one of those
   imports brought torch into this process.

PyTorch is an optional extra, so a collection of dependency-free bots must not
require it: the initializer never imports torch itself, it only reads what the
bot imports already placed in ``sys.modules``. A bot that needs torch and
cannot import it still fails loudly in the initializer.

Game identity
-------------
Every task carries the **global** game index, the master seed, both module
names, the colour mode and the shared run ID. Per-game seeds still come from
``rig.cli._derive_seed`` over ``{master seed}:{global index}:{bot id}`` and
colours still come from the global index, so a game is identical whatever
worker number runs it and whatever order results arrive in.

Bounded window
--------------
At most ``2 * workers`` tasks are outstanding at a time and records are
delivered to the caller in global-index order, waiting for the next index
when it is not ready. The whole collection is never held in memory, and no
sorting stage exists, so ``games.jsonl`` stays compatible with the existing
converter and helpers.

Failures
--------
An ordinary bot failure is still a forfeit record produced by
``rig.runner``. A worker or setup failure raises in the parent and stops the
batch visibly through the existing failed/interrupted summary; outstanding
futures are cancelled and the pool is shut down without waiting, so records
already written are kept.
"""

import multiprocessing
import os
import sys
from concurrent.futures import ProcessPoolExecutor

#: Bots loaded by the worker initializer, keyed by bot ID 1 and 2. This is
#: the only per-process state, and it is never shared or mutated during play.
_WORKER_BOTS = {}

#: Environment variables pinned before the bot modules (and so torch) are
#: imported in a worker. One inference thread per worker is deliberate.
_THREAD_ENVIRONMENT = ('OMP_NUM_THREADS', 'MKL_NUM_THREADS')


def _worker_init(bot1_module, bot2_module):
    """Limit CPU threads, load both bot modules once, then pin torch if used.

    Runs once per worker process, before that worker's first task. Import
    failures raise here, which the pool reports to the parent as a setup
    failure rather than as a game forfeit.

    The order matters and is deliberate:

    1. ``OMP_NUM_THREADS`` and ``MKL_NUM_THREADS`` are set before any bot
       module, and so before any numerical library, is imported here;
    2. the bot modules are imported once each through the existing
       ``rig.cli._load_bot``, which is what loads an NN checkpoint;
    3. only then are torch's own intra/inter-op threads pinned to 1, and only
       if one of those imports actually brought torch into this process.

    PyTorch is an optional extra, not a core dependency, so a random- or
    max-bot collection must work in a core-only install: torch is never
    imported here on that path. It is not imported speculatively to find out
    whether it is installed, because importing it to test for it would
    reintroduce the dependency, and no broad ``ImportError`` handling is used
    that could swallow a genuinely missing dependency inside ``nn_bot``: a
    bot that needs torch and cannot import it still fails loudly here.

    Pinning after the bot import is early enough. Loading a checkpoint builds
    no inference and runs no candidate forward pass, so the first inference
    happens in this worker's first task, after these limits are set.
    """
    for name in _THREAD_ENVIRONMENT:
        os.environ[name] = '1'

    # Imported here, not at module scope, so that this module stays importable
    # without importing torch and so that rig.cli, which imports this module,
    # is fully loaded before the worker uses its helpers.
    from rig.cli import _load_bot

    _WORKER_BOTS[1] = _load_bot(bot1_module)
    _WORKER_BOTS[2] = _load_bot(bot2_module)

    # Read rather than import: whatever torch is in sys.modules arrived as part
    # of the bot imports above, or is already present because this process
    # imported it earlier.
    torch = sys.modules.get('torch')
    if torch is not None:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)


def _worker_bot_ids():
    """Return this worker's ``(bot1_id, bot2_id)``.

    The parent uses these for startup output and ``metadata.json`` so it does
    not import a bot module (and so does not load an extra NN) to learn the
    display IDs.
    """
    return (_WORKER_BOTS[1]['id'], _WORKER_BOTS[2]['id'])


def _worker_play_game(task):
    """Play one complete game in this worker and return ``(index, record)``.

    The task is the plain tuple
    ``(game_index, run_id, master_seed, bot1_module, bot2_module, force_start)``.
    One task is one game: fresh per-seat players from the existing
    ``create_player`` factories, the existing runner and the existing record
    builder. Nothing about the worker number reaches the game.
    """
    index, run_id, master_seed, bot1_module, bot2_module, force_start = task
    from rig.cli import _play_one_game

    record = _play_one_game(
        index, run_id, master_seed, bot1_module, bot2_module, force_start,
        _WORKER_BOTS,
    )
    return record['game_index'], record


def _task(args, run_id, index):
    """Return the picklable task tuple for global game *index*."""
    return (index, run_id, args.seed, args.bot1, args.bot2, args.force_start)


def effective_workers(workers, games):
    """Return the worker count actually used for *games* games.

    ``workers == 1`` means the sequential path in ``rig.cli`` and never spawns
    a process. More workers than games would only idle, so the pool is capped
    at the game count and the effective number is what metadata and summaries
    report.
    """
    if workers == 1:
        return 1
    return max(1, min(workers, games))


def run_batch(args, run_id, on_ids, on_record):
    """Play the batch on spawned workers and deliver records in index order.

    *on_ids* is called once as ``on_ids(bot1_id, bot2_id)`` with IDs reported
    by the workers, before the first game starts. *on_record* is called once
    per finished record as ``on_record(record)``, in global game-index order,
    as records are written by the parent. Returns the number of records
    delivered.

    Raises whatever a worker raises (a worker or setup failure) or
    ``RuntimeError`` if a worker answers with an unexpected game index.
    """
    workers = effective_workers(args.workers, args.games)
    window = 2 * workers
    pending = {}
    context = multiprocessing.get_context('spawn')
    executor = ProcessPoolExecutor(
        max_workers=workers,
        mp_context=context,
        initializer=_worker_init,
        initargs=(args.bot1, args.bot2),
    )
    try:
        # One cheap task per worker: every process has run its initializer by
        # the time these return, so the IDs are already known before any game
        # starts and no parent-side model load is needed.
        probes = [executor.submit(_worker_bot_ids) for _ in range(workers)]
        bot1_id, bot2_id = probes[0].result()
        on_ids(bot1_id, bot2_id)

        submitted = 0
        delivered = 0
        while delivered < args.games:
            while submitted < args.games and len(pending) < window:
                pending[submitted] = executor.submit(
                    _worker_play_game, _task(args, run_id, submitted)
                )
                submitted += 1
            index, record = pending.pop(delivered).result()
            if index != delivered:
                raise RuntimeError(
                    'worker returned game %d where game %d was expected'
                    % (index, delivered)
                )
            on_record(record)
            delivered += 1
        return delivered
    finally:
        for future in pending.values():
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
