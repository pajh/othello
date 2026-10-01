/* ==========================================================================
 * Header-only float32 multilayer perceptron for the Othello outcome model.
 *
 * Self-contained C11. Include this file in exactly one translation unit per
 * program; everything is static inline, so there is no separate object to
 * build and no dependency on any other project file.
 *
 * Contract
 * --------
 * The model is a plain sequence of dense layers. A Layer points into one
 * contiguous parameter array (a Model's `blob`) at two offsets measured in
 * FLOAT ELEMENTS, not bytes:
 *
 *     weights_offset: the first of output_size * input_size weights, laid out
 *                     row-major with one row per OUTPUT NEURON and one column
 *                     per input, which is PyTorch's nn.Linear layout;
 *     bias_offset:    the layer's output_size biases.
 *
 * For the current model (128 -> 256 -> 64 -> 1, ReLU, ReLU, sigmoid, 49,537
 * parameters) the blob order is weight0, bias0, weight1, bias1, weight2,
 * bias2, and the offsets are fixed by the defines below.
 *
 * Model setup and lifetime
 * ------------------------
 * Call setup() exactly once per Model before the first forward(). It fills the
 * layer descriptors and allocates the activation buffers once: the first
 * layer's input, and one output buffer per layer. Later layers borrow the
 * previous layer's output as their input, so no rewiring is needed or wanted.
 * setup() does not initialize, overwrite or otherwise touch blob values; the
 * program fills or decodes the parameters itself.
 *
 * The buffers live for the process lifetime: there is no teardown function,
 * because a bot uses one model for its whole session. forward() performs no
 * allocation, no freeing and no pointer rewiring, so it can be called as often
 * as needed, including once per move.
 *
 * The layer loop is driven by the descriptors, so a different width or depth
 * only needs different defines and descriptors, not different forward code.
 * Those descriptors are hardcoded here on purpose: no exporter or code
 * generator exists yet.
 * ========================================================================== */

#ifndef NN_H
#define NN_H

#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* ------------------------------- types ----------------------------------- */

typedef float fp32;
typedef uint16_t u16;

/* -------------------------- current architecture ------------------------- */

#define MODEL_INPUT_SIZE 128
#define MODEL_LAYER_COUNT 3
#define MODEL_BLOB_SIZE 49537

/* Hidden widths of the current network, used by setup()'s descriptors. */
#define MODEL_HIDDEN_1 256
#define MODEL_HIDDEN_2 64

/* Float-element offsets into blob, in weight/bias order per layer:
 * 128*256 = 32768 weights then 256 biases; 256*64 = 16384 weights then 64
 * biases; then 64 weights and 1 bias. */
#define LAYER0_WEIGHTS_OFFSET 0u
#define LAYER0_BIAS_OFFSET 32768u
#define LAYER1_WEIGHTS_OFFSET 33024u
#define LAYER1_BIAS_OFFSET 49408u
#define LAYER2_WEIGHTS_OFFSET 49472u
#define LAYER2_BIAS_OFFSET 49536u

/* Activation applied to a layer's pre-activation result. */
typedef enum {
    ACT_LINEAR,
    ACT_RELU,
    ACT_SIGMOID
} Activation;

/* One dense layer. `input` and `output` are the activation buffers owned by the
 * Model; sizes and offsets come from the descriptors. */
typedef struct {
    u16 input_size;
    u16 output_size;
    fp32 *input;
    fp32 *output;
    size_t weights_offset;
    size_t bias_offset;
    Activation activation;
} Layer;

/* A whole model: one parameter array plus one descriptor per dense layer. */
typedef struct {
    fp32 blob[MODEL_BLOB_SIZE];
    Layer layers[MODEL_LAYER_COUNT];
} Model;

/* -------------------------------- setup ---------------------------------- */

static inline void abort_with(const char *message)
{
    /* stderr is the only safe channel: in a bot, stdout carries moves. */
    fprintf(stderr, "nn.h: %s\n", message);
    abort();
}

/* Fill in the layer descriptors and allocate the activation buffers.
 *
 * Call once per Model. Allocation failure aborts: a bot cannot play without its
 * model, and there is nothing sensible to recover to.
 *
 * The first layer owns an input buffer of MODEL_INPUT_SIZE floats and is handed
 * the caller's values by forward(). Every layer owns an output buffer. Layer i
 * borrows layer i-1's output, so exactly MODEL_LAYER_COUNT + 1 buffers are
 * allocated and the chain is complete after one pass.
 */
