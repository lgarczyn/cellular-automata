#!/usr/bin/env python3
"""Left-moving crystals under the free-MSB boundary condition.

Run: python3 tools/collatz_leftmover.py

Combines the two earlier results. From collatz_traveling.py: a crystal with
denominator d rigidly shifts left k cells/step when 3 == 2^k (mod d). From
collatz_halfopen.py: with a free MSB edge, the state is a real number
v = 3^t * (a0/d) - an integer head plus the fraction a_t/d.

Put them together. The looping tail is a LEFT-moving crystal, and the free head
accumulates the bits the crystal pushes past the binary point:

    tail   a -> 3a mod d          (= a shifted left k bits, a rigid left glider)
    head   H -> 3H + floor(3a/d)  (the carry the left-mover spills upward)

So a coherent left-moving pattern really does exist against a terminating left
edge: the tail crystal slides left at k cells/step, period ord_d(3) in place,
continuously feeding a growing head. The MSB edge of the head marches left at
log2(3) (that is the number growing), while the tail texture underneath it moves
left at the rational rate k.

The one thing still missing for a machine is a LOCALIZED left-mover. A defect
added on top of this background is a perturbation eps with eps -> 3*eps, which
disperses at log2(3) regardless of how fast the crystal beneath it travels - so
the crystal moves rigidly but any bump on it still smears. Finding a bounded
left-moving packet is the open handoff problem in COLLATZ.md.
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
    x = 2 % d
    for k in range(1, ord2(d) + 1):
        if x == 3 % d:
            return k
        x = x * 2 % d
    return None


def run(d, a0, steps, tail_depth, head_width):
    """Rows aligned at the binary point: head (head_width cols) | tail (tail_depth)."""
    p = ord2(d)
    a = a0 % d
    H = 0
    img = np.zeros((steps, head_width + tail_depth), np.uint8)
    edge = []
    for t in range(steps):
        for i in range(head_width):                       # head, MSB on the left
            img[t, head_width - 1 - i] = (H >> i) & 1
        r = a
        for j in range(tail_depth):                       # tail fraction bits
            r *= 2
            img[t, head_width + j] = r // d
            r %= d
        edge.append(head_width - H.bit_length())
        na = 3 * a
        H = 3 * H + na // d
        a = na % d
    return img, np.array(edge), p


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    from math import gcd, log2
    specs = [(13, "#7ee6a0", 4), (29, "#4fd1ff", 5), (61, "#ff5c8a", 6)]
    steps, tail_depth, head_width = 60, 60, 105

    print("left-moving crystals with a free MSB edge (head grows, tail slides left):")
    fig, axs = plt.subplots(1, 3, figsize=(22, 9), dpi=145)
    for ax, (d, colour, k) in zip(axs, specs):
        img, edge, p = run(d, 1, steps, tail_depth, head_width)
        Tp = ord2(d)
        # temporal period of the tail in place
        a, tper = 3 % d, 1
        while a != 1:
            a = a * 3 % d
            tper += 1
        print("   d=%-3d: tail shifts LEFT %d cells/step, period %d in place, "
              "head grows at log2(3)" % (d, k, tper))
        ax.imshow(img, cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        ax.axvline(head_width - 0.5, color="#ffffff", lw=1.5, alpha=0.8)
        t = np.arange(steps)
        ax.plot(edge, t, color="#ffd166", lw=1.6,
                label="MSB edge  (log2 3 = %.2f/step)" % log2(3))
        # tail crystal velocity guide, anchored just right of the point
        ax.plot(head_width + 8 - k * t, t, color="#ff2d6f", lw=1.6,
                label="tail crystal  (%d/step LEFT)" % k)
        ax.set_xlim(-0.5, head_width + tail_depth - 0.5)
        ax.set_ylim(steps - 0.5, -0.5)
        ax.set_title("d=%d: free head (left) | left-moving tail crystal (right)\n"
                     "period %d, tail velocity %d cells/step" % (d, p, k),
                     fontsize=11)
        ax.set_xlabel("bit position (MSB left, binary point = white)")
        ax.set_ylabel("step")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.legend(fontsize=8, loc="lower left")
    fig.suptitle("left-moving crystals under the free-MSB boundary: the tail "
                 "pattern slides left at a rational rate, feeding a growing head",
                 fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-leftmover.png"), facecolor="white")
    plt.close(fig)
    print("wrote images/collatz-leftmover.png")


if __name__ == "__main__":
    main()
