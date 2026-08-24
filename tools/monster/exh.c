// EXHAUSTIVE sweep of a class n = (m << (j+1)) - 1, m in [2^(mb-1), 2^mb)
// u128 fast path; rare overflow cases fall back to exact 512-bit arithmetic.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned __int128 u128;
#define L 8
typedef struct { uint64_t w[L]; } big;
static int is_one(const big*a){ if(a->w[0]!=1) return 0; for(int i=1;i<L;i++) if(a->w[i]) return 0; return 1; }
static int mul3p1(big*a){ unsigned __int128 c=1; for(int i=0;i<L;i++){ unsigned __int128 t=(unsigned __int128)a->w[i]*3+c; a->w[i]=(uint64_t)t; c=t>>64;} return c!=0; }
static int ctzb(const big*a){ for(int i=0;i<L;i++) if(a->w[i]) return i*64+__builtin_ctzll(a->w[i]); return -1; }
static void shrb(big*a,int k){ int ws=k/64,bs=k%64; for(int i=0;i<L;i++){ uint64_t lo=(i+ws<L)?a->w[i+ws]:0, hi=(i+ws+1<L)?a->w[i+ws+1]:0; a->w[i]= bs?((lo>>bs)|(hi<<(64-bs))):lo; } }
static long slow(uint64_t m,int j){
    big n; for(int i=0;i<L;i++) n.w[i]=0;
    int ws=(j+1)/64, bs=(j+1)%64;
    n.w[ws]= bs?(m<<bs):m; if(bs&&ws+1<L) n.w[ws+1]=m>>(64-bs);
    for(int i=0;i<L;i++){ if(n.w[i]){n.w[i]--;break;} else n.w[i]=~0ULL; }
    long s=0;
    while(!is_one(&n)){ if(mul3p1(&n)) return -1; shrb(&n,ctzb(&n)); s++; if(s>500000) return -1; }
    return s;
}
int main(int argc,char**argv){
    int bits=atoi(argv[1]), j=atoi(argv[2]);
    uint64_t lo=strtoull(argv[3],0,10), hi=strtoull(argv[4],0,10);
    int mb=bits-j-1;
    u128 LIM=((u128)1)<<125;
    long best=0; uint64_t bestm=0; long slowcnt=0;
    for(uint64_t m=lo;m<hi;m++){
        u128 n=(((u128)m)<<(j+1))-1;
        long s=0; int of=0;
        while(n!=1){
            if(n>LIM){of=1;break;}
            u128 x=3*n+1; while(!(x&1)) x>>=1; n=x; s++;
        }
        if(of){ slowcnt++; s=slow(m,j); if(s<0) continue; }
        if(s>best){ best=s; bestm=m; }
    }
    printf("%ld %llu %ld\n",best,(unsigned long long)bestm,slowcnt);
    return 0;
}
