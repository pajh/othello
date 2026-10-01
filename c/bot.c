/* ==========================================================================
 * CodinGame multiplayer Othello bot — greedy embedded neural network.
 *
 * SETTINGS / VERSION 003. Every supplied legal move is applied to the current
 * board, the resulting position is encoded from this seat's perspective and
 * scored by the embedded network, and the highest score is played. Greedy from
 * the very first move: no random opening, no sampling, no search, and no
 * legal-move generator, because the platform supplies every legal move.
 *
 * Version history: 001 played a random legal move; 002 removed the routine
 * per-turn logging; 003 replaced random scoring with the embedded network.
 *
 * Ordinary mode only (no EXPERT input). Input contract, per turn:
 *
 *   once at start:   playerID   0 = Black, 1 = White
 *                    boardSize  8
 *   every turn:      boardSize row strings, top row first
 *                      '.' = empty, '0' = Black, '1' = White
 *                    actionCount
 *                    actionCount coordinate strings, e.g. "d3"
 *
 * Output is exactly ONE coordinate string plus a newline, then flushed. No
 * extra text ever goes to stdout. EOF on stdin ends the program normally.
 * Forced passes are the platform's business: the wrapper never sends a turn
 * with no legal moves, and if actionCount is 0 anyway this loop simply waits
 * for the next board rather than inventing a move.
 *
 * stdout carries moves and nothing else. stderr carries error messages only, so
 * a local run is not spammed one line per move.
 *
 * The quoted includes below are the whole local dependency list, in the order
 * the single-file submission needs them. scripts/scrunch.py pastes each one at
 * its directive and removes the quoted includes inside the pasted headers, so
 * nothing here is ever opened twice in the assembled file. For a normal local
 * build the compiler resolves them and the header guards make that harmless.
 *
 * Build (see Makefile):  make bot
 * Direct:               cc -std=c11 -O2 -Wall -Wextra -I runs/c-model-embedded \\
 *                           -o build/c-random-bot c/bot.c -lm
 *
 * Standard C11 plus the C standard library and libm. No threads, no platform
 * headers, no other source file.
 * ========================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nn.h"
#include "model.h"
#include "model_decode.h"

/* ------------------------------- SETTINGS -------------------------------- */
/* Bot identity for local runs and reports. Increment on each completed
 * revision of this file, as with the Python bots. */
#define VERSION "003"
#define BOTNAME "C-NN"

/* Maximum board size this bot can hold. 8 is the Othello board; the constant
 * exists so the buffers below are fixed size and nothing is allocated. */
#define MAX_BOARD_SIZE 8
#define BOARD_CELLS (MAX_BOARD_SIZE * MAX_BOARD_SIZE)

/* Longest coordinate string we accept, e.g. "d3" plus terminator. */
#define MAX_COORD_LEN 16

/* Longest board row we accept, plus terminator. */
#define MAX_ROW_LEN (MAX_BOARD_SIZE + 2)

/* Board characters as the platform sends them. */
#define CELL_EMPTY '.'
#define CELL_BLACK '0'
#define CELL_WHITE '1'

/* The two planes of the model input: own discs then opponent discs. */
#define INPUT_CELLS (BOARD_CELLS * 2)

/* ------------------------------- state ----------------------------------- */
/* One model for the whole session, loaded and set up once at startup. The
 * packed payload is retained for the process lifetime and never freed; there is
 * no per-move allocation anywhere. */
static Model model;
static unsigned char *payload_storage = NULL;

/* Board cells as characters, row-major, plus scratch boards for evaluating
 * candidates. `board` is never modified while candidates are scored. */
static char board[BOARD_CELLS];
static char candidate_board[BOARD_CELLS];
static fp32 model_input[INPUT_CELLS];

/* ---------------------------- coordinate mapping ------------------------- */
/*
 * COORDINATE CONVENTION — VERIFY BEFORE SUBMITTING.
 *
 * This bot assumes a1 is the top-left square and reads a coordinate as
 * column first then row, so square index = row * board_size + column. The
 * official CodinGame Othello statement could not be loaded while this file was
 * written (the page renders its statement with JavaScript), so this mapping is
 * unconfirmed against the referee.
 *
 * If the statement or a referee log shows rank 1 on the BOTTOM row instead,
 * change square_index_to_coord() and coord_to_square_index() to use
 * board_size - 1 - row. Those two functions are the only places this
 * convention appears.
 */

