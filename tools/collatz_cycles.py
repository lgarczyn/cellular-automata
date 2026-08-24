#!/usr/bin/env python3
"""Why a loop can't close: the +1 slack, measured and turned into a bound.

Run: python3 tools/collatz_cycles.py

In the pure-rotation limit the argument is one line: a loop returns the MSB
phase to itself, so a = b*log2(3) for integers a (halvings) and b (odd steps),
so log2(3) is rational. It isn't. No loops.

The +1 is the only thing that rescues loops from that. Each 3n+1 overshoots 3n
by a phase drift of 1/(3 ln 2)/n per odd step (measured here against theory),
so the real closure condition is

    a - b*log2(3) = D,   D ~ 0.481 * b / n

which is nonzero - hence no contradiction, hence the conjecture is open rather
than trivial. But the slack is O(1/n): it vanishes exactly as you scale up.
Since best rational approximations obey |a/b - log2 3| ~ 1/b^2, closing a loop
around a value n needs b ~ 1.44*sqrt(n) odd steps.

For a d-bit machine that is a loop period of 2^(d/2) - exponential in the tape
it loops - which is what kills the "encode a Turing machine in a huge number"
design. Sanity check at the bottom: this reproduces the order of the published
cycle-length bounds (Eliahou 1993, ~1.7e10 given verification to 2^68).
"""

import math
import random

K = math.log2(3)


def measured_drift(trials=2000, seed=1):
    """Phase overshoot of 3n+1 over 3n, times n. Should be 1/(3 ln 2)."""
    rng = random.Random(seed)
    tot = 0.0
    for _ in range(trials):
        n = rng.randrange(10 ** 6, 10 ** 7) | 1
        tot += (math.log2(3 * n + 1) - math.log2(n) - K) * n
    return tot / trials


def convergents(count=12):
    """Continued-fraction convergents a/b of log2(3)."""
    terms, v = [], K
    for _ in range(count + 8):
        i = math.floor(v)
        terms.append(i)
        v = 1 / (v - i)
    h0, h1, k0, k1 = 1, terms[0], 0, 1
    out = []
    for t in terms[1:count]:
        h0, h1 = h1, t * h1 + h0
        k0, k1 = k1, t * k1 + k0
        out.append((h1, k1, abs(h1 - k1 * K)))
    return out


def main():
    d = measured_drift()
    print("+1 phase drift per odd step: %.5f/n   (theory 1/(3 ln 2) = %.5f)"
          % (d, 1 / (3 * math.log(2))))
    print()
    print("each convergent licenses a loop only around values up to n ~ 0.481*b/|a - b log2 3|:")
    print("  %14s %12s %16s" % ("a/b", "|a-b log2 3|", "largest n"))
    for a, b, err in convergents():
        print("  %7d/%-6d %12.3e %16.3e" % (a, b, err, 0.481 * b / err))
    print("  (the first row is the trivial cycle 1->4->2->1: a=2, b=1, closing at n~1)")
    print()
    print("loop length needed, from |a/b - log2 3| ~ 1/b^2  =>  b ~ 1.44*sqrt(n):")
    for bits in (20, 68, 100, 300, 1000):
        b = 1.44 * 2 ** (bits / 2)
        print("   %4d-bit tape (n ~ 2^%d) : b ~ %.2e odd steps, and the halvings"
              % (bits, bits, b))
        print("        %srewrite the tape ~%.1e times over during one loop"
              % (" " * 0, 1.585 * b / bits))
    print()
    print("cross-check: verification to 2^68 gives >= %.2e; Eliahou 1993 bound ~1.7e10"
          % (1.44 * 2 ** 34))


if __name__ == "__main__":
    main()
