/* ==========================================================================
 * Byte-equivalence smoke for the embedded model reconstruction.
 *
 * Loads the parameters from the embedded Z85 header through c/model_decode.h
 * and compares the reconstructed bytes against an existing reference blob. The
 * question is only "are these the same 198,148 bytes", so the test uses memcmp
 * and no score tolerance at all: a changed weight must not be papered over by
 * a numeric threshold here.
 *
 *     build/test-nn-embedded REFERENCE_QUANTIZED_BLOB OUTPUT_BLOB
 *
 * On success the reconstructed blob is also written to OUTPUT_BLOB, byte for
 * byte, so the existing score comparison rig can be pointed at it.
 *
 * No setup() and no forward() here: reconstructing the parameters is this
 * stage's whole job, and scoring belongs to the existing comparison rig.
 * ========================================================================== */

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "model_decode.h"
#include "nn.h"

/* Little-endian IEEE754 binary32, as the generated header's byte order and the
 * codebook's floats both require. Checked from the four bytes of 1.0f, which is
 * 0x3F800000 stored least significant byte first as 00 00 80 3f. */
static int host_matches_payload_format(void)
{
    float one = 1.0f;
    unsigned char bytes[sizeof one];

    if (sizeof(float) != 4) {
        return 0;
    }
    memcpy(bytes, &one, sizeof one);
    return bytes[0] == 0x00u && bytes[1] == 0x00u
        && bytes[2] == 0x80u && bytes[3] == 0x3fu;
}

static int read_exact(const char *path, unsigned char **bytes, size_t expected)
{
    FILE *stream = fopen(path, "rb");
    unsigned char *buffer;

    if (stream == NULL) {
        fprintf(stderr, "cannot open reference blob %s\n", path);
        return 0;
    }
    buffer = (unsigned char *)malloc(expected);
    if (buffer == NULL) {
        fprintf(stderr, "could not allocate %lu reference bytes\n",
                (unsigned long)expected);
        fclose(stream);
        return 0;
    }
    if (fread(buffer, 1, expected, stream) != expected) {
        fprintf(stderr, "reference blob %s is short of %lu bytes\n", path,
                (unsigned long)expected);
        free(buffer);
        fclose(stream);
        return 0;
    }
    if (fread(buffer, 1, 1, stream) != 0) {
        fprintf(stderr, "reference blob %s has trailing bytes\n", path);
        free(buffer);
        fclose(stream);
        return 0;
    }
    fclose(stream);
    *bytes = buffer;
    return 1;
}

int main(int argc, char **argv)
{
    static Model model;
    unsigned char *payload = NULL;
    unsigned char *reference = NULL;
    uint32_t payload_crc;
    uint32_t decoded_crc;
    FILE *out;
    int identical;

    if (argc != 3) {
        fprintf(stderr, "usage: %s REFERENCE_QUANTIZED_BLOB OUTPUT_BLOB\n",
                argv[0]);
        return 2;
    }
    if (!host_matches_payload_format()) {
        fprintf(stderr, "this host is not little-endian IEEE754 binary32; the "
                        "codebook would be read wrongly\n");
        return 2;
    }
    if (!load_embedded_model(&model, &payload)) {
        return 2;
    }
    payload_crc = model_crc32(payload, MODEL_PAYLOAD_BYTES);
    decoded_crc = model_crc32((const unsigned char *)model.blob,
                              MODEL_DECODED_BYTES);

    if (!read_exact(argv[1], &reference, MODEL_DECODED_BYTES)) {
        free(payload);
        return 2;
    }

    identical = memcmp(model.blob, reference, MODEL_DECODED_BYTES) == 0;

    printf("reference blob: %s\n", argv[1]);
    printf("output blob:    %s\n", argv[2]);
    printf("codebook centers: %u\n", (unsigned)MODEL_CODEBOOK_COUNT);
    printf("parameters:     %u\n", (unsigned)MODEL_PARAMETER_COUNT);
    printf("payload bytes:  %u\n", (unsigned)MODEL_PAYLOAD_BYTES);
    printf("z85 chars:      %u (decoded, NUL excluded)\n",
           (unsigned)MODEL_Z85_LENGTH);
    printf("decoded bytes:  %u\n", (unsigned)MODEL_DECODED_BYTES);
    printf("payload CRC32:  actual 0x%08lx expected 0x%08lx\n",
           (unsigned long)payload_crc, (unsigned long)MODEL_PAYLOAD_CRC32);
    printf("decoded CRC32:  actual 0x%08lx expected 0x%08lx\n",
           (unsigned long)decoded_crc, (unsigned long)MODEL_DECODED_CRC32);

    if (identical) {
        out = fopen(argv[2], "wb");
        if (out == NULL) {
            fprintf(stderr, "cannot write %s\n", argv[2]);
            free(reference);
            free(payload);
            return 2;
        }
        if (fwrite(model.blob, 1, MODEL_DECODED_BYTES, out)
            != MODEL_DECODED_BYTES) {
            fprintf(stderr, "could not write all %u bytes to %s\n",
                    (unsigned)MODEL_DECODED_BYTES, argv[2]);
            fclose(out);
            free(reference);
            free(payload);
            return 2;
        }
        fclose(out);
        printf("wrote %u reconstructed bytes to %s\n",
               (unsigned)MODEL_DECODED_BYTES, argv[2]);
        printf("RESULT: PASS, reconstruction is byte identical to the "
               "reference\n");
    } else {
        printf("RESULT: FAIL, reconstruction differs from the reference\n");
    }

    free(reference);
    free(payload);
    return identical ? 0 : 1;
}
