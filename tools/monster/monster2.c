// long-run searcher: logs best-so-far and overflow candidates to files
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static inline uint64_t xs(uint64_t *s){uint64_t x=*s;x^=x<<13;x^=x>>7;x^=x<<17;return *s=x;}
int main(int argc,char**argv){
    int bits=atoi(argv[1]), j=atoi(argv[2]);
    long count=atol(argv[3]); uint64_t seed=strtoull(argv[4],0,10);
    const char*tag=argv[5];
    char fb[256],fo[256];
    snprintf(fb,256,"best_%s.txt",tag); snprintf(fo,256,"ovf_%s.txt",tag);
    int mbits=bits-j-1;
    u128 LIM=((u128)1)<<125;
    long best=0; long ovf=0;
    FILE*fov=fopen(fo,"a");
    for(long t=0;t<count;t++){
        uint64_t m;
        m=xs(&seed);
        if(mbits<64) m&=(((uint64_t)1)<<mbits)-1;
        m|=((uint64_t)1)<<(mbits-1);
        u128 n=(((u128)m)<<(j+1))-1;
        long s=0; int bad=0;
        while(n!=1){
            if(n>LIM){bad=1;break;}
            u128 x=3*n+1;
            while(!(x&1)) x>>=1;
            n=x; s++;
            if(s>100000){bad=2;break;}
        }
        if(bad==1){ovf++; fprintf(fov,"%llu\n",(unsigned long long)m); fflush(fov); continue;}
        if(bad) continue;
        if(s>best){
            best=s;
            FILE*f=fopen(fb,"a");
            fprintf(f,"%ld %llu\n",s,(unsigned long long)m);
            fclose(f);
        }
    }
    fclose(fov);
    return 0;
}
