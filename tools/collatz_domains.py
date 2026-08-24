#!/usr/bin/env python3
"""Can two crystals coexist side by side, with a wall between them? No - and
this is exhaustive, not a failed search.

Run: python3 tools/collatz_domains.py [W]      (default 20; 24 takes ~4 min)

The persistent states can be enumerated exactly rather than sampled. A state has
period dividing T exactly when (3^T - 1)x = 0 mod M, i.e. when x is a multiple
of M / gcd(M, 3^T - 1). Take T to be the lcm of every achievable period and that
enumerates EVERY state on a cycle - the complete population of things that
persist at all.

Then, for each one, take the union of its support over its whole orbit. Cells
outside that union are permanently empty for that structure: they are the only
places a domain wall could ever live. Measure the longest contiguous run of them.

    W = 20 : all 349,525 cycle states -> longest permanent gap = 1 cell
    W = 24 : all 1,864,135 cycle states -> longest permanent gap = 1 cell

One cell. Across every persistent structure that exists in these rings, the
widest stretch of vacuum any of them ever leaves open is a single cell. Some of
them are genuinely inhomogeneous - local periodicity varies around the ring, and
some look like a compact blob in a sea of zeros - but the empty cells always come
as isolated holes inside a pattern (`##.###.###.###`), never as a region.

A domain wall needs somewhere to be, and there is nowhere. Juxtapose any two
crystals by hand and the wall radiates on the very first step, with no nearby
persistent state to relax into - because every persistent state is spread across
the entire ring by construction.

So the medium supports superposition (two structures in the same cells, exactly
independent) but not adjacency (two structures in different cells). That is the
whole obstruction in one sentence.
"""

import sys
from math import gcd, lcm


def factor(n):
    f, d = {}, 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def order(a, m):
    k, x = 1, a % m
    while x != 1:
        x = x * a % m
        k += 1
    return k


def max_period(M):
    """lcm of every achievable period on this ring."""
    T = 1
    for q, e in factor(M).items():
        if q != 3:
            T = lcm(T, order(3, q ** e))
    return T


def orbit_union(x, M):
    u, y = 0, x
    while True:
        u |= y
        y = (3 * y) % M
        if y == x:
            break
    return u


def longest_gap(u, W):
    s = [(int(u) >> i) & 1 for i in range(W)] * 2
    best = run = 0
    for v in s:
        run = 0 if v else run + 1
        best = max(best, run)
    return min(best, W)


def show(x, W):
    return "".join("#" if (int(x) >> i) & 1 else "." for i in range(W))


def main():
    W = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    M = (1 << W) - 1
    T = max_period(M)
    g = gcd(M, 3 ** T - 1)
    D = M // g

    print("ring W = %d, modulus %d" % (W, M))
    print("every achievable period divides Tmax = %d, so the cycle states are" % T)
    print("exactly the %d multiples of M/gcd(M, 3^Tmax - 1) = %d." % (g, D))
    print("enumerating all of them and measuring permanent vacuum:")

    best, arg = 0, None
    for i in range(1, g):
        x = (i * D) % M
        gap = longest_gap(orbit_union(x, M), W)
        if gap > best:
            best, arg = gap, x
    print("   longest contiguous permanently-empty region: %d cell%s"
          % (best, "" if best == 1 else "s"))
    if arg is not None:
        print("   widest example, its orbit union: %s" % show(orbit_union(arg, M), W))
    print("   (empty cells come as isolated holes inside a pattern, never a region)")
    print()

    R3 = M // ((1 << 3) - 1)
    R4 = M // ((1 << 4) - 1)
    b3 = [(R3 >> i) & 1 for i in range(W)]
    b4 = [(R4 >> i) & 1 for i in range(W)]
    mix = 0
    for i in range(W):
        mix |= (b3[i] if i < W // 2 else b4[i]) << i
    print("juxtaposing a period-3 and a period-4 crystal by hand:")
    print("   t=0  %s   persistent? %s" % (show(mix, W), mix % D == 0))
    y = mix
    for t in range(1, 5):
        y = (3 * y) % M
        print("   t=%d  %s" % (t, show(y, W)))
    print()
    print("the wall radiates immediately, and there is no persistent state nearby to")
    print("fall into. superposition works; adjacency does not.")


if __name__ == "__main__":
    main()
