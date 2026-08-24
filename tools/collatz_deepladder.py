#!/usr/bin/env python3
"""The deep echo ladder. SCOPE: [real-CA].

A designed flash at step k echoes at k+m for every continued-fraction
convergent denominator m of log2(3), with depth -log2|frac(m*log2 3)| - 1.
The first pass verified the ladder to m = 665. This climbs it to
m = 15601, 31867, 79335 and 111202 on real runs of tapes up to ~47,000
bits, run for up to ~111k odd steps.

The predicted depth is computed EXACTLY (frac(m*log2 3) via the top bits
of the integer 3^m), not with float log arithmetic.
"""
import sys
from math import log2

LADDER = [12, 53, 306, 665, 15601, 31867, 79335, 111202, 190537, 10590737]


def exact_frac_log2_3m(m):
    """frac(m * log2 3) computed from the integer 3^m."""
    e = 3**m
    bl = e.bit_length() - 1
    sh = bl - 80                         # 80-bit mantissa, plenty
    top = e >> sh if sh >= 0 else e << -sh
    return log2(top / (1 << 80)) % 1.0


def predicted_depth(m):
    fr = exact_frac_log2_3m(m)
    fr = min(fr, 1.0 - fr)
    return max(0.0, -log2(fr) - 1.0)


def lead_run_of(x, W=48):
    b = x.bit_length()
    if b < W:
        return 0
    top = x >> (b - W)
    bits = [(top >> (W - 1 - i)) & 1 for i in range(W)]
    first = bits[1]
    c = 0
    for v in bits[1:]:
        if v != first:
            break
        c += 1
    return c


def run_ladder(m, k=40, margin=400):
    T = k + m + 4
    thick = int(0.43 * T) + margin
    n = ((1 << thick) // 3**k) | 1
    x = n
    hits = {}
    targets = {k + mm: mm for mm in [0] + LADDER if k + mm <= T}
    for r in range(1, T + 1):
        if x <= 1:
            return None
        mm3 = 3 * x + 1
        x = mm3 >> ((mm3 & -mm3).bit_length() - 1)
        if r in targets:
            hits[targets[r]] = lead_run_of(x)
    return n.bit_length(), hits


def main():
    ms = [int(a) for a in sys.argv[1:]] or LADDER[4:]
    for m in ms:
        pred = {mm: predicted_depth(mm) for mm in LADDER if mm <= m}
        res = run_ladder(m)
        if res is None:
            print("m=%d: trajectory died early, increase margin" % m)
            continue
        bits, hits = res
        print("ladder to m=%d  (flash seed %d bits, %d odd steps):" %
              (m, bits, 40 + m + 4))
        for mm, d in sorted(hits.items()):
            p = 39.0 if mm == 0 else pred[mm]
            print("   echo at k+%-7d depth %2d bits   predicted %5.1f"
                  % (mm, d, p))


if __name__ == "__main__":
    main()
