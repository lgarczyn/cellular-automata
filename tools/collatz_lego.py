#!/usr/bin/env python3
"""The LEGO CRYSTAL. SCOPE: [ring: looped MSB, x3].

Lou's spec: a looping crystal (like collatz-immortal.png) whose repeating unit
contains TWO structures plus boundary layers, composable like legos.

Construction: bricks are width-6 blocks with v3 >= 2 (the persistence quota for
L=6; all such bricks share ONE charge class, so every assembly persists).
  A = 010010 (sparse), B = 101101 (dense), | = 111111 (wall).
Unit cell U = |A|B| (24 cells), tiled 4x on a 96-cell ring. Verified:
  - every one of the 480 rendered rows is a perfect period-24 spatial crystal
  - the whole state returns exactly after 240 steps (temporal loop)
  - reassemblies |A|A|B| and |A|B|B| of the same bricks also persist
    (period 108 on their rings): the bricks are true legos.
Run: python3 tools/collatz_lego.py  ->  images/collatz-lego.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
A, B, J = 0b010010, 0b101101, 0b111111


def word(bricks, L=6):
    X = 0
    for i, b in enumerate(bricks):
        X |= b << (L * i)
    return X, L * len(bricks)


def period(X, W):
    M = (1 << W) - 1
    y, k = (3 * X) % M, 1
    while y != X:
        y = (3 * y) % M
        k += 1
    return k


def main():
    U, u = word([J, A, J, B])
    X, W = 0, 0
    for i in range(4):
        X |= U << (u * i)
    W = 4 * u
    M = (1 << W) - 1
    T = period(X, W)
    H = 2 * T
    img = np.zeros((H, W), np.int8)
    x, sp = X, 0
    for r in range(H):
        for c in range(W):
            img[r, c] = (x >> (W - 1 - c)) & 1
        if all(((x >> i) & 1) == ((x >> ((i + u) % W)) & 1) for i in range(W)):
            sp += 1
        x = (3 * x) % M
    print("period %d; rows that are perfect period-%d crystals: %d/%d" % (T, u, sp, H))
    for name, seq in [("|A|A|B|", [J, A, J, A, J, B]), ("|A|B|B|", [J, A, J, B, J, B])]:
        Xa, Wa = word(seq)
        print("reassembly %s: ring %d, period %d (persists)" % (name, Wa, period(Xa, Wa)))

    fig = plt.figure(figsize=(13, 16), dpi=140)
    ax = fig.add_axes([0.07, 0.04, 0.9, 0.75])
    ax.imshow(img, cmap=ListedColormap(["#0b0b14", "#39d353"]), vmin=0, vmax=1,
              interpolation="nearest", aspect="auto")
    for i in range(0, W + 1, u):
        ax.axvline(i - 0.5, color="#ffffff", lw=1.4, alpha=0.85)
    ax.axhline(T - 0.5, color="#ff2d6f", lw=2)
    ax.set_xlabel("ring cell (MSB left); thick lines = unit-cell boundaries")
    ax.set_ylabel("step")
    ax.set_yticks([0, T, 2 * T])
    ax.set_xticks([])
    axz = fig.add_axes([0.07, 0.86, 0.9, 0.06])
    zoom = np.concatenate([img[:5], np.full((1, W), 0.5), img[T:T + 5]], axis=0)
    axz.imshow(zoom, cmap=ListedColormap(["#0b0b14", "#777777", "#39d353"]),
               vmin=0, vmax=1, interpolation="nearest", aspect="auto")
    axz.set_xticks([])
    axz.set_yticks([2, 8])
    axz.set_yticklabels(["steps 0-4", "steps %d-%d" % (T, T + 4)], fontsize=9)
    axz.set_title("proof of loop: first five rows == the five rows one period later\n"
                  "unit cell |A|B|: A=010010, B=101101, wall |=111111", fontsize=11)
    fig.suptitle("[ring: looped MSB, x3] LEGO CRYSTAL: |A|B| tiled 4x on 96 cells;\n"
                 "every row a period-24 crystal, exact loop every %d steps" % T,
                 fontsize=12, y=0.99)
    fig.savefig(os.path.join(IMG, "collatz-lego.png"), facecolor="white",
                bbox_inches="tight")


if __name__ == "__main__":
    main()
