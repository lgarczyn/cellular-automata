// leftscan.c: ambitious left-edge scanner for the real CA (rows = odd steps).
// Four channels per seed, all in the fresh region past the seed's MSB:
//   t: tape-frame row structure (const runs + exact periods 2..8), top-3 avg
//   f: MSB-aligned front row structure, top-3 avg
//   c: fixed-COLUMN time-periodicity (never scanned before), top-3 avg
//   v: per-seed quasicrystal anomaly: mean MSB-agreement depth at lag m
//      minus the universal prediction -log2|frac(m log2 3)|-1, max over m
// usage:
//   leftscan calib <mode32|mode64> <T> <N> <seed>
//   leftscan exh <lo> <hi> <T> <tht> <thf> <thc> <thv> <outfile>
//   leftscan rand <T> <count> <seed> <tht> <thf> <thc> <thv> <outfile>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

typedef unsigned __int128 u128;
typedef uint64_t u64;
typedef uint32_t u32;

static inline int bl64(u64 x){ return x ? 64-__builtin_clzll(x) : 0; }
static inline int bl128(u128 x){ u64 hi=(u64)(x>>64); return hi? 64+bl64(hi): bl64((u64)x); }

static inline int runlen(u64 t){ int c=0; while(t){ t &= t>>1; c++; } return c; }

// bits-of-evidence: longest constant run, or longest exactly p-periodic
// stretch (extra matched bits beyond the first period), minus log2(w)
static inline double rowscore(u64 seg, int w){
    if (w < 14) return 0.0;
    if (w > 64) w = 64;
    u64 mask = (w==64)? ~0ULL : ((1ULL<<w)-1);
    seg &= mask;
    int best = runlen(seg);
    int r0 = runlen((~seg)&mask);
    if (r0 > best) best = r0;
    for (int p=2; p<=8; p++){
        if (w-p < 10) break;
        u64 mm = ((1ULL<<(w-p))-1);
        u64 d = (seg ^ (seg>>p)) & mm;
        int z = runlen((~d)&mm);          // matched bits beyond one period
        if (z > best) best = z;
    }
    return (double)best - log2((double)w);
}

static inline void top3(double *a, double v){
    if (v > a[0]){ a[2]=a[1]; a[1]=a[0]; a[0]=v; }
    else if (v > a[1]){ a[2]=a[1]; a[1]=v; }
    else if (v > a[2]) a[2]=v;
}
static inline double avg3(double *a){ return (a[0]+a[1]+a[2])/3.0; }

#define TMAX 80
#define NCOL 40
static double PRED[TMAX+1];

static void mkpred(int T){
    double l23 = log2(3.0);
    for (int m=1; m<=T; m++){
        double fr = fmod(m*l23, 1.0);
        if (fr > 0.5) fr = 1.0-fr;
        PRED[m] = (fr<=0)? 32.0 : fmax(0.0, -log2(fr)-1.0);
        if (PRED[m] > 32.0) PRED[m] = 32.0;
    }
}

