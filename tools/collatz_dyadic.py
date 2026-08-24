#!/usr/bin/env python3
"""The fractal, found: the residual is self-affine on the 2-adic integers.

Run: python3 tools/collatz_dyadic.py [BITS]     (default 24: n < 2^24)

Zooming into the *magnitude* of n showed no self-similarity - dashes are the
same size at 10^6 and 10^9. But the residual z = b - 2.4 log2 n is driven by
the trajectory's parity sequence, and the first k parity decisions depend only
on n mod 2^k. So z is naturally a function on the 2-adic integers, and the way
to see that is to order n by *reversed* bits, which puts numbers with the same
low bits next to each other.

In that ordering the residual is genuinely self-affine, by construction:
steps(2n) = steps(n) + 1 leaves b unchanged, so the map n -> 2n acts as

    x -> x/2,   z -> z - log2 3  (up to the detrending constant, 2.4008)

i.e. the left half of the picture is an exact copy of the whole, translated
down. Recursively, at every dyadic scale. The conditional-mean curve
E[z | first k bits of n] is a Takagi-style self-affine curve: each extra bit
of n explains the same ~1% slice of the residual's variance (measured 1.0%/bit,
linear from k=1 to k=16, no saturation - equal energy per dyadic level).

So the quasicrystal lives in log n, and the fractal lives in 2-adic n.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collatz import IMAGES, decode_recipe, steps

TREND = 2.4008          # measured growth of b per doubling of n (1/log2(4/3) = 2.4094)


def bitrev(v, k):
    out = np.zeros_like(v)
    x = v.copy()
    for _ in range(k):
        out = (out << 1) | (x & 1)
        x >>= 1
    return out


def conditional_mean(n, z, k):
    """E[z | n mod 2^k], indexed by residue."""
    r = (n & ((1 << k) - 1)).astype(np.int64)
    su = np.zeros(1 << k)
    c = np.zeros(1 << k)
    np.add.at(su, r, z)
    np.add.at(c, r, 1)
    return su / np.maximum(c, 1)


def main():
    bits = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    n_max = 1 << bits
    os.makedirs(IMAGES, exist_ok=True)

    n = np.arange(1, n_max, dtype=np.int64)
    s = np.asarray(steps(n_max)[:n_max - 1], np.int64)
    log2n = np.log2(n.astype(np.float64))
    _, b = decode_recipe(s, log2n)
    z = b - TREND * log2n

    print("variance of residual explained by n mod 2^k (equal energy per level):")
    tot = z.var()
    for k in (1, 2, 4, 8, 12, 16):
        mu = conditional_mean(n, z, k)
        r = (n & ((1 << k) - 1)).astype(np.int64)
        print("   k=%2d : %5.1f%%" % (k, 100 * ((mu[r] - z.mean()) ** 2).mean() / tot))

    depth = min(14, bits - 4)
    m = conditional_mean(n, z, depth)
    mc = m[np.argsort(bitrev(np.arange(1 << depth, dtype=np.int64), depth))]
    x = np.arange(1 << depth) / (1 << depth)

    print("self-affinity: dyadic zoom vs whole curve (range of curve ~%.0f):" % (mc.max() - mc.min()))
    for lvl in (1, 2, 4):
        seg = mc[:(1 << depth) >> lvl] + TREND * lvl        # left 2^-lvl, lifted
        whole = mc.reshape(-1, 1 << lvl).mean(1)            # whole at matching resolution
        print("   zoom x%-2d : mean diff %+0.3f  sd %.3f" % (2 ** lvl, (seg - whole).mean(), (seg - whole).std()))

    fig, axs = plt.subplots(1, 3, figsize=(23, 7), dpi=145)
    axs[0].plot(x, mc, lw=0.35, color="#202070")
    axs[0].set_title("the residual as a function on the 2-adic integers")
    axs[0].set_xlabel("bit-reversed n  (2-adic ordering)")

    axs[1].plot(x, mc, lw=0.5, color="#202070", label="whole curve")
    axs[1].plot(np.arange(1 << (depth - 1)) / (1 << (depth - 1)), mc[:1 << (depth - 1)] + TREND,
                lw=0.5, color="#d03020", alpha=0.75, label="left half, stretched x2, +2.4")
    axs[1].legend(fontsize=10)
    axs[1].set_title("affine self-similarity: n -> 2n is x -> x/2, z -> z - 2.4")
    axs[1].set_xlabel("bit-reversed n")

    for sc, col in [(1, "#202070"), (4, "#d03020"), (16, "#108040")]:
        seg = mc[:(1 << depth) // sc]
        axs[2].plot(np.arange(len(seg)) / len(seg), seg + TREND * np.log2(sc),
                    lw=0.45, color=col, alpha=0.8, label="zoom x%d, lifted %.1f" % (sc, TREND * np.log2(sc)))
    axs[2].legend(fontsize=10)
    axs[2].set_title("cascade: every dyadic zoom is the same curve")
    axs[2].set_xlabel("bit-reversed n")

    for ax in axs:
        ax.set_ylabel("E[residual | first %d bits]" % depth)
    fig.tight_layout()
    fig.savefig(os.path.join(IMAGES, "collatz-dyadic.png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
