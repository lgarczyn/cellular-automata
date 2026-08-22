// exact recheck of overflow candidates with 512-bit fixed-width arithmetic
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define L 8                      // 8 * 64 = 512 bits
typedef struct { uint64_t w[L]; } big;

static int is_one(const big*a){ if(a->w[0]!=1) return 0; for(int i=1;i<L;i++) if(a->w[i]) return 0; return 1; }
static int top_bit(const big*a){ for(int i=L-1;i>=0;i--) if(a->w[i]) return i*64 + 63 - __builtin_clzll(a->w[i]); return -1; }
// a = 3a + 1 ; returns 1 on overflow out of 512 bits
static int mul3p1(big*a){
    unsigned __int128 carry = 1;
    for(int i=0;i<L;i++){
        unsigned __int128 t = (unsigned __int128)a->w[i]*3 + carry;
        a->w[i] = (uint64_t)t;
        carry = t >> 64;
    }
    return carry != 0;
}
static int ctz(const big*a){
    for(int i=0;i<L;i++) if(a->w[i]) return i*64 + __builtin_ctzll(a->w[i]);
    return -1;
}
static void shr(big*a, int k){
    int wsh = k/64, bsh = k%64;
    for(int i=0;i<L;i++){
        uint64_t lo = (i+wsh < L) ? a->w[i+wsh] : 0;
        uint64_t hi = (i+wsh+1 < L) ? a->w[i+wsh+1] : 0;
        a->w[i] = bsh ? ((lo>>bsh) | (hi<<(64-bsh))) : lo;
    }
}
int main(int argc,char**argv){
    int j = atoi(argv[1]);
    unsigned long long m;
    long best = 0; unsigned long long bestm = 0; int bestpeak = 0;
    long over = 0;
    while(scanf("%llu",&m)==1){
        big n; for(int i=0;i<L;i++) n.w[i]=0;
        // n = (m << (j+1)) - 1
        int wsh=(j+1)/64, bsh=(j+1)%64;
        n.w[wsh] = bsh ? (m<<bsh) : m;
        if(bsh && wsh+1<L) n.w[wsh+1] = m>>(64-bsh);
        // subtract 1
        for(int i=0;i<L;i++){ if(n.w[i]){ n.w[i]--; break; } else n.w[i]=~0ULL; }
        long s=0; int peak=0, bad=0;
        while(!is_one(&n)){
            if(mul3p1(&n)){ bad=1; break; }
            int t = top_bit(&n); if(t>peak) peak=t;
            shr(&n, ctz(&n));
            s++;
            if(s>500000){ bad=2; break; }
        }
        if(bad){ over++; continue; }
        if(s>best){ best=s; bestm=m; bestpeak=peak+1; }
    }
    printf("%ld %llu %d %ld\n", best, bestm, bestpeak, over);
    return 0;
}
