#!/usr/bin/env python3
"""When is the MSB edge's slope rational? Exactly when it loops. Only at n=1.

Run: python3 tools/collatz_rational.py

The per-step slope of the left edge, including the +1 correction, is

    log2(3) + log2(1 + 1/(3n))  =  log2((3n+1)/n)

Ask for that to be rational. Then ((3n+1)/n)^q = 2^p, so (3n+1)^q = 2^p n^q.
Any prime r dividing n divides the right side, hence divides (3n+1)^q, hence
divides 3n+1; but r divides 3n, so r divides 1. Contradiction. So n = 1 - and
there the slope is log2(4) = 2 exactly, which is the trivial cycle.

The drift term on its own is even starker: log2((3n+1)/(3n)) rational needs
3n | 1, so it is irrational for EVERY n without exception.

Generalised to a window of k odd steps from odd n0 to odd nk with A halvings,
the edge advance is log2(2^A * nk / n0). A rational power of 2 that is itself
rational must be an integer power, so nk/n0 = 2^j, and both being odd forces
nk = n0. Hence, at every window length:

    edge advance rational  <=>  advance is a whole number of columns  <=>  cycle

Which makes the intuition exact in both directions. "If it looped, the left
edge would be rational" is true, and so is its converse: nothing short of a
genuine cycle ever makes the left edge commensurable with the grid. The k=1
case is fully solved - 3n+1 = 2^A n forces n(2^A - 3) = 1, so n = 1, A = 2.
"""

import math
import random
from fractions import Fraction


def single_step_solutions(limit=200_000):
    """All n <= limit with log2((3n+1)/n) rational."""
    out = []
    for n in range(1, limit):
        x = Fraction(3 * n + 1, n)
        if x.denominator == 1 and (x.numerator & (x.numerator - 1)) == 0:
            out.append((n, x.numerator))
    return out


def window_scan(trials=400, seed=11, max_k=12):
    """Smallest distance to an integer over non-closing windows."""
    rng = random.Random(seed)
    best = 1.0
    count = 0
    for _ in range(trials):
        n = rng.randrange(3, 10 ** 9, 2)
        seq, halv, H = [n], [0], 0
        while n != 1 and len(seq) < 200:
            t, v = 3 * n + 1, 0
            while t % 2 == 0:
                t //= 2
                v += 1
            n, H = t, H + v
            seq.append(n)
            halv.append(H)
        for i in range(len(seq)):
            for k in range(1, min(max_k, len(seq) - i)):
                if seq[i + k] == seq[i]:
                    continue
                adv = (halv[i + k] - halv[i]) + math.log2(seq[i + k]) - math.log2(seq[i])
                best = min(best, abs(adv - round(adv)))
                count += 1
    return best, count


def main():
    sols = single_step_solutions()
    print("n with log2((3n+1)/n) rational, searched to 2*10^5: %s" % sols)
    print("  (n=1 gives 4 = 2^2, slope exactly 2 - the trivial cycle)")
    print()
    print("nearest small-denominator rational to the slope, by n:")
    for n in (1, 2, 3, 27, 1000, 10 ** 6):
        s = math.log2((3 * n + 1) / n)
        err, p, q = min((abs(s - p / q), p, q) for q in range(1, 13) for p in range(1, 4 * q + 1))
        print("   n = %-9d slope %.9f   nearest %2d/%-2d  off by %.2e" % (n, s, p, q, err))
    print()
    best, count = window_scan()
    print("windows of up to 12 odd steps that do NOT close (%d of them):" % count)
    print("   closest the edge advance came to an integer: %.6f" % best)
    print("   a closing window would give exactly 0 - the advance would be A itself")
    print()
    print("so: rational <=> integer <=> cycle, at every window length.")
    print("    the left edge is never commensurable with the grid unless it loops,")
    print("    and for a single step that happens only at n = 1.")


if __name__ == "__main__":
    main()
