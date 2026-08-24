#!/usr/bin/env python3
"""Loop the right edge, give the left edge back: what survives, and at what angle.

Run: python3 tools/collatz_halfopen.py

A configuration that repeats forever to the right and has a free MSB edge on the
left is a REAL NUMBER: an integer head H (bits at positions >= 0) plus a
repeating binary fraction f = X/(2^p - 1) for the crystal tail. One step:

    3f = q + X'/(2^p - 1),   q in {0,1,2}
    tail   X -> 3X mod (2^p - 1)      (exactly the ring dynamics)
    head   H -> 3H + q                (the tail's carry spilling upward)

so the whole configuration at time t is nothing but the real number 3^t * f0
written in binary. Three consequences, all verified below rather than argued.

1. THE LEFT EDGE NEVER TOUCHES THE RIGHT. In x -> 3x carries propagate only from
   LSB towards MSB, so this automaton has a ONE-SIDED light cone. The MSB edge is
   downstream of everything; nothing it does can reach the tail. Every persistent
   pattern survives, forever, unchanged - not "some of them", all of them.

   The lethal edge is the other one. Cut the tail off at depth D instead of
   looping it and the truncation eats upward at log2(3): measured 1.585, 1.587,
   1.583 cells/step for three different crystals. Looping the right edge is
   exactly the move that was needed; looping the left would have been pointless.

2. THE ANGLE IS THE SAME FOR EVERY PATTERN. The MSB sits at
   log2(3^t f0) = t*log2(3) + log2(f0), so the slope is log2(3) = 1.5849625 for
   every crystal without exception - measured across ten of them below. What the
   pattern sets is the OFFSET, and it sets it exactly: the edge's intercept is
   log2(f0) = log2(a/d), the tail's own value as a fraction. Different patterns
   give parallel lines, never converging, never crossing.

3. WHAT GROWS ON THE LEFT IS NOT CHAOS. The carry stream q0 q1 q2 ... is
   literally the base-3 expansion of a/d, so the head is that expansion read as a
   base-3 numeral - and for a rational tail it is periodic. The left region only
   looks like noise because it is being rendered in base 2. Draw it in base 3 and
   it is as ordered as the crystal on the right: two crystals, one in each base,
   with the binary point as the only boundary.
"""

import os
from math import gcd, log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

STEPS = 90
DEPTH = 45