/* Return the coordinate string for `square`, e.g. 19 -> "d3". */
static void square_index_to_coord(int square, int board_size, char *out)
{
    int row = square / board_size;
    int col = square % board_size;
    out[0] = (char)('a' + col);
    out[1] = (char)('1' + row);
    out[2] = '\0';
}

/* Return the square index for a coordinate, or -1 if it is malformed. */
static int coord_to_square_index(const char *coord, int board_size)
{
    int col;
    int row;

    if (coord == NULL || coord[0] == '\0' || coord[1] == '\0' || coord[2] != '\0') {
        return -1;
    }
    if (coord[0] < 'a' || coord[0] >= 'a' + board_size) {
        return -1;
    }
    if (coord[1] < '1' || coord[1] >= '1' + board_size) {
        return -1;
    }
    col = coord[0] - 'a';
    row = coord[1] - '1';
    return row * board_size + col;
}

/* --------------------------- candidate moves ----------------------------- */

/* Eight directions as (row delta, column delta). */
static const int DIRECTIONS[8][2] = {
    {-1, -1}, {-1, 0}, {-1, 1},
    {0, -1},           {0, 1},
    {1, -1},  {1, 0},  {1, 1}
};

/* Write the board that results from `actor` playing `square`, following the
 * engine's rules: a run of opponent discs is flipped only when it ends at an
 * actor disc, in any of the eight directions. The source board is not touched.
 *
 * Returns 1 when the move was applicable. The platform only supplies legal
 * moves, so 0 means the input disagreed with the rules and is reported. */
static int apply_candidate(const char *source, int square, int board_size,
                           char actor, char opponent, char *out)
{
    int dr;
    int dc;

    memcpy(out, source, BOARD_CELLS);
    if (out[square] != CELL_EMPTY) {
        return 0;
    }
    out[square] = actor;

    for (dr = 0; dr < 8; ++dr) {
        for (dc = 0; dc < 8; ++dc) {
            const int *direction = DIRECTIONS[dr];
            int row = square / board_size + direction[0];
            int col = square % board_size + direction[1];
            int run_length = 0;

            /* Walk while the ray stays on the board over opponent discs. */
            while (row >= 0 && row < board_size && col >= 0 && col < board_size
                   && out[row * board_size + col] == opponent) {
                ++run_length;
                row += direction[0];
                col += direction[1];
            }
            /* Flip only a bounded run: the ray must end on an actor disc. */
            if (run_length > 0 && row >= 0 && row < board_size
                && col >= 0 && col < board_size
                && out[row * board_size + col] == actor) {
                int step;
                row = square / board_size + direction[0];
                col = square % board_size + direction[1];
                for (step = 0; step < run_length; ++step) {
                    out[row * board_size + col] = actor;
                    row += direction[0];
                    col += direction[1];
                }
            }
        }
    }
    return 1;
}

/* Fill model_input with the after-action position from the actor's point of
 * view: own discs first, then the opponent's, both row-major, 1.0 for a disc
 * and 0.0 for an empty square. No absolute-colour channel and no scaling. */
static void encode_position(const char *position, char actor, char opponent)
{
    int square;

    for (square = 0; square < BOARD_CELLS; ++square) {
        fp32 own = position[square] == actor ? 1.0f : 0.0f;
        fp32 other = position[square] == opponent ? 1.0f : 0.0f;
        model_input[square] = own;
        model_input[BOARD_CELLS + square] = other;
    }
}

/* ---------------------------- score() ------------------------------------ */
/*
 * Expected-outcome score for one supplied legal move, in [0, 1].
 *
 * The board is copied, `actor` is placed at the move's square, bounded runs of
 * opponent discs are flipped, the result is encoded from the actor's
 * perspective and scored by the network. Every candidate is built from the same
 * untouched board, so no evaluation can see another's changes.
 *
 * Ties are the caller's business: it keeps the first strictly highest score,
 * which is the earliest supplied move among equals.
 */
static fp32 score(const char *current, const char *coord, int board_size,
                  char actor, char opponent)
{
    int square = coord_to_square_index(coord, board_size);

    if (square < 0) {
        return -1.0f;
    }
    if (!apply_candidate(current, square, board_size, actor, opponent,
                         candidate_board)) {
        return -1.0f;
    }
    encode_position(candidate_board, actor, opponent);
    return forward(model_input, &model);
}

/* ------------------------------ input helpers ---------------------------- */

/* Read one whitespace-delimited token into `buffer`, of any line layout.
 * Returns 1 on success, 0 at end of input. CodinGame sends one value per line
 * for this protocol; scanning whitespace rather than lines also tolerates a
 * referee that packs several values onto one line, and blank lines or trailing
 * whitespace cannot be mistaken for a value. */
