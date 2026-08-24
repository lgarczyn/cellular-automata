#!/usr/bin/env python3
"""The bulk: crystal phases exist, propagating excitations do not.

Run: python3 tools/collatz_bulk.py

The ring is a simulation WINDOW, not the universe - periodic boundaries used to
study the bulk of a much larger automaton, the way a lattice simulation does.
That changes what to model. The halving happens at the LSB, far outside the
window; from inside the bulk you only ever see multiplication by 3 with carries
streaming through, plus a uniform drift. So the branchless ring is not a
degenerate special case, it is the correct bulk model - and it is the one with
the rich structure.

Two things follow, one positive and one not.

POSITIVE - the bulk has ordered phases. In a ring of size W, states of spatial
period p (for any p dividing W) are EXACTLY invariant under x3: a period-p
state is X * (2^W-1)/(2^p-1), and tripling it gives 3X mod (2^p - 1) in the
same form. Verified here for p = 3, 5, 8 over hundreds of steps. These are the
CRT components of collatz_ringsize.py seen as spatial order rather than
algebra: one crystal phase per divisor of W, each an invariant subring, each a
perfectly stable structure that persists forever.

NEGATIVE - there are no quasiparticles. Put two phases side by side and the
domain wall between them does not hold together: it disperses at the same rate
as an isolated single-bit defect (measured side by side below, both saturating
near half the ring). The wedges in the figure are light cones, not trajectories.

So the medium supports order but not signals. You can build a region that
remembers a state indefinitely - that is genuine memory - but you cannot send
anything from one region to another, because every disturbance spreads at
log2(3) instead of travelling. Storage without communication, which is the one
combination that cannot be assembled into a machine.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

W = 240
M = (1 << W) - 1


def mul3(x):
    v = 3 * int(x)
    while v > M:
        v = (v & M) + (v >> W)
    return v


def phase(p, block):
    """A spatially period-p state: `block` repeated W/p times."""
    x = 0
    for i in range(W // p):
        x |= (int(block) % (1 << p)) << (i * p)
    return x


def bits(x):
    return [(int(x) >> i) & 1 for i in range(W)]


def check_invariant(p, block, steps=300):
    x = phase(p, block)
    for _ in range(steps):
        x = mul3(x)
        b = bits(x)
        if any(b[i] != b[i % p] for i in range(W)):
            return False
    return True


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    print("crystal phases - states of spatial period p, for p dividing W=%d:" % W)
    for p, blk in ((3, 0b011), (5, 0b01101), (6, 0b010011), (8, 0b10110101)):
        print("   period %d stays period %d under x3 for 300 steps: %s"
              % (p, p, check_invariant(p, blk)))
    print("   (a period-p state is X*(2^W-1)/(2^p-1); tripling gives 3X mod 2^p-1,")
    print("    same form - an exactly invariant subring, one per divisor of W)")
    print()

    A, B = phase(3, 0b011), phase(5, 0b01101)
    bA, bB = bits(A), bits(B)
    mix = 0
    for i in range(W):
        mix |= int(bA[i] if i < W // 2 else bB[i]) << i

    T = 200
    a, b, c = A, B, mix
    raw, dif, wall = [], [], []
    for _ in range(T):
        ba, bb, bc = bits(a), bits(b), bits(c)
        ref = [ba[i] if i < W // 2 else bb[i] for i in range(W)]
        raw.append(bc)
        d = [1 if bc[i] != ref[i] else 0 for i in range(W)]
        dif.append(d)
        wall.append(sum(d))
        a, b, c = mul3(a), mul3(b), mul3(c)

    a2, c2 = A, A ^ (1 << 120)
    point = []
    for _ in range(T):
        point.append(sum(1 for i, j in zip(bits(a2), bits(c2)) if i != j))
        a2, c2 = mul3(a2), mul3(c2)

    print("does a domain wall hold together? (cells disturbed)")
    print("   %6s %14s %14s" % ("step", "domain wall", "1-bit defect"))
    for t in (4, 16, 64, 128, 199):
        print("   %6d %14d %14d" % (t, wall[t], point[t]))
    print("   both disperse at the same rate and saturate near W/2 = %d" % (W // 2))

    fig, axs = plt.subplots(1, 2, figsize=(18, 9), dpi=150)
    axs[0].imshow(np.array(raw), cmap=ListedColormap(["#0b0b14", "#7ee6a0"]),
                  interpolation="nearest")
    axs[0].set_title("two crystal phases (period 3 | period 5) under x3", fontsize=13)
    axs[1].imshow(np.array(dif), cmap=ListedColormap(["#0b0b14", "#ff5c8a"]),
                  interpolation="nearest")
    axs[1].set_title("deviation from the pure phases: the walls disperse", fontsize=13)
    for ax in axs:
        ax.set_xlabel("ring cell")
        ax.set_ylabel("step")
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-bulk.png"), facecolor="white")


if __name__ == "__main__":
    main()
