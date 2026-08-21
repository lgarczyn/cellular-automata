#!/usr/bin/env python3
"""The hailstone-record protocol: guaranteed climb + searched fall. SCOPE: [real-CA rows].

The synthesis of the machine tools into a record search:
  1. RIGHT EDGE (guaranteed): restrict to n = -1 mod 2^(j+1). The fuse law
     guarantees j odd steps at v=1 (minimum legal consumption), +0.585 bits/step
     climb, no luck spent.
  2. LEFT EDGE (preserved cargo): the free bits m above the tape ride through
     the climb untouched (2-adic agreement) and arrive intact at the peak:
     they are the search space, delivered to the top.
  3. SEARCH: spend effort over m for a lucky generic fall (gain ~ ln E).

Pilot result (48-bit seeds, 480k trials/class, equal effort):
    j=0  mean 116  best 374 (7.8 steps/bit)
    j=24 mean 174  best 487 (10.15 steps/bit)   <- hybrid sweet spot
    j=40 mean 211  best 335 (7.0)               <- search space starved
  Mean rises +2.41 steps per designed bit (theory: 1 + 0.585*2.41). Best peaks
  at intermediate j: design raises the floor, search needs room for luck.
  Champion verified: n = 262018640642047 (48 bits, -1 mod 2^25): 487 odd steps,
  peak 67 bits.

WHAT BLOCKS IT (each measured or proved earlier in this program):
  1. The fuse law: every designed step costs >= 1 tape bit; designed steps <= K
     for a K-bit seed. No bootstrap (0 exceptions in 640k trials).
  2. The exchange rate log2(3) - 1 = 0.585 < 1: climb-generated carry bits are
     hash, not tape: they cannot be re-designed.
  3. Fall genericity: after the program ends, vbar -> 2 (measured): luck adds
     only ~ln(effort) steps; large deviations are exponentially expensive.
  4. Chaining collapse: multi-stage climb programs reduce to one tape (the
     total-steps formula is profile-independent): total <= ~4.82 odd steps per
     designed bit; single all-ones is already the optimal design.
  5. Scaling truth: designed giants win in ABSOLUTE steps (linear in K,
     certified) but the record RATIO (~8-10 steps/bit at small n) is a
     small-n luck phenomenon that cannot scale.
  6. The ceiling itself: sustained steps/bit above the designed+generic bound
     would need vbar < log2(3) forever = a divergent trajectory = the open
     Collatz problem.
"""
import random, time
from multiprocessing import Pool

BITS = 48
TRIALS = 120000

def odd_steps(n):
    s = 0
    while n != 1 and s < 200000:
        m = 3 * n + 1
        v = (m & -m).bit_length() - 1
        n = m >> v
        s += 1
    return s

def worker(args):
    j, seed = args
    rng = random.Random(seed)
    best, tot = 0, 0
    bestn = 0
    for _ in range(TRIALS):
        if j == 0:
            n = rng.getrandbits(BITS) | 1 | (1 << (BITS - 1))
        else:
            m = rng.getrandbits(BITS - j - 1) | (1 << (BITS - j - 2))
            n = (m << (j + 1)) - 1          # n = -1 mod 2^(j+1): j guaranteed v=1 steps
        s = odd_steps(n)
        tot += s
        if s > best:
            best, bestn = s, n
    return j, best, bestn, tot / TRIALS

if __name__ == "__main__":
    jobs = []
    for j in (0, 8, 16, 24, 32, 40):
        for w in range(4):
            jobs.append((j, j * 100 + w))
    t0 = time.time()
    with Pool(16) as p:
        res = p.map(worker, jobs)
    agg = {}
    for j, best, bestn, mean in res:
        b, bn, ms = agg.get(j, (0, 0, []))
        if best > b:
            b, bn = best, bestn
        ms.append(mean)
        agg[j] = (b, bn, ms)
    print("pilot: %d-bit seeds, %dk trials per class, equal effort per class"
          % (BITS, 4 * TRIALS // 1000))
    print("%6s %14s %12s %16s" % ("design", "mean steps", "best steps", "best steps/bit"))
    for j in sorted(agg):
        b, bn, ms = agg[j]
        print("  j=%-3d %14.1f %12d %16.2f   (n=%d)"
              % (j, sum(ms) / len(ms), b, b / BITS, bn))
    print("%.0fs" % (time.time() - t0))
