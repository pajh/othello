/* ==========================================================================
 * Reconstruct model parameters from the embedded Z85 codebook payload.
 *
 * Header-only, standard C11 only. Includes c/nn.h for the Model type and the
 * generated runs/c-model-embedded/model.h for the payload: its lengths, its two
 * CRC32 checksums and the Z85 text itself.
 *
 * What it does
 * ------------
 * load_embedded_model() decodes model_z85 into one startup allocation, checks
 * the encoded length, the true/padded payload sizes, that the known trailing
 * padding bytes are zero and the payload CRC32, then expands the codebook and
 * its uint8 indices into the model's parameter blob and checks that
 * reconstruction's CRC32. Both checksums are the standard IEEE CRC32 as
 * Python's zlib.crc32 computes it: polynomial 0xedb88320, initial and final
 * XOR 0xffffffff.
 *
 * The true payload is the codebook first (1024 bytes = 256 little-endian
 * float32 centers) and then the indices (49537 bytes, one per parameter, in
 * original order): 50561 bytes. Three zero bytes are appended to reach the
 * multiple of 4 that Z85 needs. The payload CRC32 is over the 50561 true
 * bytes, not the padding. There is no compression: the Z85 text is decoded as
 * written and the known padding is discarded after being checked.
 *
 * Lifetime
 * --------
 * One call at startup, before setup(), which stays the caller's responsibility:
 * the loader allocates the padded payload and hands it back through
 * *payload_storage so production code can retain it for the process lifetime.
 * There is no teardown function here, and no per-parameter allocation: the
 * packed buffer is the only allocation, made once. A test can free what it
 * received; nothing in this file assumes ownership of it.
 *
 * The expansion uses memcpy throughout, so no cast of a byte pointer to float
 * ever happens and nothing depends on alignment or aliasing rules.
 * ========================================================================== */

#ifndef MODEL_DECODE_H
#define MODEL_DECODE_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nn.h"
#include "model.h"

/* CRC32 (IEEE) as zlib.crc32 computes it. Bytewise on purpose: this is the
 * submission's reference implementation, and it must agree with the checksum
 * Python wrote into model.h rather than with any library. */
#define MODEL_CRC32_POLYNOMIAL 0xedb88320u

static inline uint32_t model_crc32(const unsigned char *data, size_t length)
{
    uint32_t crc = 0xffffffffu;
    size_t i;
    int bit;

    for (i = 0; i < length; ++i) {
        crc ^= (uint32_t)data[i];
        for (bit = 0; bit < 8; ++bit) {
            if ((crc & 1u) != 0u) {
                crc = (crc >> 1) ^ MODEL_CRC32_POLYNOMIAL;
            } else {
                crc >>= 1;
            }
        }
    }
    return crc ^ 0xffffffffu;
}

/* The exact standard Z85 alphabet (zeroMQ RFC 32). Returns the 0..84 value of
 * a character, or -1 if it is not part of the alphabet. */
static inline int model_z85_value(char character)
{
    static const char alphabet[86] =
        "0123456789"
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        ".-:+=^!/*?&<>()[]{}@%$#";
    int index;

    for (index = 0; index < 85; ++index) {
        if (alphabet[index] == character) {
            return index;
        }
    }
    return -1;
}

/* Decode exactly MODEL_Z85_LENGTH characters of model_z85 into *out_bytes
 * bytes, where out_length is the padded length (a multiple of 4). Returns 1 on
 * success.
 *
 * Each group of five characters is one big-endian 32-bit value written base 85
 * most significant first. The accumulator is a uint32_t and is rejected as
 * soon as it would exceed 0xffffffff / 85, which also guarantees no group can
 * silently wrap and be accepted. Padding is not part of Z85 text: the decoder
 * produces exactly the padded byte count and the caller then checks that only
 * the known trailing MODEL_PAYLOAD_PADDED_BYTES - MODEL_PAYLOAD_BYTES bytes are
 * zero. */
static inline int model_z85_decode(const char *encoded, size_t encoded_length,
                                   unsigned char *out_bytes,
                                   size_t out_length)
{
    size_t i;
    size_t out = 0;

    if (encoded_length % 5u != 0u) {
        return 0;
    }
    for (i = 0; i < encoded_length; i += 5) {
        uint32_t value = 0;
        int slot;

        for (slot = 0; slot < 5; ++slot) {
            int digit = model_z85_value(encoded[i + (size_t)slot]);
            if (digit < 0) {
                return 0;
            }
            /* Reject before multiplying so no invalid group can wrap around. */
            if (value > (UINT32_C(0xffffffff) / 85u)) {
                return 0;
            }
            value = value * 85u + (uint32_t)digit;
        }
        if (out + 4u > out_length) {
            return 0;
        }
        out_bytes[out] = (unsigned char)(value >> 24);
        out_bytes[out + 1] = (unsigned char)(value >> 16);
        out_bytes[out + 2] = (unsigned char)(value >> 8);
        out_bytes[out + 3] = (unsigned char)value;
        out += 4;
    }
    return out == out_length;
}

