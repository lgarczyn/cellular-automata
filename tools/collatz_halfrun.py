#!/usr/bin/env python3
"""Half machines: right edge looping, left edge free to march. They exist.

Run: python3 tools/collatz_halfrun.py

A "half machine" is not a cycle. It is the gadget where the LOW-order behaviour
is periodic - a prescribed, repeating halving pattern - while the value grows
without bound and the MSB edge marches off irrationally. One edge loops, one
does not.

These are real and easy to build. The canonical one is the all-ones tape
n = 2^d - 1, which sustains "exactly one halving per odd step" - the minimum
possible, hence the fastest possible growth - because after j steps its value is
3^j * 2^(d-j) - 1, odd exactly while d - j >= 1. It runs for d steps, growing by
(3/2)^d, and then stops dead.

That bound is general, and it is the point:

  * every odd step costs at least one halving, i.e. at least one bit off the
    right edge, and the first k parity decisions depend only on n mod 2^k
  * so d bits of tape buy at most d steps of prescribed behaviour, for ANY
    pattern, not just this one - measured across patterns below, total halvings
    always lands at the tape length
  * the machine does grow - from d bits to d*log2(3) bits - but the bits it
    gains are carries, fixed by arithmetic, not chosen by anyone

So the exchange rate is log2(3) - 1 = 0.58496 undesigned bits gained per
designed bit spent. A bootstrap needs that ratio above 1. It is not, it cannot
be tuned, and it is the same log2(3) that governs everything else here.

That is the precise form of "not self-sustaining": a half machine is not
impossible, it is a fuse. It burns at one bit per step and the length of the
fuse is the length of the tape.
"""

import math
import random


def sustain(n, pattern):
    """Run while the halving counts follow `pattern` cyclically."""
    steps = halvings = 0
    start = n
    while True:
        t, v = 3 * n + 1, 0
        while t % 2 == 0:
            t //= 2
            v += 1
        if v != pattern[steps % len(pattern)]:
            return steps, halvings, start, n
        n, halvings, steps = t, halvings + v, steps + 1


def best_seed(pattern, bits):
    """The bits-bit odd seed sustaining `pattern` longest (brute force)."""
    best = (0, 0)
    for r in range(1, 1 << bits, 2):
        s = sustain(r, pattern)[0]
        if s > best[1]:
            best = (r, s)
    return best


def main():
    print("all-ones tape n = 2^d - 1, the optimal half machine:")
    print("  %5s %12s %7s %16s %s" % ("d", "n", "steps", "final value", "growth"))
    for d in range(3, 13):
        s, h, a, b = sustain(2 ** d - 1, [1])
        print("  %5d %12d %7d %16d  x(3/2)^%d" % (d, 2 ** d - 1, s, b, s))
    print("  value after j steps is 3^j * 2^(d-j) - 1: odd while d-j >= 1, even at j=d.")
    print()

    print("the same budget holds for arbitrary prescribed patterns:")
    print("  %-12s %6s %7s %10s %8s %s" % ("pattern", "bits", "steps", "halvings", "a/b", ""))
    random.seed(4)
    for pattern in ([1], [1, 2, 1], [2, 1, 1], [1, 2, 3], [3, 2, 2]):
        bits = 18
        r, _ = best_seed(pattern, bits)
        s, h, a, b = sustain(r, pattern)
        rate = h / max(s, 1)
        print("  %-12s %6d %7d %10d %8.2f %s" % (str(pattern), bits, s, h, rate,
                                                 "grows" if rate < math.log2(3) else "shrinks"))
    print("  halvings consumed always lands at the tape length - the fuse burns to the end.")
    print()

    print("information budget over one lifetime:")
    for d in (16, 64, 256, 1024):
        s, h, a, b = sustain(2 ** d - 1, [1])
        gained = math.log2(b) - d
        print("  %5d-bit tape: %5d steps, ends at %7.1f bits" % (d, s, math.log2(b)))
        print("        spent %5d designed bits, gained %7.1f carry bits -> rate %.3f"
              % (d, gained, gained / d))
    print()
    print("  rate -> log2(3) - 1 = %.5f, and a bootstrap needs > 1." % (math.log2(3) - 1))


if __name__ == "__main__":
    main()
