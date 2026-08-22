#!/usr/bin/env python3
"""The river is not noise: front-aligned self-similarity. SCOPE: [real-CA].

The first left-edge pass scanned rows in TAPE alignment and called the MSB
front "noise". This module re-examines the front in its own frame: align
every row at its MSB (the mantissa window) and correlate rows across TIME.

Prediction from the mantissa law (fresh front = leading bits of 3^r * n):
rows r and r+m agree in their top bits whenever 3^m is close to a power of
2, i.e. at the continued-fraction convergent denominators of log2(3):

    m = 12   (3^12 = 2^19.02)   ~5-6 bits deep
    m = 41, 53   (3^53 = 2^84.003)   ~8-9 bits deep
    m = 306, 665 ...  deeper still

So the left edge is a TIME QUASICRYSTAL: the same texture returns at
convergent lags, to a depth set by the convergent's quality, for EVERY
seed. Measured here on real runs (LeastEdge halvings and all).
"""
import random
import sys
from math import log2

import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__file__))

LOG23 = log2(3)


def front_matrix(n, T, W=40):
    """Row r = top W bits of the real-CA row value n_r (MSB-aligned)."""
    rows = []
    x = n
    for _ in range(T):
        if x <= 1:
            break
        m = 3 * x + 1
        x = m >> ((m & -m).bit_length() - 1)
        b = x.bit_length()
        if b < W:
            break
        top = x >> (b - W)
        rows.append([(top >> (W - 1 - i)) & 1 for i in range(W)])
    return np.array(rows, dtype=np.uint8)


def agreement_curve(M, maxlag):
    """agree[m] = mean fraction of equal bits between rows r and r+m."""
    T, W = M.shape
    out = np.zeros(maxlag + 1)
    for m in range(1, maxlag + 1):
        if T - m < 8:
            break
        eq = (M[:-m] == M[m:]).mean()
        out[m] = eq
    return out


def match_depth(M, m):
    """Mean number of leading bits in which rows r and r+m agree."""
    T, W = M.shape
    if T - m < 4:
        return 0.0
    a, b = M[:-m], M[m:]
    neq = a != b
    first = np.where(neq.any(axis=1), neq.argmax(axis=1), W)
    return float(first.mean())


def predicted_depth(m):
    """Bits of agreement predicted by |frac(m*log2 3)| (mantissa drift)."""
    fr = (m * LOG23) % 1.0
    fr = min(fr, 1.0 - fr)
    if fr == 0:
        return 40.0
    return max(0.0, -log2(fr) - 1.0)


def main():
    rng = random.Random(31)
    T, W, maxlag = 900, 40, 720
    NS = 24
    curves, depths = [], {}
    lags_of_interest = [1, 5, 7, 12, 24, 41, 53, 106, 159, 306, 359, 665]
    for _ in range(NS):
        n = rng.getrandbits(700) | (1 << 700) | 1
        M = front_matrix(n, T, W)
        curves.append(agreement_curve(M, maxlag))
        for m in lags_of_interest:
            depths.setdefault(m, []).append(match_depth(M, m))
    A = np.mean([c[: maxlag + 1] for c in curves], axis=0)
    print("front-aligned agreement, %d random 700-bit seeds, T=%d, W=%d"
          % (NS, T, W))
    print("%-6s %-10s %-12s %-12s" % ("lag", "agree", "meas. depth",
                                      "pred. depth"))
    order = np.argsort(A[1:])[::-1][:12] + 1
    for m in lags_of_interest:
        print("%-6d %-10.4f %-12.2f %-12.2f"
              % (m, A[m], np.mean(depths[m]), predicted_depth(m)))
    print("top lags by raw agreement:", sorted(order.tolist()))
    np.save("/var/tmp/collatz-scratch/river_curve.npy", A)


if __name__ == "__main__":
    main()
