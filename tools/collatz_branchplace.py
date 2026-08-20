#!/usr/bin/env python3
"""Where do you read the parity on a ring? Anywhere - it is still one global bit.

Run: python3 tools/collatz_branchplace.py

Parity needs a distinguished cell, and a ring has none: every cell is
equivalent under rotation. The ring universes in collatz_loopworlds.py quietly
kept bit 0 as "the LSB", so they were not translation-invariant CAs at all -
they were rings with a hidden head bolted on.

Worse, on a ring with end-around carry, HALVING IS ROTATION. Multiplying by 2
is a symmetry of the ring (2^W = 1 mod 2^W - 1, and inv2 is the back-rotation),
so W halvings return exactly where they started. The halvings are not dynamics,
they are a period-W clock. Every bit of the actual dynamics lives in the
branch.

So "where to read the branch" is the whole design, and this script tries the
options on the same ring:

  bit-0 parity     a hidden head - not a CA, a Turing machine on a circular
                   tape. Collapses to 3 orbits.
  popcount parity  genuinely rotation-invariant, and legal, but the condition
                   reads every cell, so there is no locality at all.
  one CRT component  respects the ring's algebra - the control component runs
                   autonomously and drives the rest, a control/registers skew
                   product. Gives the longest orbits found, but the control is
                   only p states wide, so periods stay tiny.
  no branch        the rich CRT structure of collatz_ringsize.py, but then it
                   is plain multiplication, not Collatz.

None of them helps, and the reason is structural rather than a bad choice of
placement. `3n+1` on a ring is `n + rotate(n)` with carries - a GLOBAL
operation on the whole state. So whatever selects it is necessarily global too:
one bit of control, for the entire universe, once per step. You cannot have
part of the ring tripling while another part halves, because tripling is not
something a part can do.

That is the answer to "how would you turn the branch on or off": any way you
like, and it will not matter. A machine needs many independent control
decisions per step; this universe offers exactly one.
"""

import numpy as np
from math import gcd


def cycles_of(f):
    N = len(f)
    h = f.copy()
    for _ in range(int(np.ceil(np.log2(N))) + 1):
        h = h[h]
    seen = np.zeros(N, bool)
    lengths = []
    for s in np.unique(h):
        if seen[s]:
            continue
        c, y = 0, s
        while not seen[y]:
            seen[y] = True
            y = f[y]
            c += 1
        lengths.append(c)
    return sorted(lengths)


def popcount_parity(x):
    return np.array([bin(int(v)).count("1") & 1 for v in x], bool)


def main():
    for W in (15, 21):
        M = (1 << W) - 1
        inv2 = pow(2, -1, M)
        x = np.arange(M + 1, dtype=np.int64)
        up, dn = (3 * x + 1) % M, (x * inv2) % M
        p = next(q for q in (7, 31, 127, 151, 337) if M % q == 0)

        print("ring W=%d, modulus %d, gcd(3,M)=%d" % (W, M, gcd(3, M)))
        print("  halving is rotation: 2 * inv2 = %d mod M, so W halvings = identity"
              % ((2 * inv2) % M))
        options = [
            ("no branch (pure x -> 3x+1)", up),
            ("bit-0 parity (a hidden head)", np.where((x & 1) == 1, up, dn)),
            ("popcount parity (rotation-invariant, global)",
             np.where(popcount_parity(x), up, dn)),
            ("one CRT component (x mod %d)" % p, np.where((x % p) < p // 2, up, dn)),
        ]
        for name, f in options:
            L = cycles_of(f)
            print("   %-46s %6d orbits, longest %8d (%.2f%%)"
                  % (name, len(L), max(L), 100 * max(L) / (M + 1)))
        print()

    print("whichever way you read it, the branch selects ONE map for the WHOLE ring,")
    print("once per step. 3n+1 is n + rotate(n) with carries - a global operation -")
    print("so the branch controlling it is global too. one control bit per step, for")
    print("an entire universe. no architecture builds registers out of that.")


if __name__ == "__main__":
    main()