static int read_value(char *buffer, size_t size)
{
    char format[16];

    if (size < 2 || size > 99) {
        return 0;
    }
    /* "%<width-1>s" reads at most one terminator's worth less than the
     * buffer, so the result always fits and is always NUL terminated. */
    snprintf(format, sizeof format, "%%%zus", size - 1);
    return scanf(format, buffer) == 1;
}

/* ------------------------------- main ------------------------------------ */

int main(int argc, char **argv)
{
    char buffer[MAX_ROW_LEN];
    char moves[BOARD_CELLS][MAX_COORD_LEN];
    char best[MAX_COORD_LEN];
    int player_id = -1;
    int board_size = 0;
    int action_count = 0;
    int i;
    int turn = 0;
    char actor;
    char opponent;

    /* The local wrapper still passes a seed argument. Greedy play needs no RNG,
     * so it is accepted and ignored. */
    (void)argc;
    (void)argv;

    /* Load the embedded parameters and set up the activation buffers, once,
     * before any move is read. load_embedded_model() verifies both CRC32s and
     * setup() must follow it, since setup() fills descriptors and buffers
     * without touching the parameters. */
    if (!load_embedded_model(&model, &payload_storage)) {
        fprintf(stderr, "could not load the embedded model\n");
        return 1;
    }
    setup(&model);

    /* Initial input: player ID and board size, once. */
    if (!read_value(buffer, sizeof buffer)) {
        return 0; /* EOF before the game started: nothing to do. */
    }
    player_id = atoi(buffer);
    if (!read_value(buffer, sizeof buffer)) {
        return 0;
    }
    board_size = atoi(buffer);
    if (board_size < 1 || board_size > MAX_BOARD_SIZE) {
        fprintf(stderr, "unsupported board size %d\n", board_size);
        return 1;
    }
    actor = (player_id == 0) ? CELL_BLACK : CELL_WHITE;
    opponent = (player_id == 0) ? CELL_WHITE : CELL_BLACK;

    /* Turn loop. Each iteration consumes one board plus its legal moves and,
     * when there is at least one, writes exactly one coordinate. */
    for (;;) {
        fp32 best_score = -1.0f;
        int have_best = 0;

        /* Board rows, top to bottom, kept for this turn's candidates. */
        for (i = 0; i < board_size; ++i) {
            int col;
            if (!read_value(buffer, sizeof buffer)) {
                return 0; /* EOF: the game ended normally. */
            }
            for (col = 0; col < board_size; ++col) {
                char cell = buffer[col];
                if (cell != CELL_EMPTY && cell != CELL_BLACK && cell != CELL_WHITE) {
                    fprintf(stderr, "unknown board character '%c'\n", cell);
                    return 1;
                }
                board[i * board_size + col] = cell;
            }
        }

        if (!read_value(buffer, sizeof buffer)) {
            return 0;
        }
        action_count = atoi(buffer);
        if (action_count < 0 || action_count > BOARD_CELLS) {
            fprintf(stderr, "bad action count %d\n", action_count);
            return 1;
        }

        for (i = 0; i < action_count; ++i) {
            if (!read_value(moves[i], sizeof moves[i])) {
                return 0;
            }
        }

        if (action_count == 0) {
            /* No legal move: the platform drives passes itself, so wait for
             * the next board instead of printing a move. */
            ++turn;
            continue;
        }

        /* Highest score wins; strictly greater keeps the earliest of any tie. */
        for (i = 0; i < action_count; ++i) {
            fp32 candidate = score(board, moves[i], board_size, actor, opponent);
            if (candidate < 0.0f) {
                fprintf(stderr, "turn %d: could not score %s\n", turn, moves[i]);
                return 1;
            }
            if (!have_best || candidate > best_score) {
                best_score = candidate;
                strcpy(best, moves[i]);
                have_best = 1;
            }
        }

        if (!have_best) {
            return 1;
        }

        /* The platform expects one of the strings it supplied, so play the move
         * verbatim. This only cross-checks that the coordinate round-trips
         * through our square numbering. */
        {
            int square = coord_to_square_index(best, board_size);
            if (square < 0) {
                fprintf(stderr, "turn %d: unreadable move %s\n", turn, best);
                return 1;
            }
            square_index_to_coord(square, board_size, buffer);
        }

        printf("%s\n", best);
        fflush(stdout);
        ++turn;
    }
}
