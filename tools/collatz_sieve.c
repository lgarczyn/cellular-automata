/* Two ways of drawing each Collatz trajectory only once.
 *
 *   sieve      walk upward; draw n if nothing already drawn passed through it,
 *              then consume every value on n's trajectory. Enforces the rule in
 *              one direction only: draw 7 and 22, 11, 34 are out, but 9 can
 *              still be drawn later even though 7 lies on its trajectory.
 *
 *   antichain  the strict version: no drawn number lies on any other drawn
 *              number's trajectory, in either direction. Scanned downward,
 *              because scanning upward would draw 1 first and 1 is on
 *              everyone's trajectory.
 *
 * Writes a bitset of the drawn numbers. Usage:
 *   collatz_sieve sieve|antichain N out.bin
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define GET(a, i) ((a[(i) >> 6] >> ((i) & 63)) & 1ULL)
#define SET(a, i) (a[(i) >> 6] |= 1ULL << ((i) & 63))

int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "usage: %s sieve|antichain N out.bin\n", argv[0]); return 1; }
    int strict = strcmp(argv[1], "antichain") == 0;
    uint64_t N = strtoull(argv[2], NULL, 10), words = (N + 64) / 64;

    uint64_t *used = calloc(words, 8), *shown = calloc(words, 8);
    if (!used || !shown) { fprintf(stderr, "out of memory\n"); return 1; }

    uint64_t drawn = 0;
    for (uint64_t i = 1; i <= N; i++) {
        uint64_t n = strict ? N + 1 - i : i;
        if (GET(used, n)) continue;                    /* downstream of a drawn number */

        if (strict) {                                  /* also reject upstream of one */
            uint64_t x = n;
            int clash = 0;
            while (x != 1) {
                x = (x & 1) ? 3 * x + 1 : x / 2;
                if (x <= N && GET(shown, x)) { clash = 1; break; }
            }
            if (clash) continue;
        }

        SET(shown, n);
        drawn++;
        uint64_t x = n;
        while (x != 1) {
            x = (x & 1) ? 3 * x + 1 : x / 2;
            if (x <= N) SET(used, x);
        }
    }

    fprintf(stderr, "%s: N=%llu drawn=%llu (%.4f%%)\n", argv[1],
            (unsigned long long)N, (unsigned long long)drawn, 100.0 * drawn / N);
    FILE *f = fopen(argv[3], "wb");
    if (!f) { perror("fopen"); return 1; }
    fwrite(shown, 8, words, f);
    fclose(f);
    return 0;
}
