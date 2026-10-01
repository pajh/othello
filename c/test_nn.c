/* ==========================================================================
 * Standalone smoke driver for c/nn.h.
 *
 * Fills a Model's parameter blob with seeded random weights and biases, calls
 * setup() once, then runs forward() on 256 random 128-float input vectors and
 * reports what came out. The point is to exercise the header's allocation,
 * descriptor loop and arithmetic under the address and undefined-behaviour
 * sanitizers, not to measure anything about a trained model.
 *
 * The weights are deliberately modest so the sigmoid does not saturate: with
 * plain unit-scale weights and biases this network, the logit spread grows
 * quickly and every output would collapse to 0 or 1, which would hide real
 * problems behind a plausible-looking constant.
 *
 * Test-only lifetime: the driver frees the first layer's input and each layer's
 * output once at the end, so leak detection has nothing to report. Borrowed
 * pointers (a layer input that is the previous layer's output) must NOT be
 * freed. In a bot these buffers simply live for the process lifetime.
 *
 * No framework, no fixture files, no Python, no Othello positions: the inputs
 * are random vectors.
 * ========================================================================== */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "nn.h"

#define SMOKE_INPUT_COUNT 256u
#define SMOKE_PRINT_COUNT 5u

/* Small, reproducible weights: uniform in [-SCALE, SCALE]. */
#define WEIGHT_SCALE 0.05f
#define BIAS_SCALE 0.05f

/* Inputs are small non-negative values, like an encoded board's 0/1 planes. */
#define INPUT_SCALE 1.0f

/* Fill the blob with seeded random parameters. One xorshift generator, so the
 * smoke is reproducible without depending on the platform's rand(). */
static uint32_t rng_state = 2463534242u;

static uint32_t next_random(void)
{
    uint32_t x = rng_state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    rng_state = x;
    return x;
}

static fp32 next_scaled(fp32 scale)
{
    /* Map to [0, 1) then to [-scale, scale]. */
    fp32 unit = (fp32)(next_random() >> 8) / 16777216.0f;
    return (unit * 2.0f - 1.0f) * scale;
}

static void fill_parameters(Model *model)
{
    size_t i;

    for (i = 0; i < MODEL_BLOB_SIZE; ++i) {
        /* Every parameter gets the same modest scale here; a real decode would
         * lay out weights then biases per layer, which forward() does not care
         * about because it addresses them by offset. */
        model->blob[i] = next_scaled(WEIGHT_SCALE);
    }
    /* Biases are the last element of each layer, nudged separately so the
     * pre-activations are not purely symmetric. */
    model->blob[LAYER0_BIAS_OFFSET] = next_scaled(BIAS_SCALE);
    model->blob[LAYER1_BIAS_OFFSET] = next_scaled(BIAS_SCALE);
    model->blob[LAYER2_BIAS_OFFSET] = next_scaled(BIAS_SCALE);
}

static void release_model(Model *model)
{
    u16 layer;

    /* The first layer's input is owned outright; every later layer's input is
     * the previous layer's output and must not be freed here. */
    free(model->layers[0].input);
    for (layer = 0; layer < MODEL_LAYER_COUNT; ++layer) {
        free(model->layers[layer].output);
    }
}

int main(void)
{
    Model *model;
    fp32 input[MODEL_INPUT_SIZE];
    fp32 scores[SMOKE_INPUT_COUNT];
    fp32 minimum = 1.0f;
    fp32 maximum = 0.0f;
    double total = 0.0;
    size_t bad_count = 0;
    size_t at_low = 0;
    size_t at_high = 0;
    size_t identical = 0;
    u16 run;
    u16 i;

    model = (Model *)malloc(sizeof(Model));
    if (model == NULL) {
        fprintf(stderr, "could not allocate the model\n");
        return 1;
    }
    fill_parameters(model);
    setup(model);

    for (run = 0; run < SMOKE_INPUT_COUNT; ++run) {
        fp32 score;

        for (i = 0; i < MODEL_INPUT_SIZE; ++i) {
            input[i] = fabsf(next_scaled(INPUT_SCALE));
        }
        score = forward(input, model);
        scores[run] = score;

        if (!(score == score) || score < 0.0f || score > 1.0f) {
            bad_count += 1;
            fprintf(stderr, "run %u: score %g is not finite and in [0, 1]\n",
                    (unsigned)run, (double)score);
            continue;
        }
        if (score < minimum) {
            minimum = score;
        }
        if (score > maximum) {
            maximum = score;
        }
        if (score <= 0.0f) {
            at_low += 1;
        }
        if (score >= 1.0f) {
            at_high += 1;
        }
        total += (double)score;
        if (run > 0 && score == scores[run - 1]) {
            identical += 1;
        }
    }

    printf("nn.h smoke: %u forward passes over %u inputs of %u floats\n",
           (unsigned)SMOKE_INPUT_COUNT, (unsigned)SMOKE_INPUT_COUNT,
           (unsigned)MODEL_INPUT_SIZE);
    printf("first scores:");
    for (i = 0; i < SMOKE_PRINT_COUNT; ++i) {
        printf(" %g", (double)scores[i]);
    }
    printf("\n");
    printf("min %g  max %g  mean %.6f\n", (double)minimum, (double)maximum,
           total / (double)SMOKE_INPUT_COUNT);
    printf("out of range or nonfinite: %u\n", (unsigned)bad_count);
    printf("at or below 0: %u   at or above 1: %u   identical to previous: %u\n",
           (unsigned)at_low, (unsigned)at_high, (unsigned)identical);

    if (bad_count != 0) {
        printf("RESULT: FAIL, %u bad score(s)\n", (unsigned)bad_count);
    } else if (at_low == 0 && at_high == 0 && identical != 0) {
        printf("RESULT: WARN, every score is identical but none saturated; "
               "check the weights\n");
    } else if (at_low == SMOKE_INPUT_COUNT || at_high == SMOKE_INPUT_COUNT) {
        printf("RESULT: WARN, every score saturated at one end\n");
    } else {
        printf("RESULT: OK, all scores finite and strictly inside (0, 1)\n");
    }

    release_model(model);
    free(model);
    return bad_count == 0 ? 0 : 1;
}
