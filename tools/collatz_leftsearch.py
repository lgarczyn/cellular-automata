#!/usr/bin/env python3
"""Exhaustive hunt for a LOCALIZED left-mover under the free-MSB bulk. None exist.

Run: python3 tools/collatz_leftsearch.py     (uses all cores; ~30s on 16)

The question: a localized pattern (a bounded packet, not a full-ring crystal)
that travels LEFT toward the MSB while keeping its shape - a glider/soliton -
under the free-MSB boundary (terminating head, looping tail). We searched tens of
thousands of packets at every phase. There is a clean reason none survive, and
the search confirms it at scale.

WHY IT CANNOT WORK (linearity). The bulk map is x -> 3x. It is linear, so the
disturbance of a packet on ANY background is (state - background) = 3^t * e0,
independent of the background entirely. And 3^t * e0 for a localized e0 grows in
bit-span at exactly log2(3) per step, forever. A localized disturbance therefore
always disperses at the light-cone speed; the background is irrelevant, and no
choice of packet or phase changes it.

THE SEARCH (three parts, all below):

  A. 77,535 localized packets (every shape to width 16, plus sparse packets swept
     over all 210 phases) on a W=210 looping ring. Track the cyclic support span
     of 3^t*e0 for 150 steps. Result: min max-span 203 of 210 - every packet
     fills the ring. Zero stay within W/4. Lifetime to 2x span: ~10 steps.

  B. 20,000 random localized packets under the true free-MSB edge (3^t*e0 as a
     growing integer). The bit-span growth slope is log2(3) for every one
     (measured 1.581 - 1.588, mean 1.5851). No exceptions.

  C. The left-movers that DO exist are the non-localized traveling crystals of
     collatz_traveling.py: 2,022 denominators below 20,000, ~19.4 million distinct
     patterns once you count phase (numerator), each shifting rigidly left. They
     fill the ring; none is localized.

CONCLUSION. Under the pure bulk there is no localized left-mover, provably. The
only place a genuine glider could hide is the ONE nonlinearity we have not put
back: the Collatz parity branch (the halving / 3x+1 choice). x -> 3x is linear
and cannot support gliders; x -> (3x+1 or x/2) is not. That is the search the
next session should run - packets under the full branched rule, not the bulk.
"""

import statistics
import sys
from math import gcd, log2
from multiprocessing import Pool, cpu_count

W = 210
M = (1 << W) - 1
T = 150
NPROC = cpu_count()


def ord2(d):
    k, x = 1, 2 % d
    while x != 1:
        x = x * 2 % d
        k += 1
    return k


def dlog2_of_3(d):
    x = 2 % d
    for k in range(1, ord2(d) + 1):
        if x == 3 % d:
            return k
        x = x * 2 % d
    return None


def span_ring(x):
    """Smallest cyclic arc (cells) containing every set bit of x on a W-ring."""
    if x == 0:
        return 0
    pos = [i for i in range(W) if (x >> i) & 1]
    if len(pos) == 1:
        return 1
    gaps = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
    gaps.append(pos[0] + W - pos[-1])
    return W - max(gaps)


def worker(seeds):
    out = []
    for e0 in seeds:
        x = e0 % M
        if x == 0:
            continue
        s0 = span_ring(x)
        maxs, life = s0, T
        for t in range(1, T + 1):
            x = (3 * x) % M
            s = span_ring(x)
            maxs = max(maxs, s)
            if s > 2 * s0 and life == T:
                life = t
        out.append((e0, s0, maxs, life))
    return out


def part_A():
    seeds = list(range(1, 1 << 16))
    sparse = [e for e in range(1, 1 << 12) if bin(e).count("1") <= 4][:400]
    for e in sparse:
        for ph in range(0, W, 7):
            seeds.append((e << ph) % M or e)
    print("A. localized-packet search: %d seeds on a W=%d looping ring, %d steps"
          % (len(seeds), W, T))
    chunks = [seeds[i::NPROC] for i in range(NPROC)]
    with Pool(NPROC) as p:
        res = [r for part in p.map(worker, chunks) for r in part]
    res.sort(key=lambda r: (r[2], -r[3]))
    ms = [r[2] for r in res]
    print("   max-span over %d steps: min %d, median %d, max %d (ring = %d cells)"
          % (T, min(ms), int(statistics.median(ms)), max(ms), W))
    print("   packets that stayed within W/4 = %d cells: %d of %d"
          % (W // 4, sum(1 for m in ms if m <= W // 4), len(res)))
    print("   most-bounded packet reached span %d in %d steps - still fills the ring"
          % (res[0][2], res[0][3]))
    print()


def part_B():
    import random
    random.seed(1)
    slopes = []
    for _ in range(20000):
        e0 = random.getrandbits(random.randint(1, 16)) | 1
        x, spans = e0, []
        for _ in range(60):
            x = 3 * x
            spans.append(x.bit_length())
        xs, ys = list(range(20, 60)), spans[20:]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        slopes.append(sum((a - mx) * (b - my) for a, b in zip(xs, ys))
                      / sum((a - mx) ** 2 for a in xs))
    print("B. free-MSB dispersal: bit-span slope of 3^t*e0 over 20000 random packets")
    print("   mean %.5f, min %.5f, max %.5f   (log2 3 = %.5f)"
          % (statistics.mean(slopes), min(slopes), max(slopes), log2(3)))
    print("   every localized disturbance disperses at log2(3); none stay bounded.")
    print()


def part_C(dmax=20000):
    movers, phases = [], 0
    for d in range(5, dmax, 2):
        if d % 3 == 0:
            continue
        k = dlog2_of_3(d)
        if k is not None:
            movers.append((d, ord2(d), k))
            phases += d - 1
    print("C. the left-movers that exist: %d traveling-crystal denominators < %d,"
          % (len(movers), dmax))
    print("   %d distinct patterns counting phase - all non-localized (fill the ring)."
          % phases)
    import random
    random.seed(3)
    ok = checked = 0
    for d, p, k in random.sample(movers, min(300, len(movers))):
        Mp = (1 << p) - 1
        if Mp % d:
            continue
        for a in random.sample(range(1, d), min(5, d - 1)):
            X = a * (Mp // d) % Mp
            checked += 1
            ok += (3 * X) % Mp == (((X << k) | (X >> (p - k))) & Mp)
    print("   verified rigid left-shift 3X == X<<k on %d/%d crystal+phase samples"
          % (ok, checked))


if __name__ == "__main__":
    part_A()
    part_B()
    part_C()
