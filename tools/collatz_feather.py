#!/usr/bin/env python3
"""The Collatz tree drawn as geometry (Edmund Harriss style).

Run: python3 tools/collatz_feather.py [N] [OUT]    (defaults: 40000, images/collatz-feather.png)

Every trajectory is drawn backwards from 1, one unit-length segment per step,
turning a little to the left for each halving and a little to the right for
each 3n+1. Trajectories that share a tail (almost all of them) trace the same
initial curve and split where their histories diverge, so the tree structure
becomes literal branches. The turn angles are chosen so the average drift is
near zero: about 64% of steps are halvings, so 0.13 * 0.64 ~ 0.2315 * 0.36.

Colour is trajectory length (plasma), drawn dim-to-bright so the long
filaments glow on top of the dense purple body.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

A_EVEN = 0.13        # left turn per halving (radians)
A_ODD = -0.2315      # right turn per 3n+1


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 40_000
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "images", "collatz-feather.png")

    paths, lengths = [], []
    for n0 in range(3, n_max, 2):
        seq = []
        x = n0
        while x != 1:
            seq.append(x & 1)
            x = 3 * x + 1 if x & 1 else x // 2
        seq.reverse()                      # walk outward from 1
        ang = np.pi / 2 + np.cumsum([A_ODD if p else A_EVEN for p in seq])
        px = np.concatenate(([0], np.cumsum(np.cos(ang))))
        py = np.concatenate(([0], np.cumsum(np.sin(ang))))
        paths.append((px, py))
        lengths.append(len(seq))
    lengths = np.array(lengths, float)

    fig, ax = plt.subplots(figsize=(18, 18), dpi=150)
    fig.patch.set_facecolor("#07070f")
    ax.set_facecolor("#07070f")
    cmap = plt.cm.plasma
    lo, hi = lengths.min(), lengths.max()
    for i in np.argsort(lengths):          # short (dim) first, long (bright) on top
        c = cmap(0.1 + 0.85 * (lengths[i] - lo) / (hi - lo))
        ax.plot(paths[i][0], paths[i][1], color=c, lw=0.55, alpha=0.05,
                solid_capstyle="round")
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(out, facecolor=fig.get_facecolor())
    print("drew %d trajectories, longest %d steps -> %s" % (len(paths), int(hi), out))


if __name__ == "__main__":
    main()
