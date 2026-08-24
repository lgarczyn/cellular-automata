/* Compute total stopping times (iterations to reach 1) for n = 1..N.
 * Writes N uint16 values (n = 1 first) to the file given as argv[2].
 * Usage: collatz_steps N out.bin
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char **argv) {
    if (argc != 3) { fprintf(stderr, "usage: %s N out.bin\n", argv[0]); return 1; }
    uint64_t N = strtoull(argv[1], NULL, 10);

    uint16_t *steps = malloc((N + 1) * sizeof(uint16_t));
    if (!steps) { fprintf(stderr, "out of memory\n"); return 1; }
    steps[1] = 0;

    for (uint64_t n = 2; n <= N; n++) {
        uint64_t x = n;
        uint32_t c = 0;
        /* Walk until the trajectory drops below n, where the answer is cached. */
        while (x >= n) {
            x = (x & 1) ? 3 * x + 1 : x / 2;
            c++;
        }
        steps[n] = (uint16_t)(c + steps[x]);
    }

    FILE *f = fopen(argv[2], "wb");
    if (!f) { perror("fopen"); return 1; }
    fwrite(steps + 1, sizeof(uint16_t), N, f);
    fclose(f);
    free(steps);
    return 0;
}