def crystal(p, d, a=1):
    Mp = (1 << p) - 1
    return a * (Mp // d) % Mp


def tail_bit(X, p, j):
    """Bit at depth j >= 1 below the binary point, for f = X/(2^p - 1)."""
    return (X >> (p - 1 - ((j - 1) % p))) & 1


def evolve(p, X, steps):
    """Yields (head, tail, carry) at each step. head grows, tail is a ring state."""
    Mp = (1 << p) - 1
    H, out = 0, []
    for _ in range(steps):
        v = 3 * X
        q, Xn = divmod(v, Mp)
        out.append((H, X, q))
        H, X = 3 * H + q, Xn
    return out


def tail_period(X, Mp):
    T, y = 1, (3 * X) % Mp
    while y != X and T < 10 ** 6:
        y = (3 * y) % Mp
        T += 1
    return T


def picture(p, d, a, steps=STEPS, depth=DEPTH):
    """Rows aligned at the binary point: head to the left, tail to the right."""
    hist = evolve(p, crystal(p, d, a), steps)
    width = max(H.bit_length() for H, _, _ in hist)
    img = np.zeros((steps, width + depth), dtype=np.uint8)
    for t, (H, X, _) in enumerate(hist):
        for i in range(width):                       # head, MSB on the left
            img[t, width - 1 - i] = (H >> i) & 1
        for j in range(1, depth + 1):                # tail, depths 1..depth
            img[t, width + j - 1] = tail_bit(X, p, j)
    return img, width


def base3_picture(p, d, a, steps=STEPS):
    hist = evolve(p, crystal(p, d, a), steps)
    width = max(len(np.base_repr(H, 3)) if H else 0 for H, _, _ in hist)
    img = np.full((steps, width), 3, dtype=np.uint8)          # 3 = not yet there
    for t, (H, _, _) in enumerate(hist):
        if not H:
            continue
        s = np.base_repr(H, 3)
        for i, ch in enumerate(s):
            img[t, i] = int(ch)
    return img


def damage_front(p, d, depth=240, steps=150):
    """Truncate the tail instead of looping it; where does the damage reach?"""
    Mp = (1 << p) - 1
    X = crystal(p, d)
    N = (X * (1 << depth)) // Mp
    front, wedge = [], np.zeros((steps, depth), dtype=np.uint8)
    for t in range(steps):
        bad = 0
        for j in range(1, depth + 1):
            g = tail_bit(X, p, j)
            f = (N >> (depth - j)) & 1
            if g != f:
                wedge[t, j - 1] = 1
                if not bad:
                    bad = j
        front.append(depth - bad + 1 if bad else 0)
        X = (3 * X) % Mp
        N = 3 * N
    return np.array(front), wedge


def main():
    images = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          os.pardir, "images")
    os.makedirs(images, exist_ok=True)

    specs = [(5, 31, 1), (6, 7, 1), (7, 127, 1), (9, 73, 1), (4, 5, 1),
             (10, 11, 1), (12, 13, 1), (11, 23, 1), (8, 17, 1), (15, 151, 1),
             (5, 31, 3), (6, 7, 2)]

    print("1. the MSB edge: slope and offset for every crystal")
    print("   %-4s %-5s %-3s %-8s %-14s %-16s %s"
          % ("p", "d", "a", "tail T", "fitted slope", "H/3^t", "a/d"))
    for p, d, a in specs:
        Mp = (1 << p) - 1
        X0 = crystal(p, d, a)
        T = tail_period(X0, Mp)
        hist = evolve(p, X0, 400)
        L = np.array([H.bit_length() for H, _, _ in hist], dtype=float)
        k = np.arange(len(L))
        m = k >= 200
        slope = np.polyfit(k[m], L[m], 1)[0]
        H = hist[-1][0]
        print("   %-4d %-5d %-3d %-8d %-14.9f %-16.12f %.12f"
              % (p, d, a, T, slope, H / 3.0 ** (len(hist) - 1), a / float(d)))
    print("   log2(3) = %.9f - every slope, no exceptions. the offset is the" % log2(3))
    print("   tail's own value a/d, exactly.")
    print()

    print("2. the head's base-3 digits are the base-3 expansion of a/d:")
    for p, d, a in ((6, 7, 1), (12, 13, 1), (4, 5, 1), (5, 31, 1)):
        Mp = (1 << p) - 1
        carries = "".join(str(q) for _, _, q in evolve(p, crystal(p, d, a), 30))
        r, ex = a, ""
        for _ in range(30):
            r *= 3
            ex += str(r // d)
            r %= d
        print("   p=%-3d d=%-4d carries    %s" % (p, d, carries))
        print("   %-14s base3(a/d) %s   match %s" % ("", ex, carries == ex))
    print()

    print("3. which edge is lethal - truncate the tail rather than loop it:")
    for p, d in ((6, 7), (5, 31), (9, 73)):
        front, _ = damage_front(p, d)
        k = np.arange(len(front))
        m = (front > 0) & (k > 20)
        slope = np.polyfit(k[m], front[m], 1)[0]
        print("   p=%-3d d=%-4d damage front rises %.4f cells/step" % (p, d, slope))
    print("   the RIGHT edge eats the pattern at log2(3); the LEFT edge cannot")
    print("   touch it at all, because carries only travel towards the MSB.")
    print()

    fig, axs = plt.subplots(2, 3, figsize=(23, 12), dpi=145)
    for ax, (p, d, a), colour in zip(axs.ravel()[:3],
                                     ((6, 7, 1), (5, 31, 1), (9, 73, 1)),
                                     ("#7ee6a0", "#4fd1ff", "#ffb347")):
        img, width = picture(p, d, a)
        ax.imshow(img, cmap=ListedColormap(["#0b0b14", colour]),
                  interpolation="nearest")
        ax.axvline(width - 0.5, color="#ffffff", lw=1.8, alpha=0.9)
        t = np.arange(STEPS)
        ax.plot(width - (t * log2(3) + log2(a / float(d))), t,
                color="#ff5c8a", lw=1.4)
        ax.set_title("tail period %d, denominator %d   edge = t*log2(3) + log2(%d/%d)"
                     % (p, d, a, d), fontsize=11)
        ax.set_xlabel("head (MSB left)  |  looping tail (right)")
        ax.set_ylabel("step")
        ax.set_xticks([])
        ax.set_yticks([])

    ax = axs[1][0]
    for (p, d, a), col in zip(specs[:8], plt.cm.viridis(np.linspace(0, .9, 8))):
        hist = evolve(p, crystal(p, d, a), 140)
        ax.plot([H.bit_length() for H, _, _ in hist], color=col, lw=1.3,
                label="d=%d" % d)
    ax.set_title("every crystal, same slope log2(3), different offset log2(a/d)",
                 fontsize=11)
    ax.set_xlabel("step")
    ax.set_ylabel("MSB position")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=.25)

    ax = axs[1][1]
    b3 = base3_picture(6, 7, 1)
    ax.imshow(b3, cmap=ListedColormap(["#0b0b14", "#ffd166", "#ff5c8a", "#ffffff"]),
              interpolation="nearest")
    ax.set_title("the same head in BASE 3: the periodic expansion of 1/7\n"
                 "(digits 0/1/2 dark/gold/pink) - not chaos, a base-3 crystal",
                 fontsize=11)
    ax.set_xlabel("base-3 digit (most significant left)")
    ax.set_ylabel("step")
    ax.set_xticks([])
    ax.set_yticks([])

    ax = axs[1][2]
    front, wedge = damage_front(6, 7, depth=240, steps=150)
    ax.imshow(wedge, cmap=ListedColormap(["#0b0b14", "#ff5c8a"]),
              interpolation="nearest")
    ax.set_title("if you DON'T loop the right edge: truncation eats upward\n"
                 "at %.3f cells/step (log2 3 = %.3f)"
                 % (np.polyfit(np.arange(len(front))[(front > 0)],
                               front[(front > 0)], 1)[0], log2(3)), fontsize=11)
    ax.set_xlabel("depth below the binary point (cut at the right end)")
    ax.set_ylabel("step")
    ax.set_xticks([])
    ax.set_yticks([])

    fig.suptitle("looping right edge, free MSB edge on the left: the tail is "
                 "untouchable and the edge angle is always log2(3)", fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(images, "collatz-halfopen.png"), facecolor="white")
    plt.close(fig)
    print("wrote images/collatz-halfopen.png")


if __name__ == "__main__":
    main()
