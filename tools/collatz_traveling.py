#!/usr/bin/env python3
"""Patterns that spread left: rigid traveling crystals.

Run: python3 tools/collatz_traveling.py

Earlier notes claimed every disturbance in this automaton spreads at log2(3) and
nothing keeps its shape while moving. That is true of a *defect* against a
background, but it is not the whole story. There is an exact family of
shape-preserving traveling waves, and some of them move LEFT (toward the MSB).

A crystal with denominator d rigidly translates iff 3 is a power of 2 modulo d:

    3 == 2^k  (mod d)   =>   3 * (a/d)  and  2^k * (a/d)  differ by an integer

so the tail X/(2^p - 1) with denominator d is, after one x3 step, EXACTLY itself
shifted left by k bits. No dispersion, no reshaping - a rigid glider of velocity
k cells/step. The direction is set by where k sits in the period p = ord_d(2):
k <= p/2 reads as a right shift, k > p/2 as a left shift (net = k - p).

Examples (all verified below by running them):

    d=5   p=4    +3  ==  right 1/step
    d=13  p=12   +4  ==  LEFT  4/step
    d=25  p=20   +7  ==  LEFT  7/step
    d=29  p=28   +5  ==  LEFT  5/step
    d=61  p=60   +6  ==  LEFT  6/step

58 denominators below 400 translate. They are the shift-eigenvectors of the
multiply-by-3 map: the discrete-log condition dlog_2(3) mod d existing at all.

This does NOT contradict the log2(3) dispersion result. A localized DEFECT on
any background still spreads at log2(3); what travels rigidly here is the whole
periodic crystal, an exact eigenvector rather than a perturbation. The open
question - a LOCALIZED left-moving packet, a Rule-110-style glider against a
crystal ether - is left for the handoff at the end of COLLATZ.md.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


def ord2(d):
    k, x = 1, 2 % d
    while x != 1:
        x = x * 2 % d
        k += 1
    return k


def dlog2_of_3(d):
    """Smallest k with 2^k == 3 (mod d), or None if 3 is not a power of 2."""
    x = 2 % d
    for k in range(1, ord2(d) + 1):
        if x == 3 % d:
            return k
        x = x * 2 % d
    return None


def travelers(dmax=400):
    out = []
    for d in range(5, dmax, 2):
        if d % 3 == 0:
            continue
        k = dlog2_of_3(d)
        if k is None:
            continue
        p = ord2(d)
        net = k if k <= p // 2 else k - p
        out.append((d, p, k, net))
    return out


def strip(d, width, steps):
    """A width-cell window of the crystal over `steps` steps (cells stay square)."""
    p = ord2(d)
    M = (1 << p) - 1
    x = M // d
    rows = []
    for _ in range(steps):
        rows.append([(x >> (i % p)) & 1 for i in range(width)])
        x = (3 * x) % M
    return np.array(rows), p


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    allt = travelers()
    print("rigid traveling crystals - 3 is a power of 2 mod d, so the crystal")
    print("shifts by a fixed number of cells every step, forever:")
    print("   %4s %4s %6s %10s %s" % ("d", "p", "shift", "net/step", "direction"))
    for d, p, k, net in allt[:16]:
        print("   %4d %4d %6d %10d %s"
              % (d, p, k, net, "LEFT" if net > 0 else "right"))
    print("   ... %d translating denominators below 400" % len(allt))
    print()

    # verify a left mover explicitly
    d = 13
    p = ord2(d)
    M = (1 << p) - 1
    x = M // d
    k = dlog2_of_3(d)
    print("verify d=13 (left %d/step):" % k)
    for t in range(4):
        print("   t=%d  %s" % (t, format(x, "0%db" % p)))
        x = (3 * x) % M
    print()

    # net = k or k-p; imshow x runs MSB(left)->LSB(right), so a LEFT (MSB-ward)
    # move means the pattern advances toward smaller column index, slope -net.
    panels = [(5, "#ffb347", "d=5:  RIGHT 1/step"),
              (11, "#c9a0ff", "d=11: RIGHT 2/step"),
              (29, "#4fd1ff", "d=29: LEFT 5/step"),
              (61, "#ff5c8a", "d=61: LEFT 6/step")]
    W, STEPS = 80, 56
    fig, axs = plt.subplots(1, 4, figsize=(22, 7), dpi=145)
    for ax, (d, colour, title) in zip(axs, panels):
        img, p = strip(d, W, STEPS)
        net = [n for dd, _, _, n in allt if dd == d][0]
        ax.imshow(img, cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        t = np.arange(STEPS)
        x0 = W // 2
        ax.plot(x0 - net * t, t, color="#ff2d6f", lw=2.0, alpha=0.9)
        ax.set_xlim(-0.5, W - 0.5)
        ax.set_ylim(STEPS - 0.5, -0.5)
        ax.set_title("%s\nperiod %d, slope %+d cells/step"
                     % (title, p, net), fontsize=12)
        ax.set_xlabel("ring cell (MSB left)")
        ax.set_ylabel("step")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("shape-preserving traveling crystals: patterns that spread left "
                 "at a rational velocity (pink line = the exact velocity)",
                 fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-traveling.png"), facecolor="white")
    plt.close(fig)
    print("wrote images/collatz-traveling.png")


if __name__ == "__main__":
    main()
