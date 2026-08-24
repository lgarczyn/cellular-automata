// Giant echo rung without gmp.h: declare the stable mpz ABI directly and
// link against libgmp.so.10. Flash at k=40, read echoes up to lag 10,590,737.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

typedef uint64_t mp_limb_t;
typedef struct { int _mp_alloc; int _mp_size; mp_limb_t *_mp_d; } __mpz_struct;
typedef __mpz_struct mpz_t[1];
typedef unsigned long mp_bitcnt_t;
extern void __gmpz_init(mpz_t);
extern void __gmpz_set_ui(mpz_t, unsigned long);
extern void __gmpz_mul_ui(mpz_t, const mpz_t, unsigned long);
extern void __gmpz_add_ui(mpz_t, const mpz_t, unsigned long);
extern void __gmpz_mul_2exp(mpz_t, const mpz_t, mp_bitcnt_t);
extern void __gmpz_tdiv_q_2exp(mpz_t, const mpz_t, mp_bitcnt_t);
extern void __gmpz_tdiv_q(mpz_t, const mpz_t, const mpz_t);
extern void __gmpz_ui_pow_ui(mpz_t, unsigned long, unsigned long);
extern mp_bitcnt_t __gmpz_scan1(const mpz_t, mp_bitcnt_t);
extern void __gmpz_setbit(mpz_t, mp_bitcnt_t);

static inline int bl64(uint64_t x){ return x ? 64-__builtin_clzll(x) : 0; }

static long bits_of(mpz_t x){
    int s = x[0]._mp_size;
    if (s <= 0) return 0;
    return (long)(s-1)*64 + bl64(x[0]._mp_d[s-1]);
}

static int lead_run48(mpz_t x){
    int s = x[0]._mp_size;
    if (s < 2) return 0;
    unsigned __int128 top = ((unsigned __int128)x[0]._mp_d[s-1] << 64)
                          | x[0]._mp_d[s-2];
    int tb = bl64(x[0]._mp_d[s-1]) + 64;      // bits used in `top`
    uint64_t w48 = (uint64_t)(top >> (tb - 48));
    int first = (int)((w48 >> 46) & 1);        // bit after the MSB
    int c = 0;
    for (int i = 46; i >= 0; i--){
        if ((int)((w48 >> i) & 1) != first) break;
        c++;
    }
    return c;
}

int main(int argc, char **argv){
    long BIG = argc > 1 ? atol(argv[1]) : 10590737;
    const long K = 40;
    const long M[] = {12, 53, 665, 15601, 111202, 190537, 10590737, 0};
    const long T = K + BIG + 4;
    const long THICK = (long)(0.43 * T) + 20000;
    mpz_t n, three_k;
    __gmpz_init(n); __gmpz_init(three_k);
    __gmpz_ui_pow_ui(three_k, 3, K);
    __gmpz_set_ui(n, 1);
    __gmpz_mul_2exp(n, n, THICK);
    __gmpz_tdiv_q(n, n, three_k);
    __gmpz_setbit(n, 0);
    fprintf(stderr, "seed %ld bits, %ld steps\n", bits_of(n), T);
    time_t t0 = time(0);
    for (long r = 1; r <= T; r++){
        __gmpz_mul_ui(n, n, 3);
        __gmpz_add_ui(n, n, 1);
        mp_bitcnt_t v = __gmpz_scan1(n, 0);
        __gmpz_tdiv_q_2exp(n, n, v);
        for (int i = 0; M[i]; i++)
            if (r == K + M[i] && M[i] <= BIG)
                printf("echo at k+%-9ld depth %d bits  (tape now %ld bits)\n",
                       M[i], lead_run48(n), bits_of(n));
        if (r % 1000000 == 0)
            fprintf(stderr, "step %ldM, %ld bits, %lds\n",
                    r/1000000, bits_of(n), (long)(time(0)-t0));
        if (bits_of(n) < 64){ fprintf(stderr, "died at %ld\n", r); return 1; }
    }
    fprintf(stderr, "done in %lds\n", (long)(time(0)-t0));
    return 0;
}
