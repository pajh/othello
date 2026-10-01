/* ==========================================================================
 * C-versus-reference comparison rig for c/nn.h.
 *
 * Loads an exported parameter blob straight into Model.blob, reads a CSV of
 * 128 input values plus a reference score per row, runs forward() on each row
 * and reports how far the C result is from the reference.
 *
 * This is a local development tool, not part of a submission. It assumes a
 * little-endian IEEE754 32-bit float host and checks that once at startup
 * rather than converting anything.
 *
 *     build/test-nn-compare MODEL_BIN REFERENCE_CSV
 *
 * The blob must be exactly MODEL_BLOB_SIZE float32 values with no header,
 * padding or trailing bytes. The CSV's first line is the header (x000..x127,
 * score) and each later line is one row; CRLF line endings are accepted.
 *
 * Acceptance is fixed: abs(C - reference) <= 1e-5 + 1e-5 * abs(reference),
 * for every row, with every value finite and in [0, 1]. The tolerance is not
 * loosened here and the arithmetic is not adjusted to force agreement; a FAIL
 * is a finding to investigate, not something to argue away.
 * ========================================================================== */

#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nn.h"

#define LINE_CAPACITY 8192
#define FIELDS_PER_ROW (MODEL_INPUT_SIZE + 1)
#define ABSOLUTE_TOLERANCE 1e-5
#define RELATIVE_TOLERANCE 1e-5

/* One model and one scratch line, both static: the rig must not allocate per
 * row, and a static Model keeps the sanitizer's leak report about setup()'s
 * four activation buffers only. */
static Model model;
static char line[LINE_CAPACITY];
static fp32 inputs[MODEL_INPUT_SIZE];

static void release_model(void)
{
    int layer;

    /* The first layer's input is owned outright. Every later layer's input is
     * the previous layer's output and must not be freed. */
    free(model.layers[0].input);
    for (layer = 0; layer < (int)MODEL_LAYER_COUNT; ++layer) {
        free(model.layers[layer].output);
    }
}

/* Little-endian byte order and IEEE754 binary32 both show up in the four bytes
 * of 1.0f, which is 0x3F800000 stored least significant byte first as
 * 00 00 80 3f. A host that disagrees would read the blob wrongly, so the rig
 * refuses to run rather than reporting nonsense. */
static int host_matches_blob_format(void)
{
    fp32 one = 1.0f;
    unsigned char bytes[sizeof one];

    if (sizeof(fp32) != 4) {
        return 0;
    }
    memcpy(bytes, &one, sizeof one);
    return bytes[0] == 0x00u && bytes[1] == 0x00u
        && bytes[2] == 0x80u && bytes[3] == 0x3fu;
}

static int load_blob(const char *path)
{
    FILE *stream = fopen(path, "rb");
    size_t read;
    unsigned char extra;

    if (stream == NULL) {
        fprintf(stderr, "cannot open blob %s\n", path);
        return 0;
    }
    read = fread(model.blob, sizeof(fp32), MODEL_BLOB_SIZE, stream);
    if (read != MODEL_BLOB_SIZE) {
        fprintf(stderr, "blob %s is short: read %lu of %lu float32 values\n",
                path, (unsigned long)read, (unsigned long)MODEL_BLOB_SIZE);
        fclose(stream);
        return 0;
    }
    if (fread(&extra, 1, 1, stream) != 0) {
        fprintf(stderr, "blob %s has trailing bytes after %lu float32 values\n",
                path, (unsigned long)MODEL_BLOB_SIZE);
        fclose(stream);
        return 0;
    }
    fclose(stream);
    return 1;
}

/* Parse one CSV row into *inputs and *reference. Returns 0 and explains the
 * problem, naming the 1-based data row, on any malformed line. */
static int parse_row(char *text, fp32 *row_inputs, fp32 *reference,
                     unsigned long row_number)
{
    char *cursor = text;
    size_t field;

    for (field = 0; field < FIELDS_PER_ROW; ++field) {
        char *end;
        fp32 value = strtof(cursor, &end);

        if (end == cursor) {
            fprintf(stderr, "row %lu: field %lu is not a number\n",
                    row_number, (unsigned long)field);
            return 0;
        }
        if (field < MODEL_INPUT_SIZE) {
            row_inputs[field] = value;
            if (!isfinite(value)) {
                fprintf(stderr, "row %lu: input %lu is not finite\n",
                        row_number, (unsigned long)field);
                return 0;
            }
        } else {
            *reference = value;
            if (!isfinite(value)) {
                fprintf(stderr, "row %lu: reference score is not finite\n",
                        row_number);
                return 0;
            }
            if (value < 0.0f || value > 1.0f) {
                fprintf(stderr, "row %lu: reference score %g is outside [0, 1]\n",
                        row_number, (double)value);
                return 0;
            }
            /* Nothing but line ending may follow the last field. */
            cursor = end;
            while (*cursor == '\r' || *cursor == '\n'
                   || *cursor == ' ' || *cursor == '\t') {
                ++cursor;
            }
            if (*cursor != '\0') {
                fprintf(stderr, "row %lu: extra data after the reference score\n",
                        row_number);
                return 0;
            }
        }
        if (field + 1 < FIELDS_PER_ROW) {
            if (*end != ',') {
                fprintf(stderr, "row %lu: expected a comma after field %lu\n",
                        row_number, (unsigned long)field);
                return 0;
            }
            cursor = end + 1;
        }
    }
    return 1;
}

