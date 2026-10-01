/* ==========================================================================
 * Reconstruct model parameters from the embedded Base64 codebook payload.
 *
 * Header-only, standard C11 only. Includes c/nn.h for the Model type and the
 * generated runs/c-model-embedded/model.h for the payload: its lengths, its two
 * CRC32 checksums and the Base64 text itself.
 *
 * What it does
 * ------------
 * load_embedded_model() decodes model_base64 into one startup allocation,
 * checks the encoded and decoded lengths and the payload CRC32, then expands
 * the codebook and its uint8 indices into the model's parameter blob and checks
 * that reconstruction's CRC32. Both checksums are the standard IEEE CRC32 as
 * Python's zlib.crc32 computes it: polynomial 0xedb88320, initial and final
 * XOR 0xffffffff.
 *
 * The payload is the codebook first (1024 bytes = 256 little-endian float32
 * centers) and then the indices (49537 bytes, one per parameter, in original
 * order). There is no compression: the Base64 is decoded as written, padding
 * included, and MODEL_BASE64_LENGTH characters are read, excluding the NUL.
 *
 * Lifetime
 * --------
 * One call at startup, before setup(), which stays the caller's responsibility:
 * the loader allocates the packed payload and hands it back through
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

/* Standard Base64 alphabet. Returns the 6-bit value of a character, or -1 if
 * it is not part of the alphabet ('=' padding is handled by the caller). */
static inline int model_base64_value(char character)
{
    if (character >= 'A' && character <= 'Z') {
        return character - 'A';
    }
    if (character >= 'a' && character <= 'z') {
        return character - 'a' + 26;
    }
    if (character >= '0' && character <= '9') {
        return character - '0' + 52;
    }
    if (character == '+') {
        return 62;
    }
    if (character == '/') {
        return 63;
    }
    return -1;
}

/* Decode exactly MODEL_BASE64_LENGTH characters of model_base64 into
 * *out_bytes bytes. Returns 1 on success.
 *
 * Exactly three characters decode to two bytes, and one trailing '=' group
 * encodes a final single byte, which is how the standard padding works: any
 * other length is rejected rather than guessed at. */
static inline int model_base64_decode(const char *encoded, size_t encoded_length,
                                      unsigned char *out_bytes,
                                      size_t out_length)
{
    size_t i;
    size_t out = 0;

    if (encoded_length % 4u != 0u) {
        return 0;
    }
    for (i = 0; i < encoded_length; i += 4) {
        int value[4];
        int slot;
        size_t produced = 3;

        for (slot = 0; slot < 4; ++slot) {
            char character = encoded[i + (size_t)slot];
            if (character == '=') {
                /* Padding is only legal in the last group, and only as the
                 * final one or two characters. */
                if (i + 4u != encoded_length || slot < 2) {
                    return 0;
                }
                value[slot] = 0;
            } else {
                value[slot] = model_base64_value(character);
                if (value[slot] < 0) {
                    return 0;
                }
            }
        }
        /* Three bytes encode to four characters with no padding; two bytes
         * encode to three characters plus one '='; one byte encodes to two
         * characters plus '=='. So the first '=' position fixes the count. */
        if (encoded[i + 2] == '=') {
            produced = 1;
        } else if (encoded[i + 3] == '=') {
            produced = 2;
        }

        if (out + produced > out_length) {
            return 0;
        }
        if (produced >= 1) {
            out_bytes[out] = (unsigned char)((value[0] << 2) | (value[1] >> 4));
            out += 1;
        }
        if (produced >= 2) {
            out_bytes[out] = (unsigned char)((value[1] << 4) | (value[2] >> 2));
            out += 1;
        }
        if (produced >= 3) {
            out_bytes[out] = (unsigned char)((value[2] << 6) | value[3]);
            out += 1;
        }
    }
    return out == out_length;
}

/* Load the embedded payload into *model* and return 1, or return 0 after
 * explaining the problem on stderr.
 *
 * *payload_storage receives the packed bytes, which the caller owns from then
 * on: a bot keeps it for the process lifetime, a test frees it. Both CRCs and
 * both lengths are checked before the parameters are written, so a model is
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
    if (MODEL_BASE64_LENGTH % 4u != 0u) {
        fprintf(stderr, "model_decode: Base64 length %u is not a multiple of 4\n",
                (unsigned)MODEL_BASE64_LENGTH);
        return 0;
    }

    packed = (unsigned char *)malloc(MODEL_PAYLOAD_BYTES);
    if (packed == NULL) {
        fprintf(stderr, "model_decode: could not allocate %u payload bytes\n",
                (unsigned)MODEL_PAYLOAD_BYTES);
        return 0;
    }
    if (!model_base64_decode(model_base64, MODEL_BASE64_LENGTH, packed,
                             MODEL_PAYLOAD_BYTES)) {
        fprintf(stderr, "model_decode: Base64 text does not decode to %u bytes\n",
                (unsigned)MODEL_PAYLOAD_BYTES);
        free(packed);
        return 0;
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