static inline void setup(Model *model)
{
    fp32 *first_input;
    int layer;

    if (model == NULL) {
        abort_with("null model");
        return;
    }

    first_input = (fp32 *)malloc(sizeof(fp32) * MODEL_INPUT_SIZE);
    if (first_input == NULL) {
        abort_with("could not allocate the model input buffer");
        return;
    }

    model->layers[0].input_size = (u16)MODEL_INPUT_SIZE;
    model->layers[0].output_size = (u16)MODEL_HIDDEN_1;
    model->layers[0].input = first_input;
    model->layers[0].output = (fp32 *)malloc(sizeof(fp32) * MODEL_HIDDEN_1);
    model->layers[0].weights_offset = LAYER0_WEIGHTS_OFFSET;
    model->layers[0].bias_offset = LAYER0_BIAS_OFFSET;
    model->layers[0].activation = ACT_RELU;

    model->layers[1].input_size = (u16)MODEL_HIDDEN_1;
    model->layers[1].output_size = (u16)MODEL_HIDDEN_2;
    model->layers[1].input = model->layers[0].output;
    model->layers[1].output = (fp32 *)malloc(sizeof(fp32) * MODEL_HIDDEN_2);
    model->layers[1].weights_offset = LAYER1_WEIGHTS_OFFSET;
    model->layers[1].bias_offset = LAYER1_BIAS_OFFSET;
    model->layers[1].activation = ACT_RELU;

    model->layers[2].input_size = (u16)MODEL_HIDDEN_2;
    model->layers[2].output_size = 1u;
    model->layers[2].input = model->layers[1].output;
    model->layers[2].output = (fp32 *)malloc(sizeof(fp32) * 1u);
    model->layers[2].weights_offset = LAYER2_WEIGHTS_OFFSET;
    model->layers[2].bias_offset = LAYER2_BIAS_OFFSET;
    model->layers[2].activation = ACT_SIGMOID;

    for (layer = 0; layer < (int)MODEL_LAYER_COUNT; ++layer) {
        if (model->layers[layer].output == NULL) {
            abort_with("could not allocate a layer output buffer");
            return;
        }
    }
}

/* ------------------------------- forward --------------------------------- */

/* Apply one activation to one value. expf is used for the sigmoid; there is no
 * fast-math anywhere, so results stay comparable with a reference
 * implementation. */
static inline fp32 activate(Activation activation, fp32 value)
{
    switch (activation) {
    case ACT_RELU:
        return value > 0.0f ? value : 0.0f;
    case ACT_SIGMOID:
        return 1.0f / (1.0f + expf(-value));
    case ACT_LINEAR:
    default:
        return value;
    }
}

/* Score one MODEL_INPUT_SIZE-float vector and return the final layer's single
 * value.
 *
 * The caller keeps ownership of `input`; its values are copied into the model's
 * own first-layer buffer. Nothing is allocated, freed or rewired here, so this
 * is safe to call once per move.
 *
 * The loop is driven entirely by the descriptors, so the same code serves a
 * model with different widths or a different number of layers.
 */
static inline fp32 forward(const fp32 *input, Model *model)
{
    int layer;
    u16 i;

    for (i = 0; i < (u16)MODEL_INPUT_SIZE; ++i) {
        model->layers[0].input[i] = input[i];
    }

    for (layer = 0; layer < (int)MODEL_LAYER_COUNT; ++layer) {
        u16 input_size = model->layers[layer].input_size;
        u16 output_size = model->layers[layer].output_size;
        const fp32 *activations = model->layers[layer].input;
        const fp32 *weights = model->blob + model->layers[layer].weights_offset;
        const fp32 *bias = model->blob + model->layers[layer].bias_offset;

        /* One row of the weight matrix per output neuron, each row a dot
         * product of that neuron's inputs plus its bias. */
        for (i = 0; i < output_size; ++i) {
            const fp32 *row = weights + (size_t)i * (size_t)input_size;
            fp32 sum = bias[i];
            u16 j;
            for (j = 0; j < input_size; ++j) {
                sum += row[j] * activations[j];
            }
            model->layers[layer].output[i] =
                activate(model->layers[layer].activation, sum);
        }
    }

    return model->layers[MODEL_LAYER_COUNT - 1].output[0];
}

#endif /* NN_H */
