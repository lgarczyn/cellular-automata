#!/usr/bin/env python3
"""Scan the MSB region of random x3 orbits for emergent repeating patterns.

Run: python3 tools/collatz_msbscan.py     (all cores)

Using random seeds, a periodic tail (looping right), and hundreds of thousands of
window sizes: examine the top N cells (from the MSB) of x3 orbits and score how
close they come to a spatial repeat (a block repeating >=3 times).

Result across ~640k windows: near-repeats appear ONLY in tiny windows (<=30
cells) and ONLY at the rate pure chance gives - a companion control (collatz vs
truly random bits) matches to 2 decimals at every window size. For windows >= 44
cells, zero near-repeats. The MSB of a x3 orbit is the equidistributed mantissa
of 3^t (Benford); it does not approach a repeating pattern.

Repetition in this automaton lives on the LSB-anchored side (the crystals of
collatz_traveling.py / collatz_build.py, built deliberately), never in the MSB
garbling front. See collatz-anchored.png for why: x3 is lower-triangular, so the
LSB is frozen/structured and the MSB is the disordered growing front.
"""

import random, time
from multiprocessing import Pool, cpu_count

def best_period(bits):
    """Return (best_frac, period) for near-periodicity of a 0/1 list, >=3 repeats."""
    N = len(bits)
    best_frac, best_p = 0.0, 0
    for p in range(2, N // 3 + 1):           # need at least 3 repeats
        m = sum(1 for i in range(p, N) if bits[i] == bits[i - p])
        frac = m / (N - p)
        if frac > best_frac:
            best_frac, best_p = frac, p
    return best_frac, best_p

def worker(args):
    seed, trials = args
    rng = random.Random(seed)
    hits = []                                 # (frac, N, p, W, step, value_of_window)
    for _ in range(trials):
        W = rng.randint(40, 1500)
        x = rng.getrandbits(W) | 1
        steps = rng.randint(0, 40)
        for _ in range(steps):
            x = 3 * x
        bl = x.bit_length()
        N = rng.randint(24, 160)
        if bl < N + 4:
            continue
        top = [(x >> (bl - 1 - i)) & 1 for i in range(N)]   # N cells from the MSB
        frac, p = best_period(top)
        if frac >= 0.88 and N // p >= 3:
            hits.append((round(frac, 4), N, p, W, steps))
    hits.sort(reverse=True)
    return hits[:30]

def main():
    n = cpu_count()
    per = 40000
    print("scanning %d random MSB windows on %d cores..." % (per * n, n))
    t0 = time.time()
    with Pool(n) as pool:
        parts = pool.map(worker, [(i, per) for i in range(n)])
    dt = time.time() - t0
    allh = [h for part in parts for h in part]
    allh.sort(reverse=True)
    total = per * n
    print("scanned ~%d windows in %.1fs" % (total, dt))
    print("windows that approach a repeat (frac>=0.88, >=3 repeats):", len(allh))
    print()
    print("best MSB near-repeats (frac = fraction of bits matching the period):")
    print("   %-7s %-5s %-5s %-6s %-6s %s" % ("frac", "N", "period", "repeats", "seedW", "step"))
    seen = set()
    shown = 0
    for frac, N, p, W, steps in allh:
        key = (N, p, W, steps)
        if key in seen:
            continue
        seen.add(key)
        print("   %-7.4f %-5d %-5d %-6.1f %-6d %d" % (frac, N, p, N / p, W, steps))
        shown += 1
        if shown >= 30:
            break
    print()
    # how does near-repeat quality scale with window size N?
    from collections import defaultdict
    byN = defaultdict(list)
    for frac, N, p, W, steps in allh:
        byN[N // 20 * 20].append(frac)
    print("best frac by MSB-window size:")
    for nb in sorted(byN):
        v = byN[nb]
        print("   N~%-4d : best %.3f  (%d hits)" % (nb, max(v), len(v)))

if __name__ == "__main__":
    main()
