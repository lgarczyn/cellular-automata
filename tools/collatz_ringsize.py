#!/usr/bin/env python3
"""Ring size decides everything - until the parity branch throws it away.

Run: python3 tools/collatz_ringsize.py [WMAX]      (default 24)

On the cyclic ring the modulus is 2^W - 1, so the ring size controls the
arithmetic the universe is built from. Two extremes:

  W prime with 2^W - 1 a Mersenne prime (W = 17, 19): the branchless affine map
  x -> 3x + 1 has exactly TWO orbits, one of them covering the entire state
  space - 131070 of 131071 states, a single maximal cycle. A perfect clock.

  W heavily factorable (W = 24, 2^W - 1 = 3^2*5*7*13*17*241, 96 divisors):
  the same map shatters into 8394 separate orbits, longest only 240. That is
  the CRT decomposition made visible - the state splits into independent
  components, one per prime power, each cycling on its own period. Independent
  components are exactly what a machine needs for registers.

So the ring size is a genuine knob, running from "one giant clock" at the prime
end to "thousands of independent registers" at the composite end.

Then turn the Collatz parity branch back on and BOTH ends collapse to 3-5
cycles, for every W, prime or not. The reason is one line: the modulus is odd,
so a residue mod any factor of 2^W - 1 carries no information about the parity
of the representative. The branch reads a bit that is invisible to every CRT
component, and couples all of them through it. It is a global broadcast no part
of the decomposition can see coming, and it re-randomises the whole state.

Which is the sharpest statement of the obstruction found anywhere in this
investigation: the algebra of the ring offers exactly the independent parts a
machine would need, and the parity branch - the thing that makes Collatz
Collatz rather than plain multiplication - is precisely what destroys them.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


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


def n_divisors(n):
    p = 1
    for e in factor(n).values():
        p *= e + 1
    return p


def is_prime(k):
    return k > 1 and all(k % i for i in range(2, int(k ** 0.5) + 1))


def cycles_of(f):
    """All cycle lengths of a functional graph, via pointer doubling."""
    N = len(f)
    h = f.copy()
    for _ in range(int(np.ceil(np.log2(N))) + 1):
        h = h[h]
    seen = np.zeros(N, bool)
    lengths = []
    for s in np.unique(h):
        if seen[s]:
            continue
        c, x = 0, s
        while not seen[x]:
            seen[x] = True
            x = f[x]
            c += 1
        lengths.append(c)
    return lengths


def maps(W):
    """The branchless affine ring map, and the Collatz branch map, on 2^W - 1."""
    M = (1 << W) - 1
    x = np.arange(M + 1, dtype=np.int64)
    affine = ((3 * x + 1) % M).astype(np.int64)
    r = 3 * x + 1
    for _ in range(3):
        r = np.where(r > M, (r & M) + (r >> W), r)
    collatz = np.where((x & 1) == 1, r, x >> 1)
    return affine, collatz, M


def main():
    wmax = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    rows = []
    print("%3s %5s %9s %8s %26s %22s"
          % ("W", "prime", "2^W-1", "divisors", "branchless x->3x+1", "with parity branch"))
    for W in range(6, wmax + 1):
        aff, col, M = maps(W)
        ca, cc = cycles_of(aff), cycles_of(col)
        rows.append((W, is_prime(W), M, n_divisors(M), len(ca), max(ca), len(cc), max(cc)))
        print("%3s %5s %9d %8d %10d cyc, max %7d %8d cyc, max %5d"
              % (W, "P" if is_prime(W) else ".", M, n_divisors(M),
                 len(ca), max(ca), len(cc), max(cc)))

    print()
    print("why the branch erases it: 2^W - 1 is odd, so x mod (any factor) says")
    print("nothing about the parity of x. the branch reads a bit invisible to every")
    print("CRT component and couples all of them through it.")

    W = np.array([r[0] for r in rows])
    prime = np.array([r[1] for r in rows])
    M = np.array([r[2] for r in rows], float)
    ndiv = np.array([r[3] for r in rows])
    ca, maxa = np.array([r[4] for r in rows]), np.array([r[5] for r in rows], float)
    cc, maxc = np.array([r[6] for r in rows]), np.array([r[7] for r in rows], float)

    fig, axs = plt.subplots(1, 3, figsize=(21, 6.5), dpi=145)
    ax = axs[0]
    ax.scatter(ndiv[~prime], ca[~prime], s=70, c="#5470c6", label="W composite")
    ax.scatter(ndiv[prime], ca[prime], s=90, c="#d03020", marker="D", label="W prime")
    for w, d, c in zip(W, ndiv, ca):
        ax.annotate(str(w), (d, c), fontsize=8, xytext=(4, 3), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("divisors of 2^W - 1")
    ax.set_ylabel("number of orbits")
    ax.legend()
    ax.set_title("branchless: more factors -> more independent parts")

    ax = axs[1]
    ax.plot(W, maxa / M, "o-", c="#5470c6", label="branchless x->3x+1")
    ax.plot(W, maxc / M, "s-", c="#d03020", label="with parity branch")
    for w, f in zip(W, maxa / M):
        if f > 0.9:
            ax.annotate("W=%d" % w, (w, f), fontsize=9, xytext=(-8, -14), textcoords="offset points")
    ax.set_yscale("log")
    ax.set_xlabel("ring size W")
    ax.set_ylabel("longest orbit / state space")
    ax.legend()
    ax.set_title("Mersenne-prime rings give one maximal orbit")

    ax = axs[2]
    ax.scatter(ndiv[~prime], cc[~prime], s=70, c="#5470c6", label="W composite")
    ax.scatter(ndiv[prime], cc[prime], s=90, c="#d03020", marker="D", label="W prime")
    ax.set_xscale("log")
    ax.set_ylim(0, 8)
    ax.set_xlabel("divisors of 2^W - 1")
    ax.set_ylabel("number of orbits")
    ax.legend()
    ax.set_title("with the parity branch: 3-5 orbits, whatever the ring")

    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-ringsize.png"), facecolor="white")


if __name__ == "__main__":
    main()
