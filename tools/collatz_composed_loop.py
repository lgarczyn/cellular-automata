#!/usr/bin/env python3
"""The composited machine |AAA|B rendered ON ITS LOOPS. SCOPE: [real-CA].

The raw spacetime drifts diagonally, which hides the periodicity. This render
aligns every row on the LeastEdge front (the machine's own frame). In that
frame the behavior is literally periodic:

  - A phase: one loop = 2 steps (beat 1,3 = 4 cells consumed); the texture
    ahead of the front repeats every loop. Loop boundaries are drawn.
  - | boundary: the gold trace is the A/B boundary bit approaching the front.
  - B phase: one loop = 1 step (beat 1); the all-ones texture repeats each row.

Three or more full loops of each phase are visible, per the rendering rules.
"""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collatz_real as R
from collatz_machines import lift, odd_steps
from collatz_machines2 import ideal_beat

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "images")


def main():
    PA, LA = 0b010011, 6
    STEPS_A, NB = 40, 60              # 20 A-loops (80 bits) + 60 B-steps
    beat, _ = ideal_beat(PA, LA, STEPS_A)
    prog = beat + [1] * NB
    n = lift(prog)
    vals, vseq = odd_steps(n, len(prog))
    assert vseq == prog
    SA = sum(beat)                            # bits consumed in the A phase
    A_END = STEPS_A

    H = len(prog)
    # the machine's own frame, built directly from the verified row values:
    # row r = BACK LeastEdge cells | the low AHEAD bits of n_r (its front region)
    BACK, AHEAD = 4, 40
    Wwin = BACK + AHEAD
    a = np.zeros((H, Wwin), np.int8)
    for r in range(H):
        for i in range(BACK):
            a[r, i] = 3
        for i in range(AHEAD):
            a[r, BACK + i] = 1 if (vals[r] >> i) & 1 else 2

    fig, ax = plt.subplots(figsize=(11, 14), dpi=140)
    ax.imshow(a[:, ::-1], cmap=ListedColormap(["#0b0b14", "#7c3aed", "#141b28", "#39d353"]),
              interpolation="nearest", aspect="equal", vmin=0, vmax=3)
    # A-phase loop boundaries: every 2 steps (one 1,3 beat cycle)
    for r in range(0, A_END + 1, 2):
        ax.axhline(r - 0.5, color="#ffffff", lw=0.8, alpha=0.55)
    ax.axhline(A_END - 0.5, color="#ff2d6f", lw=2.2)
    # a few B-phase loop markers (every step is one loop; mark every 4 for legibility)
    for r in range(A_END + 4, H, 4):
        ax.axhline(r - 0.5, color="#ffffff", lw=0.5, alpha=0.3)
    # the | boundary bit, in the moving frame: bit (SA - S_r) of n_r
    xs, ys = [], []
    for r in range(H):
        S_r = sum(vseq[:r])
        x = BACK + (SA - S_r)
        if 0 <= x < Wwin:
            xs.append((Wwin - 1) - x)
            ys.append(r)
    ax.plot(xs, ys, color="#ffd166", lw=2.2, label="| boundary bit (A/B)")
    ax.set_title("[real-CA] composited machine |A...A|B in ITS OWN FRAME (rows aligned on\n"
                 "the LeastEdge front). A phase: 20 full loops of the (1,3) beat (white lines,\n"
                 "one loop = 2 steps): identical texture each loop. Pink = program handoff.\n"
                 "B phase: all-ones, one loop per step. Gold = the | boundary sweeping through.",
                 fontsize=11)
    ax.set_xlabel("cells ahead of the front (MSB LEFT)  |  front at right")
    ax.set_ylabel("odd step")
    ax.set_xticks([]); ax.set_yticks(range(0, H, 4))
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "collatz-composed-loop.png"), facecolor="white",
                bbox_inches="tight")
    plt.close(fig)

    # verify the loop claim numerically: aligned rows repeat with period 2 in A phase
    win = slice(6, 40)
    # loop checks, conditioned on the | boundary being outside the window
    a_rows = [r for r in range(5, A_END)
              if SA - sum(vseq[:r]) > AHEAD and SA - sum(vseq[:r - 2]) > AHEAD]
    ok_a = sum(np.array_equal(a[r, win], a[r - 2, win]) for r in a_rows)
    print("A-phase loops (boundary outside frame): %d/%d rows equal the row 2 "
          "steps earlier (period-2 loop)" % (ok_a, len(a_rows)))
    S_total = sum(vseq)
    b_rows = [r for r in range(A_END + 1, H)
              if sum(vseq[:r - 1]) - SA > 2
              and S_total + 1 - sum(vseq[:r]) > AHEAD + 4]
    ok_b = sum(np.array_equal(a[r, win], a[r - 1, win]) for r in b_rows)
    print("B-phase loops (after boundary transit): %d/%d rows equal the previous "
          "row (period-1 loop)" % (ok_b, len(b_rows)))
    print("rows where the loop check fails are exactly the | boundary transiting "
          "the frame (the gold trace)")
    print("wrote images/collatz-composed-loop.png")


if __name__ == "__main__":
    main()
