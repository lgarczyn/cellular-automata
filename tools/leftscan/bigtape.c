// bigtape.c: left-edge scanner for LARGE automata (1024+ bit tapes),
// direct-ABI libgmp. Four channels, bits-of-evidence scoring:
//   f: MSB front window (top 64 bits of each row)
//   t: base window: bits at fixed absolute positions [b0, b0+64) - the
//      band just past the start column (distinct from the front at scale)
//   c: time-columns of the base window (64-row chunks per bit position)
//   v: per-seed quasicrystal anomaly of the front (lags 2..64 + 306/359/665)
// usage:
//   bigtape calib <bits> <T> <N> <seed>
//   bigtape scan  <bits> <T> <N> <seed> <thf> <tht> <thc> <thv> <out>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

typedef uint64_t u64;
typedef uint32_t u32;
typedef struct { int _mp_alloc; int _mp_size; u64 *_mp_d; } __mpz_struct;
typedef __mpz_struct mpz_t[1];
typedef unsigned long mp_bitcnt_t;
extern void __gmpz_init2(mpz_t, mp_bitcnt_t);
extern void __gmpz_mul_ui(mpz_t, const mpz_t, unsigned long);
extern void __gmpz_add_ui(mpz_t, const mpz_t, unsigned long);
extern void __gmpz_tdiv_q_2exp(mpz_t, const mpz_t, mp_bitcnt_t);
extern mp_bitcnt_t __gmpz_scan1(const mpz_t, mp_bitcnt_t);
extern void __gmpz_import(mpz_t, size_t, int, size_t, int, size_t, const void*);
extern void __gmpz_setbit(mpz_t, mp_bitcnt_t);
extern char *__gmpz_get_str(char*, int, const mpz_t);
extern void __gmpz_set(mpz_t, const mpz_t);

static inline int bl64(u64 x){ return x ? 64-__builtin_clzll(x) : 0; }
static inline long bits_of(const mpz_t x){
    int s = x[0]._mp_size;
    return s <= 0 ? 0 : (long)(s-1)*64 + bl64(x[0]._mp_d[s-1]);
}
static inline u64 get64(const mpz_t x, long pos){ // bits [pos, pos+64)
    int s = x[0]._mp_size;
    long w = pos >> 6; int off = pos & 63;
    u64 lo = (w < s) ? x[0]._mp_d[w] : 0;
    u64 hi = (w+1 < s) ? x[0]._mp_d[w+1] : 0;
    return off ? (lo >> off) | (hi << (64-off)) : lo;
}
static inline int runlen(u64 t){ int c=0; while(t){ t &= t>>1; c++; } return c; }
static double LOG2W64;
static inline double rowscore64(u64 seg){
    int best = runlen(seg);
    int r0 = runlen(~seg);
    if (r0 > best) best = r0;
    for (int p=2; p<=8; p++){
        u64 mm = (p==0)?~0ULL:((~0ULL)>>p);
        u64 d = (seg ^ (seg>>p)) & mm;
        int z = runlen((~d)&mm);
        if (z > best) best = z;
    }
    return (double)best - LOG2W64;
}
static inline void top3(double *a, double v){
    if (v > a[0]){ a[2]=a[1]; a[1]=a[0]; a[0]=v; }
    else if (v > a[1]){ a[2]=a[1]; a[1]=v; }
    else if (v > a[2]) a[2]=v;
}
static inline double avg3(double *a){ return (a[0]+a[1]+a[2])/3.0; }

#define TCAP 4096
#define VC 4            // extra convergent lags
static double PRED[TCAP];
static const int XLAGS[VC] = {306, 359, 665, 1359};
static void mkpred(int T){
    double l23 = log2(3.0);
    for (int m=1; m<T && m<TCAP; m++){
        double fr = fmod(m*l23, 1.0);
        if (fr > 0.5) fr = 1.0-fr;
        PRED[m] = fr<=0 ? 32.0 : fmax(0.0, -log2(fr)-1.0);
        if (PRED[m] > 32.0) PRED[m] = 32.0;
    }
}

static u64 rngs;
static inline u64 xs64(){ u64 x=rngs; x^=x<<13; x^=x>>7; x^=x<<17; return rngs=x; }

