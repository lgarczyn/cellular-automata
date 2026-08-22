#!/usr/bin/env python3
"""Hex renders for the left-edge results. SCOPE: [real-CA].
All grids are CA.CollatzStep runs (collatz_real.run) on designed integers.

  collatz-leftedge-crystal.png   an aimed seed: the fresh territory anneals
                                 and crystallizes on schedule
  collatz-leftedge-both.png      both edges programmed at once: d11 rhythm
                                 on the right, scheduled crystallization on
                                 the left
  collatz-leftedge-quantifier.png  the quantifier: z vs aim error for every
                                 odd 18-bit seed + the null families
"""
import os
import math
from math import log2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import collatz_compose as C
import collatz_leftedge as L
from collatz_render_compose import draw_grid, grid_of, panel_fig, sea_front

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")
LOG23 = log2(3)


def fig_crystal():
    k, thick = 18, 56
    g = int(round(thick + k * LOG23))
    n = (2**g // 3**k) | 1
    b0 = n.bit_length()
    T = 30
    rows, vs = C.run_int(n, T)
    zs = L.Baseline(b0, T, N=100).z(L.run_features(n, T))
    g_hex = grid_of(n, T)
    front = sea_front(vs)
    notes = [(k - 8, "annealing: 3^-j words, period 2*3^(j-1)", "#5b3fa8"),
             (k + 1, "step k=%d: crystallized (a power of 2 up here)" % k,
              "#b00040"),
             (min(T - 2, k + 9), "the P-river regrows at 1.585 cells/step",
              "#0a6b28")]
    cap = ("Seed n = 2^%d/3^%d (%d bits). Everything LEFT of the pink line "
           "is territory the seed never occupied. Rows approach step k "
           "through the ternary words 1/3^j (...000111000111..., then "
           "...010101...), crystallize into a pure power of 2 at k=%d, then "
           "the x3 river regrows. Quantifier: z = (%.0f, %.0f, %.0f) vs "
           "noise |z| < 3." % (g, k, b0, k, *zs))
    panel_fig([g_hex], [cap],
              "[real-CA] the left edge is programmable: ternary aiming. "
              "The fresh territory past the start column is the x3 mantissa "
              "flow,\nand n ~ 2^g/3^k schedules a crystallization at step k. "
              "No search can find these seeds (flat landscape); you aim or "
              "you get noise.",
              os.path.join(IMG, "collatz-leftedge-crystal.png"),
              [[b0 - 1]], [notes], [front], scale=0.11)


def fig_both():
    blocks = C.enumerate_blocks(6)
    b = next(x for x in blocks if x.den == 11)
    M = 4 * b.q + len(b.pre)                    # right side: 4 d11 words
    low = C.expansion(b.x, M)
    P, k, thick = 45, 16, 52                    # left side: P=101101 at k=16
    A = (P << thick) // 3**k
    n = (A << M) | low
    b0 = n.bit_length()
    # verify the aim survives the composition
    m = n * 3**k
    top = bin(m)[2 : 2 + 30]
    assert top.startswith(bin(P)[2:] + "0" * 12), top
    T = 32
    rows, vs = C.run_int(n, T)
    lock = C.rhythm_lock(vs, list(b.vs))
    g_hex = grid_of(n, T)
    front = sea_front(vs)
    notes = [(6, "right edge: d11 rhythm 1,1,2 (locked %d steps)" % lock,
              "#0a6b28"),
             (k, "left edge: P=101101 materializes at step k=%d" % k,
              "#b00040")]
    cap = ("One integer, two independent programs. Low digits: four d11 "
           "words (the 2-adic side; rhythm 1,1,2 locked %d steps). High "
           "digits: P*2^%d/3^%d (the archimedean side; P=101101 appears at "
           "step %d in a zero field past the pink start line, then runs its "
           "own river). The two sides never interact: halvings do not touch "
           "the mantissa, the mantissa does not touch the rhythm."
           % (lock, thick, k, k))
    panel_fig([g_hex], [cap],
              "[real-CA] both edges programmed at once: the right edge is "
              "2-adic (blocks, rhythms), the left edge is archimedean "
              "(mantissa aiming).\nTwo number systems, one tape, zero "
              "interference.",
              os.path.join(IMG, "collatz-leftedge-both.png"),
              [[b0 - 1], ], [notes], [front], scale=0.10)
    print("both-edges: d11 lock", lock, "aim top bits", top[:20])


def fig_quantifier():
    T = 22
    base = L.Baseline(18, T, N=150)
    xs, ys = [], []
    for n in range((1 << 17) + 1, 1 << 18, 2):
        zs = base.z(L.run_features(n, T))
        if zs is None:
            continue
        err, k, P = L.aim_err_general(n, T)
        xs.append(max(err, 1e-7))
        ys.append(L.zmax(zs))
    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=140)
    ax.scatter(xs, ys, s=3, alpha=0.18, color="#7c3aed", edgecolors="none",
               label="every odd 18-bit seed (n=%d)" % len(xs))
    ax.axhline(5, color="#b00040", lw=1.2, ls="--")
    ax.text(2e-7, 5.4, "z = 5: structure threshold", color="#b00040",
            fontsize=9)
    # enrichment: P(structured | aim err bin), the honest statistic
    import numpy as np
    xs_a, ys_a = np.array(xs), np.array(ys)
    edges = np.logspace(-7, np.log10(max(xs)), 12)
    bx, by = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (xs_a >= lo) & (xs_a < hi)
        if m.sum() >= 5:
            bx.append(np.sqrt(lo * hi))
            by.append(100.0 * (ys_a[m] > 5).mean())
    ax2 = ax.twinx()
    ax2.plot(bx, by, color="#b00040", lw=2.0, marker="o", ms=4)
    ax2.set_ylabel("%% of seeds structured (z > 5) per aim-error bin",
                   color="#b00040")
    ax2.tick_params(axis="y", colors="#b00040")
    base_rate = 100.0 * (ys_a > 5).mean()
    ax2.axhline(base_rate, color="#b00040", lw=0.8, ls=":")
    ax2.text(edges[0] * 1.3, base_rate + 1.2,
             "base rate %.1f%%" % base_rate, color="#b00040", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("aim error: min over k<=22, odd P<=63 of the log2-distance "
                  "of n*3^k from P*2^g")
    ax.set_ylabel("structure z (max of compression / periodicity / "
                  "constant-run vs 150 random seeds)")
    ax.set_title("[real-CA] the left-edge quantifier over every odd 18-bit "
                 "seed, 22 steps.\nAiming (n ~ P*2^g/3^k) enriches structure "
                 "~25x over the base rate (red curve); structured seeds at "
                 "large raw error are\naims of the affine flow 3^r*n + C_r "
                 "(the +1 carries tip marginal aims). The fuse, every zoo "
                 "block, 3-smooth and sparse\nseeds are all noise; "
                 "hill-climbing on 96-bit seeds plateaus at z~4.6 while "
                 "designed aims reach z~19.", fontsize=10)
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    out = os.path.join(IMG, "collatz-leftedge-quantifier.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


def main():
    fig_crystal()
    fig_both()
    fig_quantifier()


if __name__ == "__main__":
    main()
