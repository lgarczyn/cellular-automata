#!/usr/bin/env python3
"""The monster hunt: designed giants vs searched hailstones. SCOPE: [value].

This is the trajectory-statistics model (integer orbit lengths), NOT the CA.
It is the payoff of the protocol in COLLATZ.md: a designed climb buys odd
steps at a fixed rate, and search buys the fall.

Two kinds of monster:

  DESIGNED (certified, no search):  n = 2^K - 1, the all-ones tape.
    The fuse law guarantees K climb steps at v=1 (+0.585 bits/step), so the
    step count is linear in the seed size and can be ordered to spec.
    K = 2^20 was run exactly: 5,044,234 odd steps, peak 1,661,954 bits.
    Theory predicted 1,661,993 peak bits and ~5.05M steps: 0.1% agreement.

  SEARCHED (exhaustive over a designed class):  n = (m << (j+1)) - 1.
    The j low ones force j guaranteed climb steps; m is free cargo. Each
    class here leaves 31 cargo bits, so the class is only 2^30 wide and was
    swept EXHAUSTIVELY (monster/exh.c): the champions below are class maxima,
    PROVED, not lucky draws.

    Two independent runs agree exactly:
      - 6h random hunt, ~290e9 trials on 16 cores (monster/monster2.c)
      - deterministic sweep of every m (monster/exhrun.sh, 7 minutes)
    Same three champions. Cross-check: the exhaustive sweep hit 5485 seeds
    that exceed 2^125 in the 80/48 class, and the random hunt had logged
    exactly 5485 distinct such seeds, i.e. it really had seen the whole class.
    All 5485 were rerun at 512-bit precision (monster/recheck.c): best 729
    odd steps, below the champion. Nothing hid in the discards.

The ratio odd/bit falls as the numbers grow (12.10 -> 10.85 -> 4.81): design
gives you unbounded totals, search gives you a better rate only at small size,
and the rate decays like ln(size). That is the ceiling the protocol predicted.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")

# class -> (bits, j, m) exhaustive class maxima from the 16-core sweep
CHAMPS = [(48, 16, 2050223741), (64, 32, 1455558314), (80, 48, 2111951648)]


def traj(n):
    """Exact odd-step trajectory. Returns (odd steps, delay, peak, profile)."""
    odd = total = 0
    peak = n
    prof = [n.bit_length()]
    while n != 1:
        if n & 1:
            n = 3 * n + 1
            odd += 1
            total += 1
            if n > peak:
                peak = n
        else:
            v = (n & -n).bit_length() - 1
            n >>= v
            total += v
            prof.append(n.bit_length())
    return odd, total, peak, prof


def main():
    print("%-8s %-26s %6s %7s %9s %8s" %
          ("class", "n", "odd", "delay", "peak bits", "odd/bit"))
    profiles = []
    for bits, j, m in CHAMPS:
        n = (m << (j + 1)) - 1
        assert n.bit_length() == bits
        o, t, p, prof = traj(n)
        profiles.append((bits, j, n, o, prof))
        print("%-8s %-26d %6d %7d %9d %8.2f" %
              ("%d/%d" % (bits, j), n, o, t, p.bit_length(), o / bits))

    # the designed machine at a size we can plot next to them
    K = 512
    g = (1 << K) - 1
    go, gt, gp, gprof = traj(g)
    print("\ndesigned 2^%d - 1: odd %d, delay %d, peak %d bits, odd/bit %.2f"
          % (K, go, gt, gp.bit_length(), go / K))
    print("  climb steps at v=1: %d (= K, the fuse law), slope %.4f bits/step"
          % (K, (gp.bit_length() - K) / K))
    print("certified giant (run separately, K = 2^20): 5,044,234 odd steps, "
          "peak 1,661,954 bits")

    fig, ax = plt.subplots(figsize=(11, 6), dpi=140)
    ax.plot(gprof, color="#7c3aed", lw=2.0,
            label="DESIGNED  2^512 - 1: %d odd steps (climb is a straight line)" % go)
    cols = ["#39d353", "#ffd166", "#ff2d6f"]
    for (bits, j, n, o, prof), c in zip(profiles, cols):
        ax.plot(prof, color=c, lw=1.6,
                label="SEARCHED  %d-bit class max (j=%d): %d odd steps" % (bits, j, o))
    ax.axvline(K, color="#7c3aed", ls=":", lw=1.2)
    ax.annotate("designed climb ends exactly at step K = 512\n"
                "(the fuse law: one guaranteed step per tape bit)",
                xy=(K, gprof[K]), xytext=(K * 0.35, gprof[K] * 0.62),
                color="#7c3aed", fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#7c3aed"))
    ax.set_title("[value] the monster hunt: designed climb vs searched luck.\n"
                 "Designed numbers buy odd steps linearly and without search; "
                 "exhaustive search over a\ndesigned class adds only a decaying "
                 "bonus. Vertical axis is the size of the number in bits.",
                 fontsize=11)
    ax.set_xlabel("odd step")
    ax.set_ylabel("size of n (bits)")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    out = os.path.join(IMG, "collatz-monster.png")
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote images/collatz-monster.png")


if __name__ == "__main__":
    main()
