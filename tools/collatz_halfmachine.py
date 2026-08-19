#!/usr/bin/env python3
"""Can the left edge be influenced at all? Yes - and exactly 1/(3n) worth.

Run: python3 tools/collatz_halfmachine.py

Two questions the machine thread reduces to.

1. The trivial cycle 1->4->2->1 proves the MSB edge CAN be influenced: a pure
   *3 advances the edge by log2(3) = 1.58496 columns, but 3*1+1 = 4 advances it
   by exactly 2. The +1 supplied 0.41504 columns of phase - precisely the
   deficit 2 - log2(3). The loop closes because the phase landed on an integer.

   But the influence of one +1 is log2(1 + 1/(3n)) columns, i.e. ~0.481/n. It
   is set by the number's MAGNITUDE, not by its bits, so the tape cannot
   modulate it. At n=1 it is 0.415 (everything you need) because the LSB and
   the MSB are the same bit. At n = 2^64 it is 10^-20. The attenuation factor
   is exactly the size of the tape you wanted to build.

2. A "half machine" - a looping right side, left edge free - is not merely
   possible, it is fully solved, and the answer is a classical theorem. The
   parity-vector map is a homeomorphism of the 2-adic integers conjugating the
   Collatz map to the plain shift (Lagarias 1985), so EVERY periodic parity
   sequence is realised by exactly one 2-adic number. Prescribe any right-side
   loop you like and this script hands you the number that performs it.

   That number is always C/(2^a - 3^b). The right side loops perfectly; being a
   positive integer is the separate condition, and it is the same Diophantine
   wall as before. Among all prescribed loops up to 4 odd steps, exactly one
   positive integer appears: n = 1.
"""

import itertools
import math
from fractions import Fraction

K = math.log2(3)


def realize(halvings):
    """The unique number whose parity sequence is (odd step, v halvings)*, repeated.

    Tracks n -> a*n + b through one period, then solves a*n + b = n.
    """
    a, b = Fraction(1), Fraction(0)
    for v in halvings:
        a, b = 3 * a, 3 * b + 1
        for _ in range(v):
            a, b = a / 2, b / 2
    if a == 1:
        return None
    return b / (1 - a), sum(halvings), len(halvings)


def main():
    print("1. the trivial cycle shows the left edge IS influenced")
    print("   pure *3 advances the MSB edge by log2(3)      = %.5f columns" % K)
    print("   3*1+1 = 4 advances it by log2(4)              = %.5f columns" % 2.0)
    print("   the +1 supplied log2(4/3)                     = %.5f" % math.log2(4 / 3))
    print("   the deficit that had to be covered, 2 - log2 3 = %.5f  <- exactly equal" % (2 - K))
    print()
    print("   but that influence is log2(1 + 1/(3n)) per step, set by size alone:")
    for n in (1, 3, 27, 255, 2 ** 16 - 1, 2 ** 32 - 1):
        print("     n = %-12d : %.3e columns  (%.5f needed)" % (n, math.log2(1 + 1 / (3 * n)), 2 - K))
    print("   at n=1 the LSB and MSB are the same bit, so a right-edge event moves")
    print("   the left edge undiluted. attenuation is 1/(3n): the size of the tape.")
    print()

    print("2. prescribe any right-side loop; here is the number that performs it")
    print("   %-22s %14s %12s %s" % ("halving pattern", "n", "2^a - 3^b", "positive integer?"))
    for h in ([2], [1], [3], [4], [2, 2], [1, 2], [3, 1], [2, 1, 2], [1, 1, 1], [5], [2, 3], [4, 2, 1]):
        r = realize(h)
        if r is None:
            continue
        n, a, b = r
        ok = "YES" if n.denominator == 1 and n > 0 else ("negative" if n < 0 else "no")
        print("   %-22s %14s %12d %s" % (h, n, 2 ** a - 3 ** b, ok))

    total = hits = 0
    for length in range(1, 5):
        for h in itertools.product(range(1, 5), repeat=length):
            r = realize(list(h))
            if r is None:
                continue
            total += 1
            if r[0].denominator == 1 and r[0] > 0:
                hits += 1
    print()
    print("   of %d prescribed loops up to 4 odd steps, %d are positive integers" % (total, hits))
    print("   (always the same one: n = 1)")
    print()
    print("   so the half machine exists - as a rational. every right-side loop is")
    print("   realisable in Z_2; requiring the carrier to be a positive integer of")
    print("   machine size is the same Diophantine wall the full machine hit.")


if __name__ == "__main__":
    main()