// returns via out[4]: t f c v
static void features(u64 n, int T, double *out){
    int b0 = bl64(n);
    u128 x = n;
    u64 S = 0;
    double t3[3]={0,0,0}, f3[3]={0,0,0}, c3[3]={0,0,0};
    u32 frows[TMAX]; int nf = 0;
    u64 colw[NCOL]; int coln[NCOL];
    memset(colw, 0, sizeof colw); memset(coln, 0, sizeof coln);
    int rows = 0;
    for (int r=0; r<T; r++){
        if (x <= 1) break;
        u128 m = 3*x + 1;
        int v = __builtin_ctzll((u64)m);
        x = m >> v;
        S += v;
        int blx = bl128(x);
        u64 top = S + blx;
        u64 start = (u64)b0 > S ? (u64)b0 : S;
        rows++;
        if (top > start){
            int w = (int)(top - start);
            if (w >= 14){
                int ww = w > 64 ? 64 : w;
                // top ww bits of the fresh window
                u64 seg = (u64)(x >> (top - S - ww));
                top3(t3, rowscore(seg, ww));
            }
            // columns: absolute positions b0..b0+NCOL-1
            for (int j=0; j<NCOL; j++){
                u64 p = (u64)b0 + j;
                if (p >= S && p < top && coln[j] < 64){
                    colw[j] |= ((u64)((x >> (p - S)) & 1)) << coln[j];
                    coln[j]++;
                }
            }
        }
        if (blx >= 26){
            u64 fseg = (u64)(x >> (blx - 26));
            top3(f3, rowscore(fseg, 26));
            if (blx >= 32 && nf < TMAX)
                frows[nf++] = (u32)(x >> (blx - 32));
        }
    }
    for (int j=0; j<NCOL; j++)
        if (coln[j] >= 14) top3(c3, rowscore(colw[j], coln[j]));
    double vmax = -100.0;
    for (int m=2; m<nf-8; m++){
        double acc=0; int cnt=0;
        for (int r=0; r+m<nf; r++){
            u32 d = frows[r] ^ frows[r+m];
            acc += d ? __builtin_clz(d) : 32;
            cnt++;
        }
        if (cnt >= 8){
            double an = acc/cnt - PRED[m];
            if (an > vmax) vmax = an;
        }
    }
    out[0]=avg3(t3); out[1]=avg3(f3); out[2]=avg3(c3); out[3]=vmax;
}

static u64 xs(u64 *s){ u64 x=*s; x^=x<<13; x^=x>>7; x^=x<<17; return *s=x; }

int main(int argc, char **argv){
    if (argc < 2) return 1;
    if (!strcmp(argv[1], "calib")){
        int m64 = !strcmp(argv[2], "mode64");
        int T = atoi(argv[3]);
        long N = atol(argv[4]);
        u64 seed = strtoull(argv[5], 0, 10);
        mkpred(T);
        double mx[4] = {0,0,0,-100};
        for (long i=0; i<N; i++){
            u64 n = xs(&seed);
            if (!m64) n = (n & 0x7fffffffULL) | 0x80000000ULL;
            n |= 1; n |= m64 ? (1ULL<<63) : 0;
            double o[4]; features(n, T, o);
            for (int k=0;k<4;k++) if (o[k]>mx[k]) mx[k]=o[k];
        }
        printf("%.6f %.6f %.6f %.6f\n", mx[0], mx[1], mx[2], mx[3]);
        return 0;
    }
    if (!strcmp(argv[1], "exh")){
        u64 lo = strtoull(argv[2],0,10), hi = strtoull(argv[3],0,10);
        int T = atoi(argv[4]);
        double th[4] = {atof(argv[5]),atof(argv[6]),atof(argv[7]),atof(argv[8])};
        FILE *f = fopen(argv[9], "w");
        mkpred(T);
        for (u64 n = lo|1; n < hi; n += 2){
            double o[4]; features(n, T, o);
            if (o[0]>th[0]||o[1]>th[1]||o[2]>th[2]||o[3]>th[3])
                fprintf(f, "%llu %.4f %.4f %.4f %.4f\n",
                        (unsigned long long)n, o[0],o[1],o[2],o[3]);
        }
        fclose(f);
        return 0;
    }
    if (!strcmp(argv[1], "rand")){
        int T = atoi(argv[2]);
        long N = atol(argv[3]);
        u64 seed = strtoull(argv[4],0,10);
        double th[4] = {atof(argv[5]),atof(argv[6]),atof(argv[7]),atof(argv[8])};
        FILE *f = fopen(argv[9], "w");
        mkpred(T);
        for (long i=0; i<N; i++){
            u64 n = xs(&seed) | 1 | (1ULL<<63);
            double o[4]; features(n, T, o);
            if (o[0]>th[0]||o[1]>th[1]||o[2]>th[2]||o[3]>th[3])
                fprintf(f, "%llu %.4f %.4f %.4f %.4f\n",
                        (unsigned long long)n, o[0],o[1],o[2],o[3]);
        }
        fclose(f);
        return 0;
    }
    return 1;
}