int main(int argc, char **argv)
{
    FILE *csv;
    unsigned long row_number = 0;
    unsigned long compared = 0;
    unsigned long outside = 0;
    unsigned long nonfinite = 0;
    double total_absolute_error = 0.0;
    double worst_error = 0.0;
    fp32 worst_c = 0.0f;
    fp32 worst_reference = 0.0f;
    unsigned long worst_row = 0;
    int saw_header = 0;

    if (argc != 3) {
        fprintf(stderr, "usage: %s MODEL_BIN REFERENCE_CSV\n", argv[0]);
        return 2;
    }
    if (!host_matches_blob_format()) {
        fprintf(stderr, "this host is not little-endian IEEE754 binary32; "
                        "the blob would be read wrongly\n");
        return 2;
    }
    if (!load_blob(argv[1])) {
        return 2;
    }
    /* After the blob is in place: setup() fills descriptors and buffers and
     * deliberately leaves the parameters alone. */
    setup(&model);

    csv = fopen(argv[2], "r");
    if (csv == NULL) {
        fprintf(stderr, "cannot open reference CSV %s\n", argv[2]);
        release_model();
        return 2;
    }

    while (fgets(line, (int)sizeof line, csv) != NULL) {
        fp32 reference;
        fp32 score;
        double error;
        double tolerance;

        if (!saw_header) {
            /* Skip the x000..x127,score header line. */
            saw_header = 1;
            continue;
        }
        if (line[0] == '\n' || line[0] == '\r' || line[0] == '\0') {
            continue; /* tolerate a blank line between rows */
        }
        row_number += 1;
        if (!parse_row(line, inputs, &reference, row_number)) {
            fclose(csv);
            release_model();
            return 2;
        }

        score = forward(inputs, &model);
        if (!isfinite(score)) {
            nonfinite += 1;
            printf("row %lu: C score is not finite\n", row_number);
            continue;
        }
        if (score < 0.0f || score > 1.0f) {
            printf("row %lu: C score %g is outside [0, 1]\n",
                   row_number, (double)score);
            continue;
        }

        error = fabs((double)score - (double)reference);
        tolerance = ABSOLUTE_TOLERANCE + RELATIVE_TOLERANCE * fabs((double)reference);
        compared += 1;
        total_absolute_error += error;
        if (error > worst_error) {
            worst_error = error;
            worst_row = row_number;
            worst_c = score;
            worst_reference = reference;
        }
        if (error > tolerance) {
            outside += 1;
            if (outside <= 5) {
                printf("row %lu: C %g vs reference %g, difference %g exceeds %g\n",
                       row_number, (double)score, (double)reference, error,
                       tolerance);
            }
        }
    }
    fclose(csv);

    printf("C blob:        %s (%d float32 values, %d bytes)\n", argv[1],
           (int)MODEL_BLOB_SIZE, (int)(MODEL_BLOB_SIZE * sizeof(fp32)));
    printf("reference CSV: %s\n", argv[2]);
    printf("rows read:     %lu\n", row_number);
    printf("rows compared: %lu\n", compared);
    printf("tolerance:     abs(C - reference) <= %g + %g * abs(reference)\n",
           ABSOLUTE_TOLERANCE, RELATIVE_TOLERANCE);
    if (compared > 0) {
        printf("mean absolute error: %.9g\n",
               total_absolute_error / (double)compared);
    } else {
        printf("mean absolute error: not measured, no rows compared\n");
    }
    printf("max absolute error:  %.9g\n", worst_error);
    if (worst_row != 0) {
        printf("worst row:          %lu (C %.9g, reference %.9g)\n",
               worst_row, (double)worst_c, (double)worst_reference);
    } else {
        printf("worst row:          none\n");
    }
    printf("outside tolerance:  %lu\n", outside);
    printf("nonfinite or range: %lu\n", nonfinite);

    if (compared == 0) {
        printf("RESULT: FAIL, no rows were compared\n");
    } else if (outside != 0 || nonfinite != 0) {
        printf("RESULT: FAIL, %lu row(s) outside tolerance, %lu nonfinite\n",
               outside, nonfinite);
    } else {
        printf("RESULT: PASS, all %lu row(s) within tolerance\n", compared);
    }

    release_model();
    return (compared > 0 && outside == 0 && nonfinite == 0) ? 0 : 1;
}