#define MAXCHUNK 40
static u32 *FR;                 // front rows (u32), allocated once

static void features(mpz_t n0, mpz_t x, int bits, int T, double *out){
    long b0 = bits;
    u64 S = 0;
    double f3[3]={0,0,0}, t3[3]={0,0,0}, c3[3]={0,0,0};
    static u64 colw[MAXCHUNK][64];
    memset(colw, 0, sizeof colw);
    int nf = 0, trow = 0;
    __gmpz_set(x, n0);
    for (int r=0; r<T; r++){
        __gmpz_mul_ui(x, x, 3);
        __gmpz_add_ui(x, x, 1);
        mp_bitcnt_t v = __gmpz_scan1(x, 0);
        __gmpz_tdiv_q_2exp(x, x, v);
        S += v;
        long bl = bits_of(x);
        if (bl < 70) break;
        top3(f3, rowscore64(get64(x, bl-64)));
        if (nf < TCAP) FR[nf++] = (u32)(get64(x, bl-64) >> 32);
        long top = S + bl;
        if (S <= (u64)b0 && top >= b0 + 64){
            u64 w = get64(x, b0 - S);
            top3(t3, rowscore64(w));
            int ch = trow >> 6, bi = trow & 63;
            if (ch < MAXCHUNK)
                for (int j=0; j<64; j++)
                    colw[ch][j] |= ((w>>j)&1ULL) << bi;
            trow++;
        }
    }
    int chunks = trow >> 6;
    for (int ch=0; ch<chunks && ch<MAXCHUNK; ch++)
        for (int j=0; j<64; j++)
            top3(c3, rowscore64(colw[ch][j]));
    double vmax = -100;
    for (int li=0; li<63+VC; li++){
        int m = li < 63 ? li+2 : XLAGS[li-63];
        if (m >= nf-8 || m >= TCAP) continue;
        double acc=0; int cnt=0;
        for (int r=0; r+m<nf; r++){
            u32 d = FR[r] ^ FR[r+m];
            acc += d ? __builtin_clz(d) : 32;
            cnt++;
        }
        if (cnt >= 8){
            double an = acc/cnt - PRED[m];
            if (an > vmax) vmax = an;
        }
    }
    out[0]=avg3(f3); out[1]=avg3(t3); out[2]=avg3(c3); out[3]=vmax;
}

int main(int argc, char **argv){
    if (argc < 6) return 1;
    int bits = atoi(argv[2]);
    int T = atoi(argv[3]);
    long N = atol(argv[4]);
    rngs = strtoull(argv[5], 0, 10);
    LOG2W64 = log2(64.0);
    mkpred(T+1);
    FR = malloc(sizeof(u32) * TCAP);
    int limbs = bits / 64;
    u64 *buf = malloc(sizeof(u64) * limbs);
    mpz_t n0, x;
    __gmpz_init2(n0, bits + 64);
    __gmpz_init2(x, bits + 8*T);
    int scan = !strcmp(argv[1], "scan");
    double th[4] = {1e9,1e9,1e9,1e9};
    FILE *fo = 0;
    if (scan){
        for (int i=0;i<4;i++) th[i] = atof(argv[6+i]);
        fo = fopen(argv[10], "w");
    }
    double mx[4] = {-1e9,-1e9,-1e9,-1e9};
    char *hex = malloc(bits/4 + 8);
    for (long i=0; i<N; i++){
        for (int j=0; j<limbs; j++) buf[j] = xs64();
        buf[limbs-1] |= 1ULL<<63;
        buf[0] |= 1ULL;
        __gmpz_import(n0, limbs, -1, 8, 0, 0, buf);
        double o[4];
        features(n0, x, bits, T, o);
        for (int k2=0;k2<4;k2++) if (o[k2]>mx[k2]) mx[k2]=o[k2];
        if (scan && (o[0]>th[0]||o[1]>th[1]||o[2]>th[2]||o[3]>th[3])){
            __gmpz_get_str(hex, 16, n0);
            fprintf(fo, "%s %.3f %.3f %.3f %.3f\n", hex, o[0],o[1],o[2],o[3]);
        }
    }
    if (scan) fclose(fo);
    else printf("%.4f %.4f %.4f %.4f\n", mx[0],mx[1],mx[2],mx[3]);
    return 0;
}