/* Load the embedded payload into *model* and return 1, or return 0 after
 * explaining the problem on stderr.
 *
 * *payload_storage receives the padded bytes, which the caller owns from then
 * on: a bot keeps it for the process lifetime, a test frees it. Both CRCs and
 * the lengths are checked before the parameters are written, so a model is
 * never left half-populated by a corrupt payload. */
static inline int load_embedded_model(Model *model, unsigned char **payload_storage)
{
    unsigned char *packed;
    uint32_t payload_crc;
    uint32_t decoded_crc;
    size_t index;

    if (model == NULL || payload_storage == NULL) {
        fprintf(stderr, "model_decode: null argument\n");
        return 0;
    }
    if (MODEL_Z85_LENGTH % 5u != 0u) {
        fprintf(stderr, "model_decode: Z85 length %u is not a multiple of 5\n",
                (unsigned)MODEL_Z85_LENGTH);
        return 0;
    }
    if (MODEL_PAYLOAD_PADDED_BYTES % 4u != 0u) {
        fprintf(stderr, "model_decode: padded payload %u is not a multiple of 4\n",
                (unsigned)MODEL_PAYLOAD_PADDED_BYTES);
        return 0;
    }
    if (MODEL_PAYLOAD_PADDED_BYTES - MODEL_PAYLOAD_BYTES
        > MODEL_PAYLOAD_PADDED_BYTES) {
        fprintf(stderr, "model_decode: inconsistent payload/padded lengths\n");
        return 0;
    }

    packed = (unsigned char *)malloc(MODEL_PAYLOAD_PADDED_BYTES);
    if (packed == NULL) {
        fprintf(stderr, "model_decode: could not allocate %u payload bytes\n",
                (unsigned)MODEL_PAYLOAD_PADDED_BYTES);
        return 0;
    }
    if (!model_z85_decode(model_z85, MODEL_Z85_LENGTH, packed,
                          MODEL_PAYLOAD_PADDED_BYTES)) {
        fprintf(stderr, "model_decode: Z85 text does not decode to %u bytes\n",
                (unsigned)MODEL_PAYLOAD_PADDED_BYTES);
        free(packed);
        return 0;
    }

    /* Check the known trailing padding is exactly zero before trusting the
     * true payload that precedes it. */
    for (index = MODEL_PAYLOAD_BYTES; index < MODEL_PAYLOAD_PADDED_BYTES;
         ++index) {
        if (packed[index] != 0u) {
            fprintf(stderr, "model_decode: padding byte %lu is %u, expected 0\n",
                    (unsigned long)index, (unsigned)packed[index]);
            free(packed);
            return 0;
        }
    }

    payload_crc = model_crc32(packed, MODEL_PAYLOAD_BYTES);
    if (payload_crc != MODEL_PAYLOAD_CRC32) {
        fprintf(stderr, "model_decode: payload CRC32 is 0x%08lx, expected 0x%08lx\n",
                (unsigned long)payload_crc, (unsigned long)MODEL_PAYLOAD_CRC32);
        free(packed);
        return 0;
    }

    /* Expand: codebook first, then one center per index, in order. Each
     * center is copied with memcpy, so no byte pointer is ever cast to float. */
    for (index = 0; index < MODEL_PARAMETER_COUNT; ++index) {
        size_t center = (size_t)packed[MODEL_CODEBOOK_COUNT * 4u + index];
        fp32 value;

        if (center >= MODEL_CODEBOOK_COUNT) {
            fprintf(stderr, "model_decode: index %lu is %lu, outside the %lu centers\n",
                    (unsigned long)index, (unsigned long)center,
                    (unsigned long)MODEL_CODEBOOK_COUNT);
            free(packed);
            return 0;
        }
        memcpy(&value, packed + center * 4u, sizeof value);
        memcpy(&model->blob[index], &value, sizeof value);
    }

    decoded_crc = model_crc32((const unsigned char *)model->blob,
                              MODEL_DECODED_BYTES);
    if (decoded_crc != MODEL_DECODED_CRC32) {
        fprintf(stderr, "model_decode: reconstructed CRC32 is 0x%08lx, expected 0x%08lx\n",
                (unsigned long)decoded_crc, (unsigned long)MODEL_DECODED_CRC32);
        free(packed);
        return 0;
    }

    *payload_storage = packed;
    return 1;
}

#endif /* MODEL_DECODE_H */
